# Test cases

This is the case reference for [the findings](FINDINGS.md). Core cases are sorted by their original
IDs. `X01`–`X10` are document IDs assigned to supplementary investigations; their original worker
IDs
remain in the evidence. They are not additional independent cases to add to the 40-case pass counts.

## Target and result key

Source: [PR 9635](https://github.com/jj-vcs/jj/pull/9635), pinned at
`d8a56d1a38cae110529ef8e67e72e3e2057ed3ca`. Exact parent:
`e9f48b3e4c1c5e816fbbfbfd06c154a6a96b0215`. Evaluation date: 25 September 2026.

Each core result line lists **macOS release / macOS debug / Linux debug / Windows debug**, in that
order. PASS means the stated criterion held, including criteria that deliberately characterize
limited behavior. FAIL is a gap against that criterion, not automatically a merge blocker. SKIP
means
no assertion ran. PASS-AUDITED corrects a Windows path-separator comparison from recorded commands;
it does not claim a rerun. Green CI means the harness ran, not that every case passed.

## Shared fixture and commands

Unless overridden, each core case starts in a fresh colocated repository containing:

- `.gitattributes`: `*.bin filter=lfs diff=lfs merge=lfs -text`.
- `asset.bin`: 2,500 deterministic payload bytes on disk and a 129-byte LFS pointer in history.
- `note.txt`: an ordinary tracked file.

The harness creates the pointer/object through Git LFS, commits the seed with Git, then runs
`jj git init --colocate`. This is deliberate fixture construction. It isolates Git/jj configuration,
disables signing, sets `core.autocrlf=false`, and uses a 16 MiB new-file limit. Each later case
mutation
is described below. `jj` means the pinned binary for that configuration. Command blocks show the
operations under test, not a complete standalone setup script; full argv, stdout, stderr, return
codes,
and byte hashes are linked in each case. Tests inspect both disk and stored bytes where stated.

To execute a case with its complete setup, run from this repository:

```sh
python3 harness/evaluate.py --jj /path/to/pinned/jj \
  --out /tmp/jj-lfs-new-fixture --only A04-removed
```

Use a fresh output path and Python 3, Git, and Git LFS. Omit `--only` for the full core sweep.
The harness selects by substring, so `--only A01` runs all A01 variants. Supplementary
investigations
use archived worker scripts and are not selected by this entry point.

## Case index

- [A01-case-sensitive](#a01-case-sensitive): Case sensitive.
- [A01-directory-only](#a01-directory-only): Directory only.
- [A01-filter-set](#a01-filter-set): Filter set.
- [A01-last-wins](#a01-last-wins): Last wins.
- [A01-macro](#a01-macro): Macro.
- [A01-nested-set](#a01-nested-set): Nested set.
- [A01-nested-unset](#a01-nested-unset): Nested unset.
- [A01-quoted-space](#a01-quoted-space): Quoted space.
- [A01-recursive](#a01-recursive): Recursive.
- [A01-subdir-relative](#a01-subdir-relative): Subdir relative.
- [A01-unicode](#a01-unicode): Unicode.
- [A01-unspecified](#a01-unspecified): Unspecified.
- [A02-info-attributes](#a02-info-attributes): Rules in .git/info/attributes.
- [A03-global-attributes](#a03-global-attributes): Rules in core.attributesFile.
- [A04-removed](#a04-removed): Delete .gitattributes.
- [A05-unset](#a05-unset): Unset an existing filter.
- [A06-existing-file](#a06-existing-file): Add a filter to an ordinary tracked file.
- [A07-symlink-attrs](#a07-symlink-attrs): Symlinked .gitattributes.
- [A08-symlink-asset](#a08-symlink-asset): An asset path is a symlink.
- [A09-ignored-directory](#a09-ignored-directory): Tracked files inside an ignored directory.
- [A10-file-directory](#a10-file-directory): Replace a file with a directory.
- [C01-disable](#c01-disable): Disable snapshot exclusion.
- [C02-force-track](#c02-force-track): Explicitly track an excluded path.
- [C03-invalid-config](#c03-invalid-config): Reject an invalid configuration type.
- [D01-permission](#d01-permission): Unreadable attribute file.
- [D02-executable](#d02-executable): Change only the executable bit.
- [N01-performance](#n01-performance): Warm snapshot timing.
- [P01-pointer](#p01-pointer): Literal pointer on disk.
- [P02-malformed](#p02-malformed): Malformed pointer-like disk content.
- [P03-empty](#p03-empty): Empty LFS-matched file.
- [P04-missing-object](#p04-missing-object): Missing local object and recovery.
- [S01-hydrated](#s01-hydrated): Repeated snapshots and ordinary edits.
- [S02-delete](#s02-delete): Excluded asset: delete.
- [S02-modify](#s02-modify): Excluded asset: modify.
- [S02-new](#s02-new): Excluded asset: new.
- [S02-rename](#s02-rename): Excluded asset: rename.
- [W01-sparse](#w01-sparse): Sparse reset and hydration.
- [W02-sparse-dirty](#w02-sparse-dirty): Sparse removal of an edited asset.
- [W03-workspace](#w03-workspace): Hydrate an additional workspace.
- [W04-run](#w04-run): Temporary snapshot in jj run.

- [X01-checkout-rebase](#x01-checkout-rebase): Checkout, rebase, and related workflow probes.
- [X02-untrack-recipe](#x02-untrack-recipe): Documented untrack procedure.
- [X03-hosted-roundtrip](#x03-hosted-roundtrip): Real GitHub publication.
- [X04-transport-failures](#x04-transport-failures): Controlled external transfer failures.
- [X05-lifecycle](#x05-lifecycle): Storage, pruning, and migration.
- [X06-performance-config](#x06-performance-config): Performance and configuration probes.
- [X07-clone-hydration](#x07-clone-hydration): Direct jj clone and hydration.
- [X08-rebase-main](#x08-rebase-main): Replay on main.
- [X09-api-compatibility](#x09-api-compatibility): Public Rust API compatibility.
- [X10-upstream-tests](#x10-upstream-tests): Existing regression suites and builds.

## A01-case-sensitive

**Case sensitive.** A differently cased extension must follow Git attribute matching semantics.

**Result:** PASS / PASS / PASS / PASS.

**Setup:** Start with only `note.txt` committed. Write the rules below, then create `a.bin` with
payload bytes.

`.gitattributes`:

```gitattributes
*.BIN filter=lfs
```

**Criterion:** Include the new asset in the jj tree; `git check-attr` supplies the reference
attribute decision.

**Commands:**

```sh
git check-attr filter -- "a.bin"
jj status
jj file list
```

**Observed:** The asset was present in `jj file list` on all four configurations, matching the Git
decision.

**Interpretation:** This checks one path and the shown rules, not every attribute construct.

**Evidence:** [macOS release](evidence/macos-release/A01-case-sensitive.json),
[macOS debug](evidence/macos/A01-case-sensitive.json),
[Linux debug](evidence/linux-modern/A01-case-sensitive.json),
[Windows debug](evidence/windows/cases/A01-case-sensitive.json).

## A01-directory-only

**Directory only.** A directory-only pattern must not implicitly filter every descendant.

**Result:** PASS / PASS / PASS / PASS-AUDITED.

**Setup:** Start with only `note.txt` committed. Write the rules below, then create `assets/a.bin`
with payload bytes.

`.gitattributes`:

```gitattributes
assets/ filter=lfs
```

**Criterion:** Include the new asset in the jj tree; `git check-attr` supplies the reference
attribute decision.

**Commands:**

```sh
git check-attr filter -- "assets/a.bin"
jj status
jj file list
```

**Observed:** The asset was present in `jj file list` on all four configurations, matching the Git
decision. Windows initially failed only because the assertion compared `/` with `\`; inspection of
the recorded path list establishes inclusion. This is an audited result, not a rerun.

**Interpretation:** This checks one path and the shown rules, not every attribute construct.

**Evidence:** [macOS release](evidence/macos-release/A01-directory-only.json),
[macOS debug](evidence/macos/A01-directory-only.json),
[Linux debug](evidence/linux-modern/A01-directory-only.json),
[Windows debug](evidence/windows/cases/A01-directory-only.json).

## A01-filter-set

**Filter set.** A boolean attribute value is not the string-valued LFS filter.

**Result:** PASS / PASS / PASS / PASS.

**Setup:** Start with only `note.txt` committed. Write the rules below, then create `a.bin` with
payload bytes.

`.gitattributes`:

```gitattributes
*.bin filter
```

**Criterion:** Include the new asset in the jj tree; `git check-attr` supplies the reference
attribute decision.

**Commands:**

```sh
git check-attr filter -- "a.bin"
jj status
jj file list
```

**Observed:** The asset was present in `jj file list` on all four configurations, matching the Git
decision.

**Interpretation:** This checks one path and the shown rules, not every attribute construct.

**Evidence:** [macOS release](evidence/macos-release/A01-filter-set.json),
[macOS debug](evidence/macos/A01-filter-set.json),
[Linux debug](evidence/linux-modern/A01-filter-set.json),
[Windows debug](evidence/windows/cases/A01-filter-set.json).

## A01-last-wins

**Last wins.** The later matching assignment must determine which filter applies.

**Result:** PASS / PASS / PASS / PASS.

**Setup:** Start with only `note.txt` committed. Write the rules below, then create `a.bin` with
payload bytes.

`.gitattributes`:

```gitattributes
*.bin filter=lfs
*.bin filter=other
```

**Criterion:** Include the new asset in the jj tree; `git check-attr` supplies the reference
attribute decision.

**Commands:**

```sh
git check-attr filter -- "a.bin"
jj status
jj file list
```

**Observed:** The asset was present in `jj file list` on all four configurations, matching the Git
decision.

**Interpretation:** This checks one path and the shown rules, not every attribute construct.

**Evidence:** [macOS release](evidence/macos-release/A01-last-wins.json),
[macOS debug](evidence/macos/A01-last-wins.json),
[Linux debug](evidence/linux-modern/A01-last-wins.json),
[Windows debug](evidence/windows/cases/A01-last-wins.json).

## A01-macro

**Macro.** A root attribute macro must expand to the configured filter value.

**Result:** PASS / PASS / PASS / PASS.

**Setup:** Start with only `note.txt` committed. Write the rules below, then create `a.bin` with
payload bytes.

`.gitattributes`:

```gitattributes
[attr]large filter=lfs -text
*.bin large
```

**Criterion:** Exclude the new asset from the jj tree; `git check-attr` supplies the reference
attribute decision.

**Commands:**

```sh
git check-attr filter -- "a.bin"
jj status
jj file list
```

**Observed:** The asset was absent from `jj file list` on all four configurations, matching the Git
decision.

**Interpretation:** This checks one path and the shown rules, not every attribute construct.

**Evidence:** [macOS release](evidence/macos-release/A01-macro.json),
[macOS debug](evidence/macos/A01-macro.json),
[Linux debug](evidence/linux-modern/A01-macro.json),
[Windows debug](evidence/windows/cases/A01-macro.json).

## A01-nested-set

**Nested set.** A child directory must be able to enable filtering under an unfiltered parent.

**Result:** PASS / PASS / PASS / PASS.

**Setup:** Start with only `note.txt` committed. Write the rules below, then create `sub/a.bin` with
payload bytes.

`.gitattributes`:

```gitattributes
*.bin -filter
```

`sub/.gitattributes`:

```gitattributes
*.bin filter=lfs
```

**Criterion:** Exclude the new asset from the jj tree; `git check-attr` supplies the reference
attribute decision.

**Commands:**

```sh
git check-attr filter -- "sub/a.bin"
jj status
jj file list
```

**Observed:** The asset was absent from `jj file list` on all four configurations, matching the Git
decision.

**Interpretation:** This checks one path and the shown rules, not every attribute construct.

**Evidence:** [macOS release](evidence/macos-release/A01-nested-set.json),
[macOS debug](evidence/macos/A01-nested-set.json),
[Linux debug](evidence/linux-modern/A01-nested-set.json),
[Windows debug](evidence/windows/cases/A01-nested-set.json).

## A01-nested-unset

**Nested unset.** A child directory must be able to disable a parent filter rule.

**Result:** PASS / PASS / PASS / PASS-AUDITED.

**Setup:** Start with only `note.txt` committed. Write the rules below, then create `sub/a.bin` with
payload bytes.

`.gitattributes`:

```gitattributes
*.bin filter=lfs
```

`sub/.gitattributes`:

```gitattributes
*.bin -filter
```

**Criterion:** Include the new asset in the jj tree; `git check-attr` supplies the reference
attribute decision.

**Commands:**

```sh
git check-attr filter -- "sub/a.bin"
jj status
jj file list
```

**Observed:** The asset was present in `jj file list` on all four configurations, matching the Git
decision. Windows initially failed only because the assertion compared `/` with `\`; inspection of
the recorded path list establishes inclusion. This is an audited result, not a rerun.

**Interpretation:** This checks one path and the shown rules, not every attribute construct.

**Evidence:** [macOS release](evidence/macos-release/A01-nested-unset.json),
[macOS debug](evidence/macos/A01-nested-unset.json),
[Linux debug](evidence/linux-modern/A01-nested-unset.json),
[Windows debug](evidence/windows/cases/A01-nested-unset.json).

## A01-quoted-space

**Quoted space.** Quoting must preserve a filename containing a space.

**Result:** PASS / PASS / PASS / PASS.

**Setup:** Start with only `note.txt` committed. Write the rules below, then create `space name.bin`
with payload bytes.

`.gitattributes`:

```gitattributes
"space name.bin" filter=lfs
```

**Criterion:** Exclude the new asset from the jj tree; `git check-attr` supplies the reference
attribute decision.

**Commands:**

```sh
git check-attr filter -- "space name.bin"
jj status
jj file list
```

**Observed:** The asset was absent from `jj file list` on all four configurations, matching the Git
decision.

**Interpretation:** This checks one path and the shown rules, not every attribute construct.

**Evidence:** [macOS release](evidence/macos-release/A01-quoted-space.json),
[macOS debug](evidence/macos/A01-quoted-space.json),
[Linux debug](evidence/linux-modern/A01-quoted-space.json),
[Windows debug](evidence/windows/cases/A01-quoted-space.json).

## A01-recursive

**Recursive.** An explicit recursive pattern must filter descendants.

**Result:** PASS / PASS / PASS / PASS.

**Setup:** Start with only `note.txt` committed. Write the rules below, then create
`assets/sub/a.bin` with payload bytes.

`.gitattributes`:

```gitattributes
assets/** filter=lfs
```

**Criterion:** Exclude the new asset from the jj tree; `git check-attr` supplies the reference
attribute decision.

**Commands:**

```sh
git check-attr filter -- "assets/sub/a.bin"
jj status
jj file list
```

**Observed:** The asset was absent from `jj file list` on all four configurations, matching the Git
decision.

**Interpretation:** This checks one path and the shown rules, not every attribute construct.

**Evidence:** [macOS release](evidence/macos-release/A01-recursive.json),
[macOS debug](evidence/macos/A01-recursive.json),
[Linux debug](evidence/linux-modern/A01-recursive.json),
[Windows debug](evidence/windows/cases/A01-recursive.json).

## A01-subdir-relative

**Subdir relative.** A nested attribute pattern must resolve relative to its containing directory.

**Result:** PASS / PASS / PASS / PASS.

**Setup:** Start with only `note.txt` committed. Write the rules below, then create `sub/a.bin` with
payload bytes.

`sub/.gitattributes`:

```gitattributes
a.bin filter=lfs
```

**Criterion:** Exclude the new asset from the jj tree; `git check-attr` supplies the reference
attribute decision.

**Commands:**

```sh
git check-attr filter -- "sub/a.bin"
jj status
jj file list
```

**Observed:** The asset was absent from `jj file list` on all four configurations, matching the Git
decision.

**Interpretation:** This checks one path and the shown rules, not every attribute construct.

**Evidence:** [macOS release](evidence/macos-release/A01-subdir-relative.json),
[macOS debug](evidence/macos/A01-subdir-relative.json),
[Linux debug](evidence/linux-modern/A01-subdir-relative.json),
[Windows debug](evidence/windows/cases/A01-subdir-relative.json).

## A01-unicode

**Unicode.** A non-ASCII filename must match the same pattern as an ASCII filename.

**Result:** PASS / PASS / PASS / PASS.

**Setup:** Start with only `note.txt` committed. Write the rules below, then create `café.bin` with
payload bytes.

`.gitattributes`:

```gitattributes
*.bin filter=lfs
```

**Criterion:** Exclude the new asset from the jj tree; `git check-attr` supplies the reference
attribute decision.

**Commands:**

```sh
git check-attr filter -- "café.bin"
jj status
jj file list
```

**Observed:** The asset was absent from `jj file list` on all four configurations, matching the Git
decision.

**Interpretation:** This checks one path and the shown rules, not every attribute construct.

**Evidence:** [macOS release](evidence/macos-release/A01-unicode.json),
[macOS debug](evidence/macos/A01-unicode.json),
[Linux debug](evidence/linux-modern/A01-unicode.json),
[Windows debug](evidence/windows/cases/A01-unicode.json).

## A01-unspecified

**Unspecified.** An explicit unspecified value must cancel an earlier filter assignment.

**Result:** PASS / PASS / PASS / PASS.

**Setup:** Start with only `note.txt` committed. Write the rules below, then create `a.bin` with
payload bytes.

`.gitattributes`:

```gitattributes
*.bin filter=lfs
a.bin !filter
```

**Criterion:** Include the new asset in the jj tree; `git check-attr` supplies the reference
attribute decision.

**Commands:**

```sh
git check-attr filter -- "a.bin"
jj status
jj file list
```

**Observed:** The asset was present in `jj file list` on all four configurations, matching the Git
decision.

**Interpretation:** This checks one path and the shown rules, not every attribute construct.

**Evidence:** [macOS release](evidence/macos-release/A01-unspecified.json),
[macOS debug](evidence/macos/A01-unspecified.json),
[Linux debug](evidence/linux-modern/A01-unspecified.json),
[Windows debug](evidence/windows/cases/A01-unspecified.json).

## A02-info-attributes

**Rules in .git/info/attributes.** Identify assets Git treats as LFS but jj does not exclude.

**Result:** FAIL / FAIL / FAIL / FAIL.

**Setup:** Commit no root filter rule. Write `a.bin filter=lfs` only to `.git/info/attributes`, then
create `a.bin`.

**Criterion:** For full Git-attribute compatibility, a path with `filter=lfs` would be excluded.

**Commands:**

```sh
git check-attr filter -- a.bin
jj status
jj file list
jj file show a.bin
```

**Observed:** Git reported `lfs`; jj included the file and stored the raw payload on every
configuration.

**Interpretation:** This is an unsupported attribute source, not an established regression. See
[F07](FINDINGS.md#f07).

**Evidence:** [macOS release](evidence/macos-release/A02-info-attributes.json),
[macOS debug](evidence/macos/A02-info-attributes.json),
[Linux debug](evidence/linux-modern/A02-info-attributes.json),
[Windows debug](evidence/windows/cases/A02-info-attributes.json).

### F07 manual reproduction

Run the [shared manual setup](#manual-reproduction-setup) once, then this block in the same Bash
session. It was verified against the pinned macOS debug binary. These smaller fixtures confirm the
finding; they do not add core scenarios or constitute a Windows rerun.

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

[Recorded output](evidence/manual-reproductions/F07.txt) · [Finding F07](FINDINGS.md#f07).

## A03-global-attributes

**Rules in core.attributesFile.** Check the other common source of user-defined LFS rules.

**Result:** FAIL / FAIL / FAIL / FAIL.

**Setup:** Commit no root filter rule. Point `core.attributesFile` at an absolute fixture file
containing `a.bin filter=lfs`; create `a.bin`.

**Criterion:** For full compatibility, exclude the file Git identifies as LFS.

**Commands:**

```sh
git check-attr filter -- a.bin
jj status
jj file list
jj file show a.bin
```

**Observed:** Git reported `lfs`; jj stored the raw payload on every configuration.

**Interpretation:** The configured global attribute source is outside the implemented lookup. See
[F07](FINDINGS.md#f07).

**Evidence:** [macOS release](evidence/macos-release/A03-global-attributes.json),
[macOS debug](evidence/macos/A03-global-attributes.json),
[Linux debug](evidence/linux-modern/A03-global-attributes.json),
[Windows debug](evidence/windows/cases/A03-global-attributes.json).

## A04-removed

**Delete .gitattributes.** A read-only status sequence should not produce successive content changes
when disk contents do not change.

**Result:** FAIL / FAIL / FAIL / FAIL.

**Setup:** Use the hydrated seed. Delete `.gitattributes` once, then leave disk contents unchanged.

**Criterion:** The first and second stored-content hashes should agree.

**Commands:**

```sh
jj status
jj --ignore-working-copy file show asset.bin
jj status
jj --ignore-working-copy file show asset.bin
jj status
jj --ignore-working-copy file show asset.bin
```

**Observed:** The first snapshot retained the pointer; the second replaced it with raw payload; the
third was stable, on all configurations.

**Interpretation:** `--ignore-working-copy` prevents the inspection itself from taking another
snapshot. See [F04](FINDINGS.md#f04).

**Evidence:** [macOS release](evidence/macos-release/A04-removed.json),
[macOS debug](evidence/macos/A04-removed.json),
[Linux debug](evidence/linux-modern/A04-removed.json),
[Windows debug](evidence/windows/cases/A04-removed.json).

### F04 manual reproduction

Run the [shared manual setup](#manual-reproduction-setup) once, then this block in the same Bash
session. It was verified against the pinned macOS debug binary. These smaller fixtures confirm the
finding; they do not add core scenarios or constitute a Windows rerun.

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

[Recorded output](evidence/manual-reproductions/F04.txt) · [Finding F04](FINDINGS.md#f04).

## A05-unset

**Unset an existing filter.** Distinguish explicit rule removal from deleting the attribute file.

**Result:** PASS / PASS / PASS / PASS.

**Setup:** Replace the seed rule with `*.bin -filter` while leaving the asset hydrated.

**Criterion:** Snapshot the ordinary raw bytes after disabling the filter.

**Commands:**

```sh
jj status
jj file show asset.bin
```

**Observed:** The stored bytes matched the payload on all configurations.

**Interpretation:** This is an explicit transition to ordinary storage, not automatic LFS cleaning.

**Evidence:** [macOS release](evidence/macos-release/A05-unset.json),
[macOS debug](evidence/macos/A05-unset.json),
[Linux debug](evidence/linux-modern/A05-unset.json),
[Windows debug](evidence/windows/cases/A05-unset.json).

## A06-existing-file

**Add a filter to an ordinary tracked file.** Check whether adding attributes converts already
stored data.

**Result:** PASS / PASS / PASS / PASS.

**Setup:** Seed an ordinary raw `asset.bin` with empty attributes. Add `*.bin filter=lfs` and edit
the disk payload.

**Criterion:** Retain the old stored bytes and leave the edited disk bytes intact during exclusion.

**Commands:**

```sh
jj status
jj file show asset.bin
```

**Observed:** Both byte comparisons passed on all configurations: old raw content remained stored;
edited content remained on disk.

**Interpretation:** Adding the rule does not retroactively turn raw history into LFS pointers.

**Evidence:** [macOS release](evidence/macos-release/A06-existing-file.json),
[macOS debug](evidence/macos/A06-existing-file.json),
[Linux debug](evidence/linux-modern/A06-existing-file.json),
[Windows debug](evidence/windows/cases/A06-existing-file.json).

## A07-symlink-attrs

**Symlinked .gitattributes.** Avoid reading filter rules through a symlink.

**Result:** PASS / PASS / PASS / SKIP.

**Setup:** Create `rules` containing `*.bin filter=lfs`; replace `.gitattributes` with a symlink to
it; create `new.bin`.

**Criterion:** Do not follow the symlink; track `new.bin` as ordinary content.

**Commands:**

```sh
jj status
jj file list
```

**Observed:** The asset was tracked on macOS and Linux. Windows explicitly skipped this case.

**Interpretation:** No Windows symlink result is claimed.

**Evidence:** [macOS release](evidence/macos-release/A07-symlink-attrs.json),
[macOS debug](evidence/macos/A07-symlink-attrs.json),
[Linux debug](evidence/linux-modern/A07-symlink-attrs.json),
[Windows debug](evidence/windows/cases/A07-symlink-attrs.json).

## A08-symlink-asset

**An asset path is a symlink.** Git stores a symlink as a link, even if its name matches an LFS
pattern.

**Result:** FAIL / FAIL / FAIL / SKIP.

**Setup:** Seed the LFS rule and ordinary `note.txt`. Create `link.bin` as a symlink to `note.txt`,
then stage it with Git for the comparison.

**Criterion:** Keep the symlink in the jj tree; the Git index should identify mode `120000`.

**Commands:**

```sh
git add link.bin
git ls-files --stage link.bin
jj status
jj file list
```

**Observed:** Git recorded the symlink, but jj omitted `link.bin` on macOS and Linux. Windows
skipped the test.

**Interpretation:** See [F05](FINDINGS.md#f05). This tests a symlink matching a filter pattern, not
a hydrated regular file.

**Evidence:** [macOS release](evidence/macos-release/A08-symlink-asset.json),
[macOS debug](evidence/macos/A08-symlink-asset.json),
[Linux debug](evidence/linux-modern/A08-symlink-asset.json),
[Windows debug](evidence/windows/cases/A08-symlink-asset.json).

### F05 manual reproduction

Run the [shared manual setup](#manual-reproduction-setup) once, then this block in the same Bash
session. It was verified against the pinned macOS debug binary. These smaller fixtures confirm the
finding; they do not add core scenarios or constitute a Windows rerun.

```sh
new_case F05 || exit 1
python3 -c 'from pathlib import Path; Path("link.bin").symlink_to("note.txt")'
git add link.bin
git ls-files --stage link.bin
jj status
jj file list
```

[Recorded output](evidence/manual-reproductions/F05.txt) · [Finding F05](FINDINGS.md#f05).

## A09-ignored-directory

**Tracked files inside an ignored directory.** Exercise the traversal shortcut for directories that
contain tracked files.

**Result:** PASS / PASS / PASS / PASS.

**Setup:** Seed `ignored/asset.bin` and `ignored/note.txt`. Add `ignored/` to `.gitignore`, then
edit both files.

**Criterion:** Preserve the LFS pointer but capture the tracked ordinary edit.

**Commands:**

```sh
jj status
jj file show ignored/asset.bin
jj file show ignored/note.txt
```

**Observed:** Both stored-byte assertions passed on every configuration.

**Evidence:** [macOS release](evidence/macos-release/A09-ignored-directory.json),
[macOS debug](evidence/macos/A09-ignored-directory.json),
[Linux debug](evidence/linux-modern/A09-ignored-directory.json),
[Windows debug](evidence/windows/cases/A09-ignored-directory.json).

## A10-file-directory

**Replace a file with a directory.** Changing path kind must not leave contradictory cached file
states.

**Result:** PASS / FAIL / FAIL / FAIL.

**Setup:** Remove seeded `asset.bin`, create directory `asset.bin`, and write `asset.bin/child.txt`.

**Criterion:** Status should complete with exit 0 without violating an internal assertion.

**Commands:**

```sh
jj status
jj file list
```

**Observed:** macOS release completed successfully. macOS debug, Linux debug, and Windows debug
exited 101 at the file-state assertion. The file list is read only when status succeeds.

**Interpretation:** Independent transition probes show the exact parent passes. A release crash was
not demonstrated. See [F03](FINDINGS.md#f03).

**Evidence:** [macOS release](evidence/macos-release/A10-file-directory.json),
[macOS debug](evidence/macos-recheck/A10-file-directory.json),
[Linux debug](evidence/linux-modern/A10-file-directory.json),
[Windows debug](evidence/windows/cases/A10-file-directory.json).

### F03 manual reproduction

Run the [shared manual setup](#manual-reproduction-setup) once, then this block in the same Bash
session. It was verified against the pinned macOS debug binary. These smaller fixtures confirm the
finding; they do not add core scenarios or constitute a Windows rerun.

```sh
new_case F03 || exit 1
rm asset.bin
mkdir asset.bin
printf 'child\n' > asset.bin/child.txt
jj status
printf 'status exit=%s\n' "$?"
```

[Recorded output](evidence/manual-reproductions/F03.txt) · [Finding F03](FINDINGS.md#f03).

## C01-disable

**Disable snapshot exclusion.** Verify the configuration escape hatch.

**Result:** PASS / PASS / PASS / PASS.

**Setup:** Use the hydrated seed with its LFS rule unchanged.

**Criterion:** Snapshot raw payload bytes when exclusion is disabled.

**Commands:**

```sh
jj --config='git.ignore-filters=[]' status
jj file show asset.bin
```

**Observed:** The stored file matched the payload on every configuration.

**Interpretation:** This setting applies broadly; it is not a safe one-file pointer-publication
recipe.

**Evidence:** [macOS release](evidence/macos-release/C01-disable.json),
[macOS debug](evidence/macos/C01-disable.json),
[Linux debug](evidence/linux-modern/C01-disable.json),
[Windows debug](evidence/windows/cases/C01-disable.json).

## C02-force-track

**Explicitly track an excluded path.** An explicit user request needs an actionable outcome.

**Result:** FAIL / FAIL / FAIL / FAIL.

**Setup:** Seed the rule but no asset; create a new hydrated `new.bin`.

**Criterion:** Either track the path, return a failure, or explain filter exclusion in stderr.

**Commands:**

```sh
jj file track new.bin
jj file list
```

**Observed:** Exit 0, empty stderr, and no `new.bin` in the tree on every configuration.

**Interpretation:** The assertion accepts any of the three outcomes above; it does not require a
particular UX. See [F06](FINDINGS.md#f06).

**Evidence:** [macOS release](evidence/macos-release/C02-force-track.json),
[macOS debug](evidence/macos/C02-force-track.json),
[Linux debug](evidence/linux-modern/C02-force-track.json),
[Windows debug](evidence/windows/cases/C02-force-track.json).

### F06 manual reproduction

Run the [shared manual setup](#manual-reproduction-setup) once, then this block in the same Bash
session. It was verified against the pinned macOS debug binary. These smaller fixtures confirm the
finding; they do not add core scenarios or constitute a Windows rerun.

```sh
new_case F06 || exit 1
printf 'new payload\n' > new.bin
jj file track new.bin > "$LAB/F06-out" 2> "$LAB/F06-err"
printf 'track exit=%s\n' "$?"
printf 'stderr bytes='; wc -c < "$LAB/F06-err"
jj file list
```

[Recorded output](evidence/manual-reproductions/F06.txt) · [Finding F06](FINDINGS.md#f06).

## C03-invalid-config

**Reject an invalid configuration type.** Misconfiguration should identify the offending key.

**Result:** PASS / PASS / PASS / PASS.

**Setup:** Use the hydrated seed. Supply a string where the filter list is required.

**Criterion:** Return nonzero and mention `ignore-filters` in stderr.

**Commands:**

```sh
jj --config='git.ignore-filters="lfs"' status
```

**Observed:** Both checks passed on every configuration.

**Interpretation:** This checks type validation and key context, not all configuration errors.

**Evidence:** [macOS release](evidence/macos-release/C03-invalid-config.json),
[macOS debug](evidence/macos/C03-invalid-config.json),
[Linux debug](evidence/linux-modern/C03-invalid-config.json),
[Windows debug](evidence/windows/cases/C03-invalid-config.json).

## D01-permission

**Unreadable attribute file.** Filesystem read failure should identify the affected path.

**Result:** PASS / PASS / SKIP / SKIP.

**Setup:** Use the hydrated seed; set `.gitattributes` mode to `000`, restoring permissions after
the probe.

**Criterion:** Return nonzero with `.gitattributes` in stderr.

**Commands:**

```sh
jj status
```

**Observed:** macOS debug and release met the criterion. Linux ran as root and skipped it; Windows
skipped Unix mode enforcement.

**Interpretation:** Windows ACL/read-only behavior is untested.

**Evidence:** [macOS release](evidence/macos-release/D01-permission.json),
[macOS debug](evidence/macos/D01-permission.json),
[Linux debug](evidence/linux-modern/D01-permission.json),
[Windows debug](evidence/windows/cases/D01-permission.json).

## D02-executable

**Change only the executable bit.** Characterize metadata-only edits to an excluded asset.

**Result:** PASS / PASS / PASS / SKIP.

**Setup:** Use the hydrated seed; change `asset.bin` mode to `0755` without changing its bytes.

**Criterion:** The stored LFS pointer remains intact.

**Commands:**

```sh
jj status
git diff --summary
jj file show asset.bin
```

**Observed:** Pointer preservation passed on macOS and Linux. Windows skipped Unix executable-bit
semantics.

**Interpretation:** The assertion checks pointer bytes; it does not establish that jj records the
desired executable flag.

**Evidence:** [macOS release](evidence/macos-release/D02-executable.json),
[macOS debug](evidence/macos/D02-executable.json),
[Linux debug](evidence/linux-modern/D02-executable.json),
[Windows debug](evidence/windows/cases/D02-executable.json).

## N01-performance

**Warm snapshot timing.** Measure the enabled/disabled cost on the same tree and binary.

**Result:** PASS / PASS / PASS / PASS.

**Setup:** Create 3,000 ordinary files beneath 120 directories, each with a `.gitattributes` file.
Warm the snapshot, then alternate five enabled and five disabled runs.

**Criterion:** All commands complete and all 3,122 expected files remain tracked. Record timings
without a latency pass threshold.

**Commands:**

```sh
jj status
jj --config='git.ignore-filters=["lfs"]' status
jj --config='git.ignore-filters=[]' status
jj file list
```

**Observed:** The file-count assertion passed on all configurations; per-run timings are in the
evidence.

**Interpretation:** A PASS does not certify performance. Different machines/profiles cannot be
compared as paired runs; see [X06](#x06-performance-config).

**Evidence:** [macOS release](evidence/macos-release/N01-performance.json),
[macOS debug](evidence/macos/N01-performance.json),
[Linux debug](evidence/linux-modern/N01-performance.json),
[Windows debug](evidence/windows/cases/N01-performance.json).

## P01-pointer

**Literal pointer on disk.** Preserve a valid pointer as well as an already hydrated asset.

**Result:** PASS / PASS / PASS / PASS.

**Setup:** Replace the hydrated disk file with its canonical pointer bytes.

**Criterion:** Keep the original stored pointer and preserve the pointer bytes on disk.

**Commands:**

```sh
jj status
jj file show asset.bin
```

**Observed:** Both byte comparisons passed on all configurations.

**Evidence:** [macOS release](evidence/macos-release/P01-pointer.json),
[macOS debug](evidence/macos/P01-pointer.json),
[Linux debug](evidence/linux-modern/P01-pointer.json),
[Windows debug](evidence/windows/cases/P01-pointer.json).

## P02-malformed

**Malformed pointer-like disk content.** Check whether excluded content is parsed or merely left
alone.

**Result:** PASS / PASS / PASS / PASS.

**Setup:** Replace the disk file with a pointer-like string containing `oid sha256:bad`.

**Criterion:** Retain the valid pointer already stored, while leaving the malformed disk bytes
unchanged.

**Commands:**

```sh
jj status
jj file show asset.bin
```

**Observed:** Both assertions passed on all configurations.

**Interpretation:** This demonstrates exclusion, not pointer validation or safe upload of malformed
pointers.

**Evidence:** [macOS release](evidence/macos-release/P02-malformed.json),
[macOS debug](evidence/macos/P02-malformed.json),
[Linux debug](evidence/linux-modern/P02-malformed.json),
[Windows debug](evidence/windows/cases/P02-malformed.json).

## P03-empty

**Empty LFS-matched file.** Check Git LFS empty-file passthrough.

**Result:** PASS / PASS / PASS / PASS.

**Setup:** Seed `empty.bin` with zero bytes using the LFS rule and Git LFS.

**Criterion:** The stored file remains empty rather than becoming a nonempty pointer.

**Commands:**

```sh
jj file show empty.bin
```

**Observed:** The stored-byte assertion passed on all configurations.

**Interpretation:** The test does not exercise transitions from nonempty content to empty content.

**Evidence:** [macOS release](evidence/macos-release/P03-empty.json),
[macOS debug](evidence/macos/P03-empty.json),
[Linux debug](evidence/linux-modern/P03-empty.json),
[Windows debug](evidence/windows/cases/P03-empty.json).

## P04-missing-object

**Missing local object and recovery.** A failed external hydration must not invent content or
corrupt the stored pointer.

**Result:** PASS / PASS / PASS / PASS.

**Setup:** Delete the cached LFS object and put its pointer on disk. After the first checkout,
restore the known object bytes to the same cache path.

**Criterion:** While missing, both stored and disk files remain pointers. After restoration, disk
bytes match the payload.

**Commands:**

```sh
git lfs checkout
jj status
jj file show asset.bin
# Restore the known object bytes in the LFS cache.
git lfs checkout
jj status
```

**Observed:** All three byte checks passed on all configurations.

**Interpretation:** The initial checkout exit code is recorded but not asserted; missing-object
success is judged from bytes, not exit code alone.

**Evidence:** [macOS release](evidence/macos-release/P04-missing-object.json),
[macOS debug](evidence/macos/P04-missing-object.json),
[Linux debug](evidence/linux-modern/P04-missing-object.json),
[Windows debug](evidence/windows/cases/P04-missing-object.json).

## S01-hydrated

**Repeated snapshots and ordinary edits.** The central use case is editing ordinary files beside
hydrated assets.

**Result:** PASS / PASS / PASS / PASS.

**Setup:** Use the hydrated seed. Run status three times; edit `note.txt`; run status again.

**Criterion:** Keep hydrated bytes on disk and the pointer in the tree, while capturing the ordinary
edit.

**Commands:**

```sh
jj status
jj file show asset.bin
# Edit note.txt; repeat status.
jj status
jj file show note.txt
jj file show asset.bin
```

**Observed:** All byte assertions passed on every configuration.

**Interpretation:** This does not change the asset or exercise a later checkout that overwrites it.

**Evidence:** [macOS release](evidence/macos-release/S01-hydrated.json),
[macOS debug](evidence/macos/S01-hydrated.json),
[Linux debug](evidence/linux-modern/S01-hydrated.json),
[Windows debug](evidence/windows/cases/S01-hydrated.json).

## S02-delete

**Excluded asset: delete.** Characterize exactly which disk changes snapshot exclusion leaves
unrecorded.

**Result:** PASS / PASS / PASS / PASS.

**Setup:** Use the hydrated seed. Delete `asset.bin` from disk.

**Criterion:** Retain the original stored pointer; do not add new or renamed excluded paths.

**Commands:**

```sh
jj status
jj file show asset.bin
jj file list
```

**Observed:** The stored-pointer assertion passed on all configurations. The disk mutation was not
recorded in the jj tree.

**Interpretation:** PASS means exclusion behaved as tested. It does not mean jj supports this asset
operation or protects the unrecorded bytes during checkout. See [F01](FINDINGS.md#f01).

**Evidence:** [macOS release](evidence/macos-release/S02-delete.json),
[macOS debug](evidence/macos/S02-delete.json),
[Linux debug](evidence/linux-modern/S02-delete.json),
[Windows debug](evidence/windows/cases/S02-delete.json).

## S02-modify

**Excluded asset: modify.** Characterize exactly which disk changes snapshot exclusion leaves
unrecorded.

**Result:** PASS / PASS / PASS / PASS.

**Setup:** Use the hydrated seed. Replace the hydrated bytes in `asset.bin` with a second payload.

**Criterion:** Retain the original stored pointer; do not add new or renamed excluded paths.

**Commands:**

```sh
jj status
jj file show asset.bin
jj file list
```

**Observed:** The stored-pointer assertion passed on all configurations. The disk mutation was not
recorded in the jj tree.

**Interpretation:** PASS means exclusion behaved as tested. It does not mean jj supports this asset
operation or protects the unrecorded bytes during checkout. See [F01](FINDINGS.md#f01).

**Evidence:** [macOS release](evidence/macos-release/S02-modify.json),
[macOS debug](evidence/macos/S02-modify.json),
[Linux debug](evidence/linux-modern/S02-modify.json),
[Windows debug](evidence/windows/cases/S02-modify.json).

## S02-new

**Excluded asset: new.** Characterize exactly which disk changes snapshot exclusion leaves
unrecorded.

**Result:** PASS / PASS / PASS / PASS.

**Setup:** Use the hydrated seed. Create `new.bin` with a second payload.

**Criterion:** Retain the original stored pointer; do not add new or renamed excluded paths.

**Commands:**

```sh
jj status
jj file show asset.bin
jj file list
```

**Observed:** Both assertions passed on all configurations. The mutation remained outside the jj
tree.

**Interpretation:** PASS means exclusion behaved as tested. It does not mean jj supports this asset
operation or protects the unrecorded bytes during checkout. See [F01](FINDINGS.md#f01).

**Evidence:** [macOS release](evidence/macos-release/S02-new.json),
[macOS debug](evidence/macos/S02-new.json),
[Linux debug](evidence/linux-modern/S02-new.json),
[Windows debug](evidence/windows/cases/S02-new.json).

## S02-rename

**Excluded asset: rename.** Characterize exactly which disk changes snapshot exclusion leaves
unrecorded.

**Result:** PASS / PASS / PASS / PASS.

**Setup:** Use the hydrated seed. Rename `asset.bin` to `renamed.bin` on disk.

**Criterion:** Retain the original stored pointer; do not add new or renamed excluded paths.

**Commands:**

```sh
jj status
jj file show asset.bin
jj file list
```

**Observed:** Both assertions passed on all configurations. The mutation remained outside the jj
tree.

**Interpretation:** PASS means exclusion behaved as tested. It does not mean jj supports this asset
operation or protects the unrecorded bytes during checkout. See [F01](FINDINGS.md#f01).

**Evidence:** [macOS release](evidence/macos-release/S02-rename.json),
[macOS debug](evidence/macos/S02-rename.json),
[Linux debug](evidence/linux-modern/S02-rename.json),
[Windows debug](evidence/windows/cases/S02-rename.json).

## W01-sparse

**Sparse reset and hydration.** Verify recovery of an unchanged asset after excluding and restoring
its path.

**Result:** PASS / PASS / PASS / PASS.

**Setup:** Seed `assets/asset.bin` and `note.txt`; do not edit the asset.

**Criterion:** After reset and explicit checkout, disk bytes match the original payload.

**Commands:**

```sh
jj sparse set --clear --add note.txt
jj sparse reset
git lfs checkout
```

**Observed:** The final byte assertion passed on all configurations.

**Interpretation:** This covers unchanged content. The dirty-content case below has a different
result.

**Evidence:** [macOS release](evidence/macos-release/W01-sparse.json),
[macOS debug](evidence/macos/W01-sparse.json),
[Linux debug](evidence/linux-modern/W01-sparse.json),
[Windows debug](evidence/windows/cases/W01-sparse.json).

## W02-sparse-dirty

**Sparse removal of an edited asset.** Excluded edits must remain recoverable when a checkout
removes their path.

**Result:** FAIL / FAIL / FAIL / FAIL.

**Setup:** Seed `assets/asset.bin`, then replace its hydrated bytes with a distinct edited payload.

**Criterion:** At least one safeguard holds: the command refuses, the disk file survives, or the
edited bytes are stored in the tree.

**Commands:**

```sh
jj sparse set --clear --add note.txt
jj --ignore-working-copy file show assets/asset.bin
```

**Observed:** All safeguards failed on every PR configuration: exit 0, file removed, and only the
old pointer stored. The exact-parent comparison stored the edited bytes.

**Interpretation:** Parent raw-byte storage breaks LFS semantics but establishes recoverability
before this change. See [F01](FINDINGS.md#f01).

**Evidence:** [macOS release](evidence/macos-release/W02-sparse-dirty.json),
[macOS debug](evidence/macos/W02-sparse-dirty.json),
[Linux debug](evidence/linux-modern/W02-sparse-dirty.json),
[Windows debug](evidence/windows/cases/W02-sparse-dirty.json).

### F01 manual reproduction

Run the [shared manual setup](#manual-reproduction-setup) once, then this block in the same Bash
session. It was verified against the pinned macOS debug binary. These smaller fixtures confirm the
finding; they do not add core scenarios or constitute a Windows rerun.

```sh
new_case F01 assets/asset.bin || exit 1
printf 'unrecorded edit\n' > assets/asset.bin
jj sparse set --clear --add note.txt
printf 'sparse exit=%s\n' "$?"
if test -e assets/asset.bin; then echo 'disk=present'; else echo 'disk=missing'; fi
jj --ignore-working-copy file show assets/asset.bin
```

[Recorded output](evidence/manual-reproductions/F01.txt) · [Finding F01](FINDINGS.md#f01).

## W03-workspace

**Hydrate an additional workspace.** Verify whether an additional colocated workspace supplies Git
context to Git LFS.

**Result:** PASS / PASS / PASS / PASS.

**Setup:** Create an additional workspace from the hydrated seed. Inspect its asset before
hydration, then run the following commands inside that workspace.

**Criterion:** Initial disk content is a pointer; external checkout hydrates it; jj keeps the
pointer stored.

**Commands:**

```sh
git lfs checkout
jj status
jj file show asset.bin
```

**Observed:** All checks passed on every configuration. The additional workspace had a `.git` file.

**Interpretation:** An earlier missing-Git expectation was wrong and is retained as historical
evidence. This does not establish non-colocated workspace support. See [F08](FINDINGS.md#f08).

**Evidence:** [macOS release](evidence/macos-release/W03-workspace.json),
[macOS debug](evidence/macos-recheck/W03-workspace.json),
[Linux debug](evidence/linux-modern/W03-workspace.json),
[Windows debug](evidence/windows/cases/W03-workspace.json).

### F08 manual reproduction

Run the [shared manual setup](#manual-reproduction-setup) once, then this block in the same Bash
session. It was verified against the pinned macOS debug binary. These smaller fixtures confirm the
finding; they do not add core scenarios or constitute a Windows rerun.

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

[Recorded output](evidence/manual-reproductions/F08.txt) · [Finding F08](FINDINGS.md#f08).

## W04-run

**Temporary snapshot in jj run.** Temporary snapshots should apply the same exclusion rule as the
working copy.

**Result:** PASS / PASS / PASS / PASS.

**Setup:** Create `write-run.py` outside the repository; it writes `run mutation` to `asset.bin` and
`run ordinary` to `note.txt`.

**Criterion:** Retain the LFS pointer while capturing the ordinary edit from the temporary
workspace.

**Commands:**

```sh
jj run -r @ -- python /path/to/write-run.py
jj file show asset.bin
jj file show note.txt
```

**Observed:** Both byte assertions passed on all configurations.

**Interpretation:** The command uses the harness Python executable and fixture script path; names
here are normalized.

**Evidence:** [macOS release](evidence/macos-release/W04-run.json),
[macOS debug](evidence/macos/W04-run.json),
[Linux debug](evidence/linux-modern/W04-run.json),
[Windows debug](evidence/windows/cases/W04-run.json).

## X01-checkout-rebase

**Edited payloads during checkout.** Snapshot exclusion is useful only if later checkout operations
preserve edits that jj did not record. This investigation compares the PR with its exact parent.

**Setup:** Commit two LFS pointer versions. Select the first, hydrate it, and change its payload to
a
third byte sequence. Record the edited hash and current revision before switching or rebasing.
Revision arguments below stand for fixture revisions recorded in the transcript.

```sh
jj edit <first-revision>
git lfs checkout
# Edit asset.bin to a third payload.
jj status
jj edit <second-revision>
# In a separate fixture, replace the final edit with:
jj rebase -r @ -d <second-revision>
```

**Criterion:** If the disk edit is replaced, its bytes must remain recoverable in the inspected
prior
revision, or the operation must refuse. Inspect both disk and stored content after the operation.

**Observed:** PR switch and rebase exited 0 and replaced the edit with a pointer; the prior revision
still contained the old pointer. The rebase reported a conflict but did not preserve the edited
payload. Parent runs captured the raw edited bytes before the operation. This establishes a loss of
recoverability, not a correct parent LFS workflow. See [F01](FINDINGS.md#f01).

**Evidence:** [comparison](evidence/workflows-sol/v4/comparison.json) contains original IDs
`pr-switch`, `pr-rebase`, `base-switch`, and `base-rebase`;
[transcript](evidence/workflows-sol/v4/transcript.json) records full commands and revision IDs.

Earlier [exploratory probes](evidence/workflows-sol/v3) also exercised restore, squash, split,
conflicted attributes, and additional workspaces. Squash/split left edited payloads on disk without
recording them; restore of the tested empty child did not alter them. These bounded observations
are not safety passes for arbitrary checkout/conflict variants. The reduced comparisons above are
the basis of the finding.

Additional path-kind probes are in the [debug](evidence/transitions-sol/debug/comparison.json) and
[release](evidence/transitions-sol/release/comparison.json) comparisons, with original suffixes
`file_to_dir`, `dir_to_file`, and `file_to_symlink`. Each changes the path kind, runs status twice,
inspects the tree, restores the original kind, and runs status again. Release file-to-directory
processing completed, but restoring a filtered file did not retrack it; directory-to-file omitted
the replacement filtered file; file-to-symlink retained the old pointer. Their recovery-oriented
PASS labels do not certify that every intermediate tree represents the disk path kind. See
[A10](#a10-file-directory) and [A08](#a08-symlink-asset) for the specific failed expectations.

## X02-untrack-recipe

**Validate the documented procedure.** The proposed guidance suggests untracking existing LFS paths.
The criterion is that following that guidance must preserve the committed pointer.

**Setup:** A committed pointer with a hydrated disk file, under the LFS filter rule.

```sh
jj file list
jj file untrack asset.bin
jj status
jj file list
jj file show asset.bin
```

**Observed:** On the PR, untrack exited 0, status reported `D asset.bin`, the path disappeared from
the tree, and file-show exited 1. The hydrated file remained on disk. On the exact parent, untrack
refused because the path was not ignored. This is a bad documentation recipe, not a claim that
untrack should preserve tracked entries. See [F02](FINDINGS.md#f02).

**Evidence:** original IDs `pr-untrack` and `base-untrack` in the
[comparison](evidence/workflows-sol/v4/comparison.json) and
[transcript](evidence/workflows-sol/v4/transcript.json).

### F02 manual reproduction

Run the [shared manual setup](#manual-reproduction-setup) once, then this block in the same Bash
session. It was verified against the pinned macOS debug binary. These smaller fixtures confirm the
finding; they do not add core scenarios or constitute a Windows rerun.

```sh
new_case F02 || exit 1
jj file untrack asset.bin
printf 'untrack exit=%s\n' "$?"
jj status
jj file list
jj file show asset.bin
printf 'show exit=%s\n' "$?"
```

[Recorded output](evidence/manual-reproductions/F02.txt) · [Finding F02](FINDINGS.md#f02).

## X03-hosted-roundtrip

**Real GitHub publication.** Determine which parts of a usable LFS workflow require external Git
LFS.
Use the [disposable repository](https://github.com/joshka/jj-lfs-eval-20260925), small synthetic
payloads, and fresh clones to verify server-side state rather than trusting push exit codes.

The [command transcript](evidence/hosted/commands.txt) and
[repository checks](evidence/hosted/repository-state.json) cover these separate observations:

| Step | Operation and verification | Observed result |
| --- | --- | --- |
| Initial asset | Git/LFS upload, then independent clone | Payload hydrated correctly |
| Ordinary edit | `jj git push`, then independent clone | Ordinary edit and LFS pointer preserved |
| New pointer | `jj git push` before uploading its object | GitHub rejected with `GH008` |
| Recovery | `git lfs push --object-id`, retry jj push, clone | Both assets hydrated |
| Archive | Download GitHub source archive, inspect asset bytes | Pointers under default settings |
| Locking | `git lfs lock`, `locks`, `unlock` | API operations worked; test lock removed |

**Criterion:** A successful publication must survive an independent clone with correct payload
hashes; missing-object rejection must leave the remote ref unchanged. Both were verified. A total
of 7,168 payload bytes was uploaded. jj did not upload the new object itself.

**Limits:** A working lock API does not show that jj enforces another user's lock. The archive test
does not cover the repository setting that includes LFS objects. A preparation attempt with broad
filter opt-out also captured an unrelated hydrated file as raw bytes; do not copy that configuration
as a one-file publication recipe. These are observations of the tested handoff, not a complete safe
asset-edit procedure.

## X04-transport-failures

**External transfer errors and integrity.** A loopback server implements enough of the LFS batch
protocol to return controlled failures. Seed two pointers, empty the object cache, point Git LFS at
the local endpoint, and run `git lfs fetch` under a timeout. Then run `jj status`, inspect stored
and
disk pointers, and enumerate the cache.

**Criterion:** Git LFS fails; jj remains usable; no pointer changes or invalid cached objects
appear.
These are external Git LFS behavior checks, not tests of a native jj transfer client.

| Original case ID | Server response | Observed Git LFS diagnostic |
| --- | --- | --- |
| batch-401 | Batch HTTP 401 | Credentials unavailable; prompts disabled |
| batch-403 | Batch HTTP 403 | Mock forbidden batch response |
| batch-404 | Batch HTTP 404 | Mock missing batch response |
| batch-429 | Batch HTTP 429 | Rate-limit response, with retries |
| batch-500 | Batch HTTP 500 | Fatal batch response and log-file guidance |
| corrupt-data | Downloaded bytes mismatch object hash | Integrity verification failure |
| object-404 | HTTP 200 batch with per-object 404 | Missing-object diagnostic |

All seven fetches failed, all subsequent jj status calls exited 0, both pointers stayed unchanged,
and no cache files remained. The 429 probe made nine requests and took about 6.9 seconds. It
completed
under the guard despite retry configuration. This does not establish production retry behavior or
credential redaction: mock URLs contained no secrets.

**Evidence:** [summary](evidence/failures-sol/results/summary.json),
[per-case records](evidence/failures-sol/results), and
[server/runner](evidence/failures-sol/evaluate_failures.py.txt).

## X05-lifecycle

**Storage, pruning, and external migration.** These macOS probes use disposable local repositories,
a local bare remote where needed, and the PR debug binary. Original IDs are listed below; each links
to the command record. The aggregate PASS labels refer to the worker's individual checks, not a
blanket claim of lifecycle safety.

### custom-storage

Set `git config lfs.storage <absolute-shared-store>`, create the seed, run jj status and external
`git lfs checkout`. The object existed in the configured store, jj kept its pointer, and disk bytes
matched the payload after checkout. This tests an absolute custom path, not all shared-cache races.
[Evidence](evidence/lifecycle-sol/custom-storage.json).

### fetch-exclude

Set `git config lfs.fetchexclude other.bin` with both objects already local, then use external
checkout and jj status. Both stored pointers remained intact. No remote fetch-selection assertion
was made; this is configuration coexistence only.
[Evidence](evidence/lifecycle-sol/fetch-exclude.json).

### migrate-after

Run `git lfs migrate import '--include=*.bin' --yes` after jj initialization, followed by
`jj git import`. Migration exited 0; the recorded post-import stored hash was the pointer hash.
The original raw content was checked before migration. This was a one-asset fixture, not a test of
large rewritten stacks or remote collaborators.
[Evidence](evidence/lifecycle-sol/migrate-after.json).

### migrate-before

Run the same external import before `jj git init`. jj then read the converted pointer correctly.
The assertion compared stored bytes with the expected pointer.
[Evidence](evidence/lifecycle-sol/migrate-before.json).

### migrate-export-after

Run `git lfs migrate export '--include=*.bin' --yes`, then `jj git import`. Both exited 0; the jj
tree
changed from a pointer to the original raw payload. The byte comparisons passed.
[Evidence](evidence/lifecycle-sol/migrate-export-after.json).

### missing-lfs

Remove `git-lfs` from the fixture PATH, run jj status, switch to an empty revision and back to the
asset revision. jj commands succeeded and the disk file remained a pointer. This verifies that
snapshot/checkout does not require Git LFS; it does not establish automatic hydration.
[Evidence](evidence/lifecycle-sol/missing-lfs.json).

### prune-abandoned and prune-unbookmarked

Create a jj-only asset reference; in the second fixture abandon the change while retaining operation
history. Inspect refs, then run the following against each disposable fixture:

```sh
git lfs prune --dry-run --verbose
git lfs prune --recent --dry-run --verbose
git lfs prune --verify-remote --dry-run --verbose
git lfs prune --force --dry-run --verbose
git lfs prune --force --verbose
```

Ordinary/recent dry runs retained the tested object. Forced pruning removed it. Operation recovery
could restore the pointer but not recreate the deleted payload. The tests deliberately assert that
forced pruning can remove it; their PASS label is not evidence that forcing prune is safe. Normal
long-aged retention, every ref layout, and garbage collection were not established.
[Abandoned evidence](evidence/lifecycle-sol/prune-abandoned.json),
[unbookmarked evidence](evidence/lifecycle-sol/prune-unbookmarked.json).

### skip-smudge

Use skip-smudge configuration during external checkout, then inspect disk and jj stored bytes.
Both remained the expected pointer. This verifies an unhydrated working copy, not payload download.
[Evidence](evidence/lifecycle-sol/skip-smudge.json).

## X06-performance-config

**Release-profile measurement and diagnostics.** Each timing comparison uses the same fixture and
binary with filtering enabled versus disabled. Five alternating warm runs were recorded. PASS means
commands and content checks succeeded; no latency or memory acceptance threshold was defined.

| Original case ID | Fixture | Enabled median | Disabled median |
| --- | --- | ---: | ---: |
| bench-none | 3,000 ordinary files, empty attributes | 18.29 ms | 18.28 ms |
| bench-root-patterns | 3,000 files, 5,000 root patterns | 27.77 ms | 19.85 ms |
| bench-nested | 3,000 files, 60 nested attribute files | 30.00 ms | 30.88 ms |

Commands alternate `jj status` and `jj --config='git.ignore-filters=[]' status` after warmup.
The pattern-heavy fixture shows overhead in this sample. There is no cold-cache, peak-RSS,
network-filesystem, or multi-gigabyte result.

Three further original IDs:

- `large-64m`: run status with a 64 MiB hydrated asset; compare disk hashes and stored pointer.
  Disk bytes were unchanged, the stored pointer was 133 bytes, and status took 16.40 ms.
- `custom-filter`: configure `git.ignore-filters=["crypt"]`; status excluded a `crypt` path and
  included an `lfs` path, confirming selection by configured filter name.
- `debug-excluded`: create a filtered path; run `jj --debug status` and `jj file list`.
  The path was excluded. Debug stderr contained lock events, not the path or filter name.
  The worker PASS checked exclusion; missing explanatory logging supports [F06](FINDINGS.md#f06).

**Evidence:** [results and raw timings](evidence/performance-sol/results.json),
[per-case commands](evidence/performance-sol). These figures are recalculated from the retained JSON;
earlier README figures were inconsistent with it. No new benchmark was run for this document.

## X07-clone-hydration

**A developer clones with jj first.** In isolated configuration without repository-local LFS
installation, clone the hosted fixture and inspect the two asset files.

```sh
jj git clone <test-repository-url> <fresh-directory>
# Inside the fresh directory:
git lfs pull
git lfs install --local
git lfs pull
jj status
```

**Criterion:** Hydration requires matching payload bytes on disk and preserved stored pointers, not
merely a zero exit code. The initial jj clone produced pointers. The first pull downloaded objects
but returned 0 while saying LFS was not installed and skipping checkout. After local installation,
the second pull hydrated both assets. This demonstrates the missing setup step in this isolated
configuration; it does not claim every user's global configuration behaves identically.

**Evidence:** [initial commands](evidence/hosted-jj-clone/commands.json),
[installed result](evidence/hosted-jj-clone/installed-results.json).

## X08-rebase-main

**Integration check, not a fixed branch.** Duplicate the pinned change in an isolated jj checkout
and replay it onto `f1b29bced933e289096a9c98276153e29dd95674`, the main revision used for this
check.
Inspect conflict paths after the rebase.

**Criterion:** Identify whether a clean replay is possible; only a resolved and built result could
establish main compatibility. Conflicts were reported in `CHANGELOG.md` and `Cargo.lock`, with no
Rust source conflict reported. They were left unresolved. No post-rebase build/test was performed.

**Evidence:** [rebase operation output](evidence/verification/rebase-result.log),
[conflict paths](evidence/verification/rebase-conflicts.txt).

## X09-api-compatibility

**Public Rust API review.** Inspect the PR's public `TreeStateSettings` and `SnapshotError`
definitions
and compare the released v0.45.1 type shapes. This is source review, not a downstream compilation
test.

**Criterion:** Existing external struct literals and exhaustive matches should remain valid for a
source-compatible release. The new required `ignore_filters` field and new variant in the exhaustive
public error enum can break those callers. That supports a pre-1.0 minor-version boundary rather
than a patch release if these API changes ship. No downstream crate was compiled.

**Evidence:** [PR patch](evidence/pr.diff),
[released struct](evidence/verification/released-treestate-settings.txt),
[released enum](evidence/verification/released-snapshot-error.txt), and
[contract review](evidence/verification/contract-audit.md.txt).

## X10-upstream-tests

**Existing regression coverage and build configurations.** Run relevant existing suites against the
pinned source. Success means the suite exits 0 with the reported test counts, not that the
independent
compatibility expectations also pass.

| Suite | macOS distinct tests passed | Windows focused tests passed |
| --- | ---: | ---: |
| Attribute unit tests | 26 | 26 |
| Local/concurrent working copy | 97 | 5 |
| `jj run` | 40 | Part of two CLI cases below |
| Diff-edit | 11 | Part of two CLI cases below |

The Windows CLI filter selected two temporary-snapshot tests in total. Its 33 focused tests repeat
coverage and are not added to the 174 distinct macOS test count. Locked debug/release builds passed
on macOS; debug builds passed on Linux and Windows. The no-default-features jj-lib check passed on
macOS and Windows.

Representative focused commands:

```sh
cargo check --locked -p jj-lib --no-default-features
cargo test --locked -p jj-lib --lib gitattributes
cargo test --locked -p jj-lib --test runner gitattributes
cargo test --locked -p jj-cli --test runner gitattributes_filter_in_temp_snapshot
cargo build --locked -p jj-cli --bin jj
```

**Evidence:** [verification logs](evidence/verification), [Windows
gates](evidence/windows/README.md),
and [workflow](harness/workflow_windows.yml). The full repository suite, clippy, MSRV, downstream
compilation, and a Windows release build were not run.

## Manual reproduction setup

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
