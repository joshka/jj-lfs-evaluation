# Findings

**Do not merge the pinned head unchanged.** Edited hydrated assets can be lost during checkout, and
the documented untrack recipe removes committed pointers. These are the two highest-priority issues.
The PR does preserve pointers during ordinary snapshots; that narrower behavior works.

Target: [PR 9635](https://github.com/jj-vcs/jj/pull/9635), `d8a56d1a38ca`. Exact-parent comparisons
use
`e9f48b3e4c1c`. No implementation fixes were made. Case links below provide setup, rationale,
acceptance criteria, full commands, and raw evidence. [Methodology](METHODOLOGY.md) records
provenance.

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

**P1 — Checkout loses unrecorded asset edits. PR regression.**

After editing a hydrated asset, `jj status` keeps its old pointer. `jj edit` to a different asset
revision exits 0 and replaces the edited bytes; the inspected prior revision contains only the old
pointer. Rebase has the same loss, even though it reports a conflict. Sparse exclusion also exits 0
and removes the edited file. The exact parent stores the raw edit before checkout, making it
recoverable. That violates LFS pointer semantics but establishes the regression in recoverability.

Require preservation or a clear refusal before overwriting excluded edits.
[Checkout/rebase case and comparison](TEST-CASES.md#x01-checkout-rebase) ·
[Sparse case, including release and Windows](TEST-CASES.md#w02-sparse-dirty).

### F02

**P1 — The documented untrack recipe removes a committed pointer. Documentation defect.**

With an existing pointer and hydrated file, `jj file untrack asset.bin` exits 0; status reports
`D asset.bin`; file-show exits 1. The disk payload remains, but the revision records a deletion.
Untrack is doing its job. The advice to use it for LFS is wrong: existing tracked assets are already
excluded from snapshots. The exact parent refuses this untrack because the path is not ignored.

Replace the recipe with a tested pointer-preserving procedure.
[Procedure, commands, and comparison](TEST-CASES.md#x02-untrack-recipe).

### F03

**P2 — File-to-directory replacement breaks a snapshot invariant. PR regression.**

Replace `asset.bin` with `asset.bin/child.txt` under `*.bin filter=lfs`, then run `jj status`.
macOS, Linux, and Windows debug builds exit 101 at `local_working_copy.rs:1464`: cached paths
include
both the old file and child; the tree contains only the child. The exact parent handles the change.
The macOS release command succeeds. **A release crash was not demonstrated.**

Repair the invariant and test subsequent snapshots and checkout, not just the first command.
[Case and profile-specific evidence](TEST-CASES.md#a10-file-directory).

### F04

**P2 — Deleting attributes produces a second content change without a disk edit.**

Delete `.gitattributes`, then run status twice. The first snapshot retains the asset pointer; the
second stores raw payload. A third is stable. The parent does not exhibit that transition. Reading
through `--ignore-working-copy` confirms the difference without triggering extra snapshots.
The revision's contents therefore depend on how many commands have snapshotted it.

Settle deletion semantics and test successive snapshots.
[Case](TEST-CASES.md#a04-removed) · [Parent comparison](evidence/base-comparison/A04-removed.json).

### F05

**P2 — An LFS pattern hides a symlink that Git tracks.**

Create `link.bin` under `*.bin filter=lfs`. Git stages a mode-120000 symlink; jj omits it.
The parent tracks it. A separate file-to-symlink probe leaves the old pointer stored while the disk
path is a symlink. This is distinct from symlinked `.gitattributes`, which is correctly not
followed.
Windows symlink probes were skipped.

[Symlink case](TEST-CASES.md#a08-symlink-asset) ·
[Path-kind probes](TEST-CASES.md#x01-checkout-rebase).

### F06

**P2 — Explicit track reports success without tracking or explanation.**

`jj file track new.bin` exits 0 with empty stderr, but file-list omits the filtered path.
A separate `jj --debug status` shows lock events, not the excluded path or filter. Explicit requests
need an actionable outcome; routine status need not warn for every hydrated asset.
[Tracking case](TEST-CASES.md#c02-force-track) · [Logging probe](TEST-CASES.md#x06-performance-config).

### F07

**Compatibility limit — Info and global attributes are not read.**

With an LFS rule only in `.git/info/attributes` or `core.attributesFile`, Git reports `filter=lfs`
but jj adds the raw payload. The implementation reads repository `.gitattributes`. This is not an
established regression; deferral is reasonable if the support boundary is explicit.
[Info-attribute case](TEST-CASES.md#a02-info-attributes) ·
[Global-attribute case](TEST-CASES.md#a03-global-attributes).

### F08

**Documentation — Workspace and attribute descriptions are stale.**

The tested colocated additional workspace has a `.git` file and supports `git lfs checkout`,
contrary to the broad documented limitation. Qualify that advice by layout. The PR description also
says symlinked attribute files are followed and all rules are parsed every snapshot; current code
rejects those symlinks and loads visited rules lazily.
[Workspace case](TEST-CASES.md#w03-workspace) · [Symlinked-rule case](TEST-CASES.md#a07-symlink-attrs).

## What worked

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
