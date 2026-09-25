# Findings

**Do not merge the pinned head unchanged.** Edited hydrated assets can be lost during checkout, and
the documented untrack recipe removes committed pointers. These are the two highest-priority issues.
The PR does preserve pointers during ordinary snapshots; that narrower behavior works.

Target: [PR 9635](https://github.com/jj-vcs/jj/pull/9635), `d8a56d1a38ca`. Exact-parent comparisons
use `e9f48b3e4c1c`. No implementation fixes were made. Case links below provide setup, rationale,
acceptance criteria, full commands, and raw evidence. [Methodology](METHODOLOGY.md) records provenance.

The commands below create disposable repositories and were rechecked against the pinned debug
binary on macOS. Run the shared setup once, then any finding's block. Each creates its own fixture.
The fixture bytes are smaller than the original evaluation; the same failure conditions are checked.
Suggested fixes are proposals, not implemented or validated changes.

## Reproduction setup

Prerequisites: Bash, Python 3, Git, Git LFS, and a debug `jj` binary built from
`d8a56d1a38cae110529ef8e67e72e3e2057ed3ca`. Use debug to reproduce F03; its release command succeeds.
These Bash reproductions were verified on macOS. Windows findings are supported by the earlier
native CI evidence; these new shell blocks were not rerun there. F05 requires symlink support.

If needed, build the pinned binary from its source archive in a separate temporary directory:

```sh
BUILD_DIR="$(mktemp -d "${TMPDIR:-/tmp}/jj-lfs-build.XXXXXX")"
curl -fL https://github.com/jj-vcs/jj/archive/d8a56d1a38cae110529ef8e67e72e3e2057ed3ca.tar.gz \
  -o "$BUILD_DIR/source.tar.gz"
tar -xzf "$BUILD_DIR/source.tar.gz" -C "$BUILD_DIR" --strip-components=1
(cd "$BUILD_DIR" && cargo build --locked -p jj-cli --bin jj)
# Use "$BUILD_DIR/target/debug/jj" as JJ_BIN below.
```

Shared fixture setup (set `JJ_BIN` to the absolute path before running):

```sh
# Use a fresh Bash session. JJ_BIN must be an absolute path to the pinned debug binary.
export JJ_BIN=/absolute/path/to/pinned/jj
export LAB="$(mktemp -d "${TMPDIR:-/tmp}/jj-lfs-report.XXXXXX")"
export GIT_CONFIG_GLOBAL=/dev/null GIT_CONFIG_NOSYSTEM=1 GIT_ATTR_NOSYSTEM=1
export GIT_TERMINAL_PROMPT=0 JJ_PAGER=cat
export JJ_CONFIG="$LAB/jj.toml"
cat > "$JJ_CONFIG" <<'CONFIG'
[user]
name = "LFS Evaluation"
email = "eval@example.invalid"
[signing]
behavior = "drop"
[ui]
color = "never"
CONFIG
jj() { "$JJ_BIN" "$@"; }
new_case() {
  # Arguments: unique case name, optional asset path, optional "plain" rule mode.
  mkdir "$LAB/$1" && cd "$LAB/$1" || return 1
  git init -q -b main || return 1
  git config user.name 'LFS Evaluation'
  git config user.email eval@example.invalid
  git config commit.gpgsign false
  git config core.autocrlf false
  git lfs install --local || return 1
  python3 - "${2:-asset.bin}" "${3:-lfs}" <<'SEED'
from pathlib import Path
import sys
asset = Path(sys.argv[1])
asset.parent.mkdir(parents=True, exist_ok=True)
asset.write_bytes(b"seed asset\n" * 100)
Path("note.txt").write_bytes(b"ordinary\n")
rule = "*.bin filter=lfs diff=lfs merge=lfs -text\n" if sys.argv[2] == "lfs" else ""
Path(".gitattributes").write_text(rule)
SEED
  git add . && git commit -qm 'Seed fixture' || return 1
  jj git init --colocate || return 1
}
```

Do not enable shell `errexit`: several commands intentionally fail, and the next line prints their
exit code. Fixture setup failures explicitly stop the block. Use unique case names if repeating a
block in the same session. No command contacts a remote after setup.

## Failures and compatibility gaps

| Finding | Consequence | Disposition |
| --- | --- | --- |
| [F01](#f01) | Edited payload lost during checkout/rebase/sparse removal | Block merge |
| [F02](#f02) | Documented untrack recipe removes the pointer | Correct before merge |
| [F03](#f03) | File-to-directory transition panics in debug builds | Fix before merge |
| [F04](#f04) | Second status stores raw bytes after attribute deletion | Settle semantics |
| [F05](#f05) | Matching symlink omitted from the tree | Fix or narrow scope |
| [F06](#f06) | Explicit track succeeds silently without tracking | Explain exclusion |
| [F07](#f07) | Info/global attribute rules do not prevent raw snapshots | Document scope |
| [F08](#f08) | Workspace/attribute descriptions are stale | Correct documentation |

### F01

**P1 — Edited asset bytes are lost.**

**Setup:** A committed LFS pointer at `assets/asset.bin`; its hydrated disk content has a new,
unrecorded edit.

**Reproduce:**

```sh
new_case F01 assets/asset.bin || exit 1
printf 'unrecorded edit\n' > assets/asset.bin
jj sparse set --clear --add note.txt
printf 'sparse exit=%s\n' "$?"
if test -e assets/asset.bin; then echo 'disk=present'; else echo 'disk=missing'; fi
jj --ignore-working-copy file show assets/asset.bin
```

**Expected:** Refuse to remove the edited file, keep it on disk, or save its edited bytes before
removal.

**Actual:** Sparse-set exits 0 and deletes the disk file. File-show returns the old pointer, not the
edited bytes.

**Relevant output** (nonconsecutive lines; see the linked transcript):

```text
sparse exit=0
disk=missing
version https://git-lfs.github.com/spec/v1
```

**Difference:** The edited bytes are missing from both disk and the inspected tree. The exact parent
saves the raw edit. Revision switching and rebasing also lose edits in separate fixtures.

**Suggested fix:** Before checkout overwrites or removes an excluded file, detect unrecorded content
and preserve it or refuse with an actionable error. Cover switch, rebase, and sparse removal. Do not
silently resume storing raw payloads as the LFS solution.

**Scope:** PR regression. Sparse loss reproduces in release and all tested debug configurations.

**Cases:** [W02-sparse-dirty](TEST-CASES.md#w02-sparse-dirty) ·
[X01-checkout-rebase](TEST-CASES.md#x01-checkout-rebase).

**Reproduction transcript:** [F01.txt](evidence/manual-reproductions/F01.txt).

### F02

**P1 — The documented untrack step deletes the pointer.**

**Setup:** An existing committed LFS pointer and hydrated `asset.bin`; follow the proposed untrack
guidance.

**Reproduce:**

```sh
new_case F02 || exit 1
jj file untrack asset.bin
printf 'untrack exit=%s\n' "$?"
jj status
jj file list
jj file show asset.bin
printf 'show exit=%s\n' "$?"
```

**Expected:** Following the LFS setup instructions keeps the asset in the revision.

**Actual:** Untrack exits 0. Status reports `D asset.bin`; file-list omits it; file-show exits 1.
The disk payload remains.

**Relevant output** (nonconsecutive lines; see the linked transcript):

```text
untrack exit=0
D asset.bin
show exit=1
Error: No such path: asset.bin
```

**Difference:** The working revision records a deletion. Publishing that revision removes the asset,
although its bytes still exist locally.

**Suggested fix:** Remove the untrack instruction. Explain that tracked LFS paths are already
excluded from snapshots, and provide a tested procedure for updating pointers through external Git
LFS.

**Scope:** Documentation defect. The untrack command is behaving as requested; the parent refuses
this operation because the path is not ignored.

**Cases:** [X02-untrack-recipe](TEST-CASES.md#x02-untrack-recipe).

**Reproduction transcript:** [F02.txt](evidence/manual-reproductions/F02.txt).

### F03

**P2 — Replacing an asset file with a directory crashes debug builds.**

**Setup:** With `*.bin filter=lfs`, replace disk file `asset.bin` with directory
`asset.bin/child.txt`.

**Reproduce:**

```sh
new_case F03 || exit 1
rm asset.bin
mkdir asset.bin
printf 'child\n' > asset.bin/child.txt
jj status
printf 'status exit=%s\n' "$?"
```

**Expected:** Exit 0 and represent the file-to-directory change consistently.

**Actual:** Debug builds exit 101 at `local_working_copy.rs:1464`. Cached file states contain both
`asset.bin` and its child; the tree contains only the child.

**Relevant output** (nonconsecutive lines; see the linked transcript):

```text
status exit=101
assertion `left == right` failed
```

**Difference:** The path-state cache disagrees with the tree. The exact parent handles the
transition.

**Suggested fix:** Update or remove stale file-state entries during excluded file-to-directory
transitions. Add repeated-snapshot and subsequent-checkout regression coverage.

**Scope:** PR regression reproduced on macOS, Linux, and Windows debug builds. macOS release exits
0; no release crash was demonstrated.

**Cases:** [A10-file-directory](TEST-CASES.md#a10-file-directory) · [X01 path-kind
probes](TEST-CASES.md#x01-checkout-rebase).

**Reproduction transcript:** [F03.txt](evidence/manual-reproductions/F03.txt).

### F04

**P2 — A second status changes stored asset content without another edit.**

**Setup:** Delete `.gitattributes` while `asset.bin` is hydrated. Make no further disk changes.

**Reproduce:**

```sh
new_case F04 || exit 1
rm .gitattributes
jj status
jj --ignore-working-copy file show asset.bin > "$LAB/F04-first"
jj status
jj --ignore-working-copy file show asset.bin > "$LAB/F04-second"
python3 - "$LAB" <<'CHECK'
from pathlib import Path
import sys
root = Path(sys.argv[1])
a, b = [(root / name).read_bytes() for name in ("F04-first", "F04-second")]
print("first_is_pointer=", a.startswith(b"version https://git-lfs.github.com/spec/v1\n"))
print("second_is_raw=", b == b"seed asset\n" * 100)
print("same_bytes=", a == b)
CHECK
```

**Expected:** Both inspections return the same stored bytes once the first snapshot has processed
the deletion.

**Actual:** The first returns the LFS pointer. The second returns the raw payload. A third snapshot
is stable.

**Relevant output** (nonconsecutive lines; see the linked transcript):

```text
first_is_pointer= True
second_is_raw= True
same_bytes= False
```

**Difference:** The number of status calls changes what is stored. The parent does not show this
two-step transition.

**Suggested fix:** Define when deleted attribute rules stop applying, and use that policy
consistently within the first snapshot. Test successive snapshots with non-snapshotting inspections.

**Scope:** Reproduces in every tested configuration. The intended policy needs a decision; these
results do not prescribe whether the first snapshot should retain a pointer or store raw bytes.

**Cases:** [A04-removed](TEST-CASES.md#a04-removed) · [Parent
comparison](evidence/base-comparison/A04-removed.json).

**Reproduction transcript:** [F04.txt](evidence/manual-reproductions/F04.txt).

### F05

**P2 — A matching symlink disappears from the jj tree.**

**Setup:** Under `*.bin filter=lfs`, create `link.bin` as a symlink to ordinary `note.txt`.

**Reproduce:**

```sh
new_case F05 || exit 1
python3 -c 'from pathlib import Path; Path("link.bin").symlink_to("note.txt")'
git add link.bin
git ls-files --stage link.bin
jj status
jj file list
```

**Expected:** Keep `link.bin` as a symlink entry, as Git does.

**Actual:** Git records mode `120000`. jj file-list omits `link.bin`.

**Relevant output** (nonconsecutive lines; see the linked transcript):

```text
120000 97922aee98474ad751b77adb4aa5e4f3dce681fe 0 link.bin
The working copy has no changes.
.gitattributes
asset.bin
note.txt
```

**Difference:** The filter pattern suppresses a normal symlink tree entry. The parent tracks it.

**Suggested fix:** Apply LFS snapshot exclusion to appropriate regular-file content, not symlink
entries solely because their names match. Test new symlinks and file-to-symlink transitions.

**Scope:** Reproduced on macOS and Linux. Windows symlink probes were skipped. Symlinked
`.gitattributes` is a separate case and is correctly not followed.

**Cases:** [A08-symlink-asset](TEST-CASES.md#a08-symlink-asset) · [X01 path-kind
probes](TEST-CASES.md#x01-checkout-rebase).

**Reproduction transcript:** [F05.txt](evidence/manual-reproductions/F05.txt).

### F06

**P2 — Track says success but does not track the file.**

**Setup:** Create a new `new.bin` that matches `filter=lfs`.

**Reproduce:**

```sh
new_case F06 || exit 1
printf 'new payload\n' > new.bin
jj file track new.bin > "$LAB/F06-out" 2> "$LAB/F06-err"
printf 'track exit=%s\n' "$?"
printf 'stderr bytes='; wc -c < "$LAB/F06-err"
jj file list
```

**Expected:** Track the path, return a failure, or explain why it remains excluded.

**Actual:** Track exits 0 with empty stderr. File-list does not contain `new.bin`.

**Relevant output** (nonconsecutive lines; see the linked transcript):

```text
track exit=0
stderr bytes=       0
.gitattributes
asset.bin
note.txt
```

**Difference:** The explicit request silently does nothing. A separate `jj --debug status` probe
also does not name the excluded path or filter.

**Suggested fix:** Return an actionable diagnostic for explicit tracking of an excluded path,
including the filter and supported next step. Add optional debug tracing for exclusion decisions.

**Scope:** Usability gap in every tested configuration. This does not require noisy warnings on
every ordinary status.

**Cases:** [C02-force-track](TEST-CASES.md#c02-force-track) · [X06 diagnostic
probe](TEST-CASES.md#x06-performance-config).

**Reproduction transcript:** [F06.txt](evidence/manual-reproductions/F06.txt).

### F07

**Compatibility gap — Git identifies LFS content that jj stores raw.**

**Setup:** Put `a.bin filter=lfs` only in `.git/info/attributes`; repeat separately with
`core.attributesFile`. No repository rule matches.

**Reproduce:**

```sh
new_case F07-info asset.bin plain || exit 1
printf 'a.bin filter=lfs\n' > .git/info/attributes
printf 'new payload\n' > a.bin
git check-attr filter -- a.bin
jj status
jj file list
jj file show a.bin

new_case F07-global asset.bin plain || exit 1
printf 'a.bin filter=lfs\n' > "$LAB/global-attributes"
git config core.attributesFile "$LAB/global-attributes"
printf 'new payload\n' > a.bin
git check-attr filter -- a.bin
jj status
jj file list
jj file show a.bin
```

**Expected:** For full Git-attribute compatibility, exclude the file that Git identifies as
LFS-managed.

**Actual:** Git reports `a.bin: filter: lfs`. jj adds `a.bin` and stores its raw payload.

**Relevant output** (nonconsecutive lines; see the linked transcript):

```text
a.bin: filter: lfs
A a.bin
new payload
```

**Difference:** Only repository `.gitattributes` rules provide exclusion; local/global rule sources
do not.

**Suggested fix:** Document the supported sources explicitly and keep regression tests for that
boundary. If full parity is intended, implement the missing sources with Git precedence semantics.

**Scope:** Not an established regression. This compatibility expectation exceeds the current
implementation; deferral is reasonable with clear scope.

**Cases:** [A02-info-attributes](TEST-CASES.md#a02-info-attributes) ·
[A03-global-attributes](TEST-CASES.md#a03-global-attributes).

**Reproduction transcript:** [F07.txt](evidence/manual-reproductions/F07.txt).

### F08

**Documentation — The workspace limitation is too broad.**

**Setup:** Create an additional colocated workspace from the LFS fixture. The first command runs in
the original workspace; the others run in the new workspace.

**Reproduce:**

```sh
new_case F08 || exit 1
jj workspace add "$LAB/F08-extra"
cd "$LAB/F08-extra" || exit 1
if test -f .git; then echo 'git context=present'; else echo 'git context=missing'; fi
git lfs checkout
printf 'checkout exit=%s\n' "$?"
python3 - <<'CHECK'
from pathlib import Path
print("hydrated=", Path("asset.bin").read_bytes() == b"seed asset\n" * 100)
CHECK
jj status
jj file show asset.bin
```

**Expected:** Documentation describes the Git context and external hydration supported by the tested
layout.

**Actual:** The workspace has a `.git` file. External checkout hydrates the asset, and jj retains
its stored pointer. The docs broadly say jj workspaces lack Git context.

**Relevant output** (nonconsecutive lines; see the linked transcript):

```text
git context=present
checkout exit=0
hydrated= True
version https://git-lfs.github.com/spec/v1
```

**Difference:** The documented restriction excludes a workflow that works on all tested
configurations. Separately, source review found stale PR-description claims about following
symlinked attributes and eagerly parsing all rules.

**Suggested fix:** Qualify workspace guidance by repository layout. Describe the current symlink
handling and lazy rule loading rather than older behavior.

**Scope:** Documentation correction. Non-colocated workspace support was not established; lazy
loading is a source-review observation, not a conclusion from these commands.

**Cases:** [W03-workspace](TEST-CASES.md#w03-workspace) ·
[A07-symlink-attrs](TEST-CASES.md#a07-symlink-attrs).

## What worked

**Reproduction transcript:** [F08.txt](evidence/manual-reproductions/F08.txt).

### Ordinary snapshots and supported attributes

Repeated `jj status`, an ordinary file edit, and `jj file show` confirmed that hydrated bytes stay
on disk while the original LFS pointer stays stored. An ignored-directory traversal also captures
ordinary edits while preserving the asset pointer. Asset modification/deletion/rename cases pass
because they remain **unrecorded**, not because those operations are supported safely.
[Snapshot case](TEST-CASES.md#s01-hydrated) · [Excluded edits](TEST-CASES.md#s02-modify) ·
[Ignored directory](TEST-CASES.md#a09-ignored-directory).

`git check-attr`, status, and file-list agreed for the tested repository-rule overrides, macros,
precedence, unspecified/boolean states, quoted spaces, Unicode, and recursive patterns. Explicit
opt-out stores raw bytes. It applies broadly and can capture an unrelated hydrated asset too.
[Attribute cases](TEST-CASES.md#a01-case-sensitive) · [Opt-out](TEST-CASES.md#c01-disable).

### Hydration and temporary workspaces

`jj run` captured an ordinary edit while preserving the filtered pointer. External `git lfs
checkout`
hydrated an additional workspace and restored a sparse-reset asset. With a missing local object,
pointers stayed intact; restoring the object allowed hydration. Malformed pointer-like disk content
was left unchanged: this is exclusion, not pointer validation.
[Temporary snapshot](TEST-CASES.md#w04-run) · [Workspace](TEST-CASES.md#w03-workspace) ·
[Sparse reset](TEST-CASES.md#w01-sparse) · [Missing object](TEST-CASES.md#p04-missing-object).

A direct jj clone produced pointers. In isolated configuration, `git lfs pull` downloaded objects
but exited 0 while skipping checkout because LFS was not installed locally. Running
`git lfs install --local` then pulling again hydrated both assets. Exit status alone was
insufficient.
[Clone/hydration case](TEST-CASES.md#x07-clone-hydration).

### Hosted publication and transfer errors

An ordinary jj edit beside an LFS asset pushed and survived a fresh clone. Publishing a new pointer
without its object failed with GitHub `GH008`, leaving the remote ref unchanged. Explicit
`git lfs push --object-id`, retrying jj push, and cloning again hydrated both assets. This verifies
a
manual handoff, not automatic LFS upload. Lock/list/unlock worked, but lock enforcement by jj was
not tested. The default source archive contained pointers.
[Hosted checks](TEST-CASES.md#x03-hosted-roundtrip).

Seven controlled `git lfs fetch` failures covered batch HTTP errors, per-object errors, and corrupt
bytes. Every fetch failed; jj remained usable; disk/stored pointers and the empty cache were
unchanged.
Those checks belong to external Git LFS, not a jj transfer implementation.
[Individual errors and diagnostics](TEST-CASES.md#x04-transport-failures).

### Lifecycle and performance

Absolute custom storage, skip-smudge, and bounded external migration/import probes worked.
Ordinary/recent prune dry runs retained the tested jj-only objects. Forced pruning deleted payloads;
operation recovery restored pointers, not missing object bytes. Long-aged retention remains
untested.
[Lifecycle cases and their exact criteria](TEST-CASES.md#x05-lifecycle).

Warm release medians with filtering on/off were 18.29/18.28 ms for empty attributes, 27.77/19.85 ms
for 5,000 root patterns, and 30.00/30.88 ms for 60 nested attribute files, each with 3,000 ordinary
files.
A 64 MiB asset retained its payload and 133-byte pointer; status took 16.40 ms. These measurements
show bounded local overhead, not a production latency or memory guarantee.
[Fixtures and raw timings](TEST-CASES.md#x06-performance-config).

## Validation boundaries

174 distinct relevant upstream tests passed; Windows repeated 33 focused tests. The independent
Windows sweep has 30 audited passes, six failures, and four skips. Two original failures were
path-separator mistakes in the harness; the correction uses recorded output, not a rerun.
[Suite coverage](TEST-CASES.md#x10-upstream-tests) · [Counts and corrections](METHODOLOGY.md).

Replaying onto the tested main revision conflicts in `CHANGELOG.md` and `Cargo.lock`; no resolved
build was tested. Public `jj-lib` field/enum additions can break downstream source; no downstream
crate was compiled. These remain separate integration/release considerations.
[Main replay](TEST-CASES.md#x08-rebase-main) · [API review](TEST-CASES.md#x09-api-compatibility).

[Remaining coverage](FOLLOW-UP.md) includes Windows ACLs, CRLF conversion, case-only renames,
release builds, and broader retention/hosting scenarios. Resolve the findings against an explicit
support contract, then rerun the critical cases on the resulting head.
