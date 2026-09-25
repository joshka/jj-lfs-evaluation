#!/usr/bin/env python3
"""Disposable, evidence-producing jj/LFS compatibility evaluation; no product fixes."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import platform
import shutil
import subprocess
import sys
import time
import traceback


PAYLOAD = b"LFS evaluation payload\x00\xff\n" * 100
OTHER = b"second LFS evaluation payload\x00\xfe\n" * 100


def sha(data):
    return hashlib.sha256(data).hexdigest()


def pointer(data):
    return (f"version https://git-lfs.github.com/spec/v1\noid sha256:{sha(data)}\n"
            f"size {len(data)}\n").encode()


class Fixture:
    def __init__(self, suite, name):
        self.suite = suite
        self.root = suite.out / "repos" / name
        self.root.mkdir(parents=True)
        self.env = suite.env.copy()
        self.commands = []
        self.checks = []
        self.observations = {}
        self.g("init", "-b", "main")
        self.g("config", "user.name", "LFS Evaluation")
        self.g("config", "user.email", "eval@example.invalid")
        self.g("config", "commit.gpgsign", "false")
        self.g("config", "core.autocrlf", "false")
        self.g("lfs", "install", "--local")

    def run(self, args, ok=True, env=None, cwd=None, timeout=40):
        start = time.monotonic()
        cp = subprocess.run([str(x) for x in args], cwd=cwd or self.root,
                            env=env or self.env, capture_output=True, timeout=timeout)
        rec = {"argv": [str(x) for x in args], "cwd": str(cwd or self.root),
               "rc": cp.returncode, "seconds": time.monotonic() - start,
               "stdout": cp.stdout.decode("utf-8", "backslashreplace"),
               "stderr": cp.stderr.decode("utf-8", "backslashreplace")}
        self.commands.append(rec)
        if ok and cp.returncode:
            raise RuntimeError(json.dumps(rec))
        return cp

    def g(self, *args, **kw):
        return self.run(["git", *args], **kw)

    def jj(self, *args, **kw):
        return self.run([self.suite.jj, *args], **kw)

    def write(self, name, content):
        path = self.root / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(content.encode() if isinstance(content, str) else content)

    def seed(self, attrs="*.bin filter=lfs diff=lfs merge=lfs -text\n", files=None):
        self.write(".gitattributes", attrs)
        for name, data in (files or {"asset.bin": PAYLOAD, "note.txt": b"ordinary\n"}).items():
            self.write(name, data)
        self.g("add", ".")
        self.g("commit", "-m", "Seed LFS fixture")
        self.seed_sha = self.g("rev-parse", "HEAD").stdout.decode().strip()
        self.jj("git", "init", "--colocate")
        return self

    def stored(self, name):
        return self.jj("file", "show", name, ok=False).stdout

    def files(self):
        return self.jj("file", "list").stdout.decode().splitlines()

    def check(self, label, condition, **evidence):
        self.checks.append({"label": label, "pass": bool(condition), **evidence})

    def bytes_check(self, label, actual, expected):
        self.check(label, actual == expected, actual_sha256=sha(actual),
                   expected_sha256=sha(expected), actual_size=len(actual),
                   expected_size=len(expected))


class Suite:
    def __init__(self, args):
        self.out = Path(args.out).resolve()
        self.out.mkdir(parents=True, exist_ok=True)
        self.jj = str(Path(args.jj).resolve())
        config = self.out / "jj-config.toml"
        config.write_text('[user]\nname="LFS Evaluation"\nemail="eval@example.invalid"\n'
                          '[ui]\npager="cat"\ncolor="never"\n'
                          '[signing]\nbehavior="drop"\n'
                          '[snapshot]\nmax-new-file-size="16MiB"\n')
        self.env = os.environ.copy()
        for key in list(self.env):
            if key.startswith(("JJ_", "GIT_")):
                self.env.pop(key)
        self.env.update(JJ_CONFIG=str(config), JJ_PAGER="cat", GIT_CONFIG_GLOBAL=os.devnull,
                        GIT_CONFIG_NOSYSTEM="1", GIT_ATTR_NOSYSTEM="1", GIT_TERMINAL_PROMPT="0")
        self.results = []
        self.selected = args.only

    def case(self, name, purpose, fn, category="contract"):
        if self.selected and not any(x in name for x in self.selected.split(",")):
            return
        start = time.monotonic()
        f = None
        result = {"id": name, "purpose": purpose, "category": category}
        try:
            f = Fixture(self, name)
            fn(f)
            result["status"] = "PASS" if all(c["pass"] for c in f.checks) else "FAIL"
            if not f.checks:
                result["status"] = "OBSERVED"
        except Exception as ex:
            result.update(status="ERROR", error=str(ex), traceback=traceback.format_exc())
        result["seconds"] = time.monotonic() - start
        if f:
            result.update(checks=f.checks, observations=f.observations)
            evidence = self.out / (name + ".json")
            evidence.write_text(json.dumps({**result, "commands": f.commands}, indent=2))
        self.results.append(result)
        (self.out / "results.json").write_text(json.dumps(self.results, indent=2))
        print(name, result["status"], flush=True)


def basic(f):
    f.seed()
    for _ in range(3):
        f.jj("status")
    f.bytes_check("Hydrated payload remains on disk", (f.root / "asset.bin").read_bytes(), PAYLOAD)
    f.bytes_check("Snapshot preserves pointer", f.stored("asset.bin"), pointer(PAYLOAD))
    f.write("note.txt", "changed\n")
    f.jj("status")
    f.bytes_check("Ordinary edits snapshot", f.stored("note.txt"), b"changed\n")
    f.bytes_check("Unrelated edit preserves pointer", f.stored("asset.bin"), pointer(PAYLOAD))


def ignored_change(f, mode):
    f.seed()
    if mode == "modify":
        f.write("asset.bin", OTHER)
    elif mode == "delete":
        (f.root / "asset.bin").unlink()
    elif mode == "rename":
        (f.root / "asset.bin").rename(f.root / "renamed.bin")
    elif mode == "new":
        f.write("new.bin", OTHER)
    st = f.jj("status")
    f.bytes_check("Stored pointer unchanged by excluded mutation", f.stored("asset.bin"), pointer(PAYLOAD))
    f.observations["status"] = st.stdout.decode()
    f.observations["mutation"] = mode
    f.observations["disk_files"] = [p.name for p in f.root.iterdir() if p.is_file()]
    f.check("No new excluded path snapshots", "new.bin" not in f.files() and "renamed.bin" not in f.files())


def attr_case(f, root_attrs, path, extra_attrs=None, excluded=True, info=False, global_attr=False):
    f.seed(attrs=root_attrs, files={"note.txt": b"seed\n"})
    for name, content in (extra_attrs or {}).items():
        f.write(name, content)
    if info:
        f.write(".git/info/attributes", f"{path} filter=lfs\n")
    if global_attr:
        global_file = f.root.parent / (f.root.name + "-global-attributes")
        global_file.write_text(f"{path} filter=lfs\n")
        f.g("config", "core.attributesFile", str(global_file))
    f.write(path, PAYLOAD)
    oracle = f.g("check-attr", "filter", "--", path)
    st = f.jj("status")
    included = path in f.files()
    f.check("Expected exclusion matches Git attribute decision", included != excluded,
            expected_excluded=excluded, actual_included=included,
            git_check_attr=oracle.stdout.decode(), jj_status=st.stdout.decode())
    if included:
        f.observations["stored_payload_sha256"] = sha(f.stored(path))


def disable(f):
    f.seed()
    f.jj("--config=git.ignore-filters=[]", "status")
    f.bytes_check("Opt-out snapshots raw payload", f.stored("asset.bin"), PAYLOAD)


def force_track(f):
    f.seed(files={"note.txt": b"seed\n"})
    f.write("new.bin", PAYLOAD)
    cp = f.jj("file", "track", "new.bin", ok=False)
    f.observations["track"] = {"rc": cp.returncode, "stderr": cp.stderr.decode()}
    f.check("Explicit tracking either tracks or explains exclusion", "new.bin" in f.files()
            or cp.returncode != 0 or "filter" in cp.stderr.decode().lower())


def attrs_remove(f):
    f.seed()
    (f.root / ".gitattributes").unlink()
    for n in (1, 2, 3):
        st = f.jj("status")
        stored = f.jj("--ignore-working-copy", "file", "show", "asset.bin").stdout
        f.observations[str(n)] = {"status": st.stdout.decode(), "stored_hash": sha(stored),
                                  "is_pointer": stored == pointer(PAYLOAD)}
    f.check("Repeated status without disk changes is stable",
            f.observations["1"]["stored_hash"] == f.observations["2"]["stored_hash"])


def attrs_change(f, value):
    f.seed()
    f.write(".gitattributes", f"*.bin {value}\n")
    f.jj("status")
    f.bytes_check("Removing filter permits raw snapshot", f.stored("asset.bin"), PAYLOAD)


def add_attrs_existing(f):
    f.seed(attrs="", files={"asset.bin": PAYLOAD})
    f.write(".gitattributes", "*.bin filter=lfs\n")
    f.write("asset.bin", OTHER)
    f.jj("status")
    f.bytes_check("Adding filter retains old stored content", f.stored("asset.bin"), PAYLOAD)
    f.bytes_check("Edited disk content survives snapshot", (f.root / "asset.bin").read_bytes(), OTHER)


def symlink_attrs(f):
    if os.name == "nt":
        f.observations["skip"] = "Symlink privilege varies on Windows; tested on Unix."
        return
    f.seed(attrs="", files={"note.txt": b"seed"})
    (f.root / ".gitattributes").unlink()
    f.write("rules", "*.bin filter=lfs\n")
    (f.root / ".gitattributes").symlink_to("rules")
    f.write("new.bin", PAYLOAD)
    f.jj("status")
    f.check("Symlinked attributes not followed", "new.bin" in f.files())


def symlink_asset(f):
    if os.name == "nt":
        f.observations["skip"] = "Symlink privilege varies on Windows; tested on Unix."
        return
    f.seed(files={"note.txt": b"seed"})
    (f.root / "link.bin").symlink_to("note.txt")
    f.g("add", "link.bin")
    git_entry = f.g("ls-files", "--stage", "link.bin").stdout.decode()
    f.jj("status")
    f.check("LFS pattern does not hide a Git symlink", "link.bin" in f.files(), git_entry=git_entry)


def ignored_dir(f):
    f.seed(files={"ignored/asset.bin": PAYLOAD, "ignored/note.txt": b"old"})
    f.write(".gitignore", "ignored/\n")
    f.write("ignored/asset.bin", OTHER)
    f.write("ignored/note.txt", "new")
    f.jj("status")
    f.bytes_check("Ignored-dir fast path preserves LFS pointer", f.stored("ignored/asset.bin"), pointer(PAYLOAD))
    f.bytes_check("Ignored-dir tracked ordinary edit snapshots", f.stored("ignored/note.txt"), b"new")


def file_dir(f):
    f.seed()
    (f.root / "asset.bin").unlink()
    f.write("asset.bin/child.txt", "directory replacement")
    cp = f.jj("status", ok=False)
    f.observations["status"] = {"rc": cp.returncode, "stderr": cp.stderr.decode()}
    f.check("File-to-directory transition completes without panic", cp.returncode == 0)
    if cp.returncode == 0:
        f.observations["files"] = f.files()


def literal_pointer(f, payload):
    f.seed()
    f.write("asset.bin", payload)
    f.jj("status")
    f.bytes_check("Filtered arbitrary disk bytes do not alter stored pointer", f.stored("asset.bin"), pointer(PAYLOAD))
    f.bytes_check("Snapshot preserves disk bytes", (f.root / "asset.bin").read_bytes(), payload)


def empty_file(f):
    f.seed(files={"empty.bin": b"", "note.txt": b"seed"})
    f.bytes_check("Empty LFS file passthrough stays empty", f.stored("empty.bin"), b"")


def missing_object(f):
    f.seed()
    obj = f.root / ".git/lfs/objects" / sha(PAYLOAD)[:2] / sha(PAYLOAD)[2:4] / sha(PAYLOAD)
    obj.unlink()
    f.write("asset.bin", pointer(PAYLOAD))
    cp = f.g("lfs", "checkout", ok=False)
    f.observations["checkout"] = {"rc": cp.returncode, "stderr": cp.stderr.decode()}
    f.jj("status")
    f.bytes_check("Missing object leaves pointer intact", f.stored("asset.bin"), pointer(PAYLOAD))
    f.bytes_check("Missing object does not fabricate disk data", (f.root / "asset.bin").read_bytes(), pointer(PAYLOAD))
    obj.parent.mkdir(parents=True, exist_ok=True)
    obj.write_bytes(PAYLOAD)
    f.g("lfs", "checkout")
    f.jj("status")
    f.bytes_check("Restored object hydrates correctly", (f.root / "asset.bin").read_bytes(), PAYLOAD)


def sparse(f, dirty=False):
    f.seed(files={"assets/asset.bin": PAYLOAD, "note.txt": b"ordinary"})
    if dirty:
        f.write("assets/asset.bin", OTHER)
    cp = f.jj("sparse", "set", "--clear", "--add", "note.txt", ok=False)
    exists = (f.root / "assets/asset.bin").exists()
    f.observations["sparse"] = {"rc": cp.returncode, "stderr": cp.stderr.decode(), "asset_exists": exists}
    if dirty:
        saved = f.jj("--ignore-working-copy", "file", "show", "assets/asset.bin", ok=False).stdout
        f.check("Sparse exclusion preserves, snapshots, or rejects local edits", cp.returncode != 0 or exists or saved == OTHER,
                stored_sha256=sha(saved), edited_sha256=sha(OTHER))
    else:
        f.jj("sparse", "reset")
        f.g("lfs", "checkout")
        f.bytes_check("Sparse reset and hydration restore content", (f.root / "assets/asset.bin").read_bytes(), PAYLOAD)


def workspace(f):
    f.seed()
    other = f.root.parent / (f.root.name + "-workspace")
    f.jj("workspace", "add", str(other))
    f.bytes_check("Additional workspace initially contains pointer", (other / "asset.bin").read_bytes(), pointer(PAYLOAD))
    cp = f.run(["git", "lfs", "checkout"], cwd=other, ok=False)
    f.observations["plain_git_lfs"] = {"rc": cp.returncode, "stderr": cp.stderr.decode()}
    st = f.run([f.suite.jj, "status"], cwd=other)
    f.observations["git_context"] = (other / ".git").read_text() if (other / ".git").is_file() else "absent"
    f.check("Colocated additional workspace supports external hydration", cp.returncode == 0 and (other / "asset.bin").read_bytes() == PAYLOAD, status=st.stdout.decode())
    stored = f.run([f.suite.jj, "file", "show", "asset.bin"], cwd=other).stdout
    f.bytes_check("Hydrated additional workspace retains stored pointer", stored, pointer(PAYLOAD))


def attrs_permission(f):
    if os.name == "nt" or (hasattr(os, "geteuid") and os.geteuid() == 0):
        f.observations["skip"] = "Requires non-root Unix permission enforcement."
        return
    f.seed()
    path = f.root / ".gitattributes"
    path.chmod(0)
    try:
        cp = f.jj("status", ok=False)
        f.check("Unreadable attributes fail with path context", cp.returncode != 0 and ".gitattributes" in cp.stderr.decode(), stderr=cp.stderr.decode())
    finally:
        path.chmod(0o644)


def invalid_config(f):
    f.seed()
    cp = f.jj('--config=git.ignore-filters="lfs"', "status", ok=False)
    f.check("Invalid config reports key and fails", cp.returncode != 0 and "ignore-filters" in cp.stderr.decode(), stderr=cp.stderr.decode())


def run_temp(f):
    f.seed()
    script = f.root.parent / "write-run.py"
    script.write_text("from pathlib import Path\nPath('asset.bin').write_bytes(b'run mutation')\nPath('note.txt').write_text('run ordinary')\n")
    f.jj("run", "-r", "@", "--", sys.executable, str(script))
    f.bytes_check("Run temp snapshot preserves pointer", f.stored("asset.bin"), pointer(PAYLOAD))
    f.bytes_check("Run captures ordinary edits", f.stored("note.txt"), b"run ordinary")


def executable(f):
    if os.name == "nt":
        f.observations["skip"] = "Executable bit is not supported by Windows filesystem semantics."
        return
    f.seed()
    (f.root / "asset.bin").chmod(0o755)
    st = f.jj("status")
    f.observations["status"] = st.stdout.decode()
    f.observations["git_diff"] = f.g("diff", "--summary").stdout.decode()
    f.check("Pointer survives executable-bit-only edit", f.stored("asset.bin") == pointer(PAYLOAD))


def performance(f):
    f.seed(attrs="*.bin filter=lfs\n", files={"note.txt": b"seed"})
    for i in range(120):
        f.write(f"tree/d{i}/.gitattributes", "*.dat -filter\n")
        for j in range(25):
            f.write(f"tree/d{i}/f{j}.dat", b"ordinary\n")
    f.jj("status", timeout=90)
    times = {"enabled": [], "disabled": []}
    for _ in range(5):
        for name, conf in (("enabled", 'git.ignore-filters=["lfs"]'), ("disabled", "git.ignore-filters=[]")):
            start = time.monotonic()
            f.jj("--config=" + conf, "status", timeout=90)
            times[name].append(time.monotonic() - start)
    f.observations["timings_seconds"] = times
    f.observations["fixture"] = "3000 ordinary files, 120 nested attribute files, same binary, warm runs"
    f.check("All ordinary files remain tracked", len(f.files()) == 3122)


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--jj", required=True)
    p.add_argument("--out", required=True)
    p.add_argument("--only", default="")
    args = p.parse_args()
    s = Suite(args)
    meta = {"platform": platform.platform(), "python": sys.version, "jj": s.jj,
            "binary_sha256": sha(Path(s.jj).read_bytes()), "time_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())}
    for name, cmd in (("jj_version", [s.jj, "--version"]), ("git_version", ["git", "--version"]), ("lfs_version", ["git", "lfs", "version"])):
        meta[name] = subprocess.check_output(cmd, env=s.env).decode().strip()
    (s.out / "environment.json").write_text(json.dumps(meta, indent=2))
    s.case("S01-hydrated", "Ordinary edits and repeated snapshots preserve LFS pointers", basic)
    for mode in ("modify", "delete", "rename", "new"):
        s.case("S02-" + mode, "Characterize silent snapshot exclusion: " + mode,
               lambda f, m=mode: ignored_change(f, m))
    attrs = [
        ("nested-unset", "*.bin filter=lfs\n", "sub/a.bin", {"sub/.gitattributes": "*.bin -filter\n"}, False),
        ("nested-set", "*.bin -filter\n", "sub/a.bin", {"sub/.gitattributes": "*.bin filter=lfs\n"}, True),
        ("macro", "[attr]large filter=lfs -text\n*.bin large\n", "a.bin", {}, True),
        ("unspecified", "*.bin filter=lfs\na.bin !filter\n", "a.bin", {}, False),
        ("last-wins", "*.bin filter=lfs\n*.bin filter=other\n", "a.bin", {}, False),
        ("quoted-space", '"space name.bin" filter=lfs\n', "space name.bin", {}, True),
        ("unicode", "*.bin filter=lfs\n", "café.bin", {}, True),
        ("directory-only", "assets/ filter=lfs\n", "assets/a.bin", {}, False),
        ("recursive", "assets/** filter=lfs\n", "assets/sub/a.bin", {}, True),
        ("case-sensitive", "*.BIN filter=lfs\n", "a.bin", {}, False),
        ("filter-set", "*.bin filter\n", "a.bin", {}, False),
        ("subdir-relative", "", "sub/a.bin", {"sub/.gitattributes": "a.bin filter=lfs\n"}, True),
    ]
    for name, root, path, extra, excluded in attrs:
        s.case("A01-" + name, "Attribute matching agrees with Git", lambda f, r=root, p=path, e=extra, x=excluded: attr_case(f, r, p, e, x))
    s.case("A02-info-attributes", "Local info attributes protect LFS payload", lambda f: attr_case(f, "", "a.bin", info=True), "compatibility")
    s.case("A03-global-attributes", "Configured global attributes protect LFS payload", lambda f: attr_case(f, "", "a.bin", global_attr=True), "compatibility")
    s.case("A04-removed", "Attribute removal reaches stable snapshot in one command", attrs_remove, "compatibility")
    s.case("A05-unset", "LFS-to-ordinary transition", lambda f: attrs_change(f, "-filter"))
    s.case("A06-existing-file", "Ordinary-to-LFS transition", add_attrs_existing)
    s.case("A07-symlink-attrs", "Do not follow symlinked attribute files", symlink_attrs)
    s.case("A08-symlink-asset", "LFS patterns do not suppress symlink versioning", symlink_asset, "compatibility")
    s.case("A09-ignored-directory", "Ignored directory shortcut respects LFS exclusion", ignored_dir)
    s.case("A10-file-directory", "File-to-directory replacement is handled", file_dir)
    s.case("C01-disable", "Explicit filter opt-out", disable)
    s.case("C02-force-track", "Explicit tracking has actionable result", force_track, "diagnostics")
    s.case("C03-invalid-config", "Invalid config has useful error", invalid_config)
    s.case("P01-pointer", "Literal pointer snapshots unchanged", lambda f: literal_pointer(f, pointer(PAYLOAD)))
    s.case("P02-malformed", "Malformed pointer-like content remains external", lambda f: literal_pointer(f, b"version https://git-lfs.github.com/spec/v1\noid sha256:bad\n"))
    s.case("P03-empty", "Empty LFS file passthrough", empty_file)
    s.case("P04-missing-object", "Missing local object and recovery", missing_object)
    s.case("W01-sparse", "Sparse reset then external hydration", sparse)
    s.case("W02-sparse-dirty", "Sparse removal must not silently lose local edits", lambda f: sparse(f, True), "data-integrity")
    s.case("W03-workspace", "Additional workspace and missing Git context", workspace)
    s.case("W04-run", "Temporary run snapshot preserves filtered paths", run_temp)
    s.case("D01-permission", "Unreadable attributes have useful error", attrs_permission)
    s.case("D02-executable", "Executable bit-only edits characterized", executable)
    s.case("N01-performance", "Measure per-snapshot attribute overhead", performance, "performance")
    counts = {status: sum(r["status"] == status for r in s.results) for status in ("PASS", "FAIL", "ERROR", "OBSERVED")}
    print(json.dumps(counts), flush=True)
    # Findings are the output of an evaluation, not a reason to lose CI artifacts.
    return 2 if counts["ERROR"] else 0


if __name__ == "__main__":
    sys.exit(main())
