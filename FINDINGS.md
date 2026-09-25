# Findings

**Do not merge the pinned head unchanged.** Edited hydrated assets can be lost during checkout, and
the documented untrack recipe removes committed pointers. These are the two highest-priority issues.
The PR does preserve pointers during ordinary snapshots; that narrower behavior works.

Target: [PR 9635](https://github.com/jj-vcs/jj/pull/9635), `d8a56d1a38ca`. Exact-parent comparisons
use `e9f48b3e4c1c`. No implementation fixes were made. Case links below provide setup, rationale,
acceptance criteria, full commands, and raw evidence. [Methodology](METHODOLOGY.md) records provenance.

The command excerpts below show each trigger after the stated setup. Full fixture scripts and
verification commands are linked by case ID. Suggested fixes are proposals, not validated changes.

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

**When:**

```sh
jj sparse set --clear --add note.txt
jj --ignore-working-copy file show assets/asset.bin
```

**Actual:** Exit 0; the disk file is deleted; file-show returns the old pointer. The edited bytes
are absent from both disk and the inspected tree.

**Expected:** Refuse to remove the edited file, keep it on disk, or save its edited bytes before
removal.

**Suggested fix:** Detect unrecorded edits before overwriting or removing excluded files; preserve
them or refuse with an actionable error. Cover checkout, rebase, and sparse removal.

**Scope:** PR regression: the exact parent saves the raw edit before checkout. Separate
switch/rebase cases also lose edits on the PR.

**Cases:** [W02-sparse-dirty](TEST-CASES.md#w02-sparse-dirty) ·
[X01-checkout-rebase](TEST-CASES.md#x01-checkout-rebase).

[Full reproduction and recorded output](TEST-CASES.md#f01-manual-reproduction).

### F02

**P1 — The documented untrack step deletes the pointer.**

**Setup:** An existing committed LFS pointer and hydrated `asset.bin`; follow the proposed untrack
guidance.

**When:**

```sh
jj file untrack asset.bin
jj status
jj file list
jj file show asset.bin
```

**Actual:** Untrack exits 0. Status reports `D asset.bin`; file-list omits it; file-show exits 1.
The disk payload remains.

**Expected:** Following the LFS setup instructions keeps the asset in the revision.

**Suggested fix:** Remove the untrack step. Existing tracked LFS files are already excluded. Replace
it with a tested pointer-preserving update procedure.

**Scope:** Documentation defect; untrack is behaving as requested. The parent refuses the operation
because the path is not ignored.

**Cases:** [X02-untrack-recipe](TEST-CASES.md#x02-untrack-recipe).

[Full reproduction and recorded output](TEST-CASES.md#f02-manual-reproduction).

### F03

**P2 — Replacing an asset file with a directory crashes debug builds.**

**Setup:** With `*.bin filter=lfs`, replace disk file `asset.bin` with directory
`asset.bin/child.txt`.

**When:**

```sh
jj status
```

**Actual:** Debug status exits 101 with `assertion left == right failed` at
`local_working_copy.rs:1464`. Cached file states contain the old file and child; the tree contains
only the child.

**Expected:** Exit 0 and represent the file-to-directory change consistently.

**Suggested fix:** Remove or update stale file-state entries during path-kind transitions. Test
repeated snapshots and the next checkout.

**Scope:** Reproduces on macOS, Linux, and Windows debug. The parent succeeds. macOS release
succeeds; no release crash was demonstrated.

**Cases:** [A10-file-directory](TEST-CASES.md#a10-file-directory) · [X01 path-kind
probes](TEST-CASES.md#x01-checkout-rebase).

[Full reproduction and recorded output](TEST-CASES.md#f03-manual-reproduction).

### F04

**P2 — A second status changes stored asset content without another edit.**

**Setup:** Delete `.gitattributes` while `asset.bin` is hydrated. Make no further disk changes.

**When:**

```sh
jj status
jj --ignore-working-copy file show asset.bin
jj status
jj --ignore-working-copy file show asset.bin
```

**Actual:** The first returns the LFS pointer. The second returns the raw payload. A third snapshot
is stable.

**Expected:** Both inspections return the same stored bytes once the first snapshot has processed
the deletion.

**Suggested fix:** Apply deletion of attribute rules consistently in the first snapshot. Test that a
second snapshot without disk edits changes nothing.

**Scope:** Reproduces on all tested configurations. The parent does not show the two-step
transition. The intended attribute-deletion policy still needs a decision.

**Cases:** [A04-removed](TEST-CASES.md#a04-removed) · [Parent
comparison](evidence/base-comparison/A04-removed.json).

[Full reproduction and recorded output](TEST-CASES.md#f04-manual-reproduction).

### F05

**P2 — A matching symlink disappears from the jj tree.**

**Setup:** Under `*.bin filter=lfs`, create `link.bin` as a symlink to ordinary `note.txt`.

**When:**

```sh
git add link.bin
git ls-files --stage link.bin
jj status
jj file list
```

**Actual:** Git records mode `120000`. jj file-list omits `link.bin`.

**Expected:** Keep `link.bin` as a symlink entry, as Git does.

**Suggested fix:** Do not exclude symlink entries solely because their names match an LFS pattern.
Test new symlinks and file-to-symlink transitions.

**Scope:** Reproduces on macOS and Linux; the parent tracks the symlink. Windows symlink tests were
skipped.

**Cases:** [A08-symlink-asset](TEST-CASES.md#a08-symlink-asset) · [X01 path-kind
probes](TEST-CASES.md#x01-checkout-rebase).

[Full reproduction and recorded output](TEST-CASES.md#f05-manual-reproduction).

### F06

**P2 — Track says success but does not track the file.**

**Setup:** Create a new `new.bin` that matches `filter=lfs`.

**When:**

```sh
jj file track new.bin
jj file list
```

**Actual:** Track exits 0 with empty stderr. File-list does not contain `new.bin`.

**Expected:** Track the path, return a failure, or explain why it remains excluded.

**Suggested fix:** Explain why the explicit track request is excluded and how to proceed. Add debug
tracing for exclusion decisions.

**Scope:** Reproduces on all tested configurations. A separate debug-status probe also omitted the
excluded path and filter.

**Cases:** [C02-force-track](TEST-CASES.md#c02-force-track) · [X06 diagnostic
probe](TEST-CASES.md#x06-performance-config).

[Full reproduction and recorded output](TEST-CASES.md#f06-manual-reproduction).

### F07

**Compatibility gap — Git identifies LFS content that jj stores raw.**

**Setup:** Put `a.bin filter=lfs` only in `.git/info/attributes`; repeat separately with
`core.attributesFile`. No repository rule matches.

**When:**

```sh
git check-attr filter -- a.bin
jj status
jj file list
jj file show a.bin
```

**Actual:** Git reports `a.bin: filter: lfs`. jj adds `a.bin` and stores its raw payload.

**Expected:** For full Git-attribute compatibility, exclude the file that Git identifies as
LFS-managed.

**Suggested fix:** Document that only repository attribute files are supported, or implement the
other sources with Git precedence. Keep tests for the chosen boundary.

**Scope:** Compatibility limitation, not an established regression. Deferral is reasonable if the
scope is explicit.

**Cases:** [A02-info-attributes](TEST-CASES.md#a02-info-attributes) ·
[A03-global-attributes](TEST-CASES.md#a03-global-attributes).

[Full reproduction and recorded output](TEST-CASES.md#f07-manual-reproduction).

### F08

**Documentation — The workspace limitation is too broad.**

**Setup:** Create an additional colocated workspace from the LFS fixture. The first command runs in
the original workspace; the others run in the new workspace.

**When:**

```sh
jj workspace add /path/to/additional-workspace
# In the additional workspace:
git lfs checkout
jj status
jj file show asset.bin
```

**Actual:** The new workspace has a `.git` file. External checkout hydrates the asset and jj keeps
its pointer. The documented claim that jj workspaces lack Git context is too broad.

**Expected:** Documentation describes the Git context and external hydration supported by the tested
layout.

**Suggested fix:** Qualify the workspace limitation by layout. Also update stale source
descriptions: symlinked attributes are not followed, and rules are loaded lazily.

**Scope:** Verified for additional colocated workspaces. Non-colocated support was not established;
lazy loading is a source-review observation.

**Cases:** [W03-workspace](TEST-CASES.md#w03-workspace) ·
[A07-symlink-attrs](TEST-CASES.md#a07-symlink-attrs).

[Full reproduction and recorded output](TEST-CASES.md#f08-manual-reproduction).

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
