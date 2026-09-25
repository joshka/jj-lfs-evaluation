# Remaining coverage

The [findings](FINDINGS.md) identify concrete blockers; it does not claim exhaustive coverage. These
scenarios remain explicit follow-up work rather than implicit passes.

## Required when validating a proposed fix

1. F01 across checkout, edit, rebase, sparse changes, undo, and workspace updates, including dirty
   hydrated bytes, literal pointers, unchanged hydrated bytes, and missing local objects.
1. Attribute deletion/rename and simultaneous content edits, with tree equality after repeated
   snapshots. Include the attribute file itself being filtered or becoming a directory.
1. Symlink and file/directory transitions under both profiles, followed by checkout and recovery.
1. Explicit file tracking/untracking instructions, verifying exported pointer trees before push.
1. Windows path handling, CRLF, case-only renames, and read-only assets on the corrected head.
1. Rebase onto current main, resolve its integration conflicts, then repeat these critical scenarios.

## High-value expansion before broader everyday-use claims

- Watchman/fsmonitor invalidation when only an attribute file or filter configuration changes.
- Long-aged jj-only commits, remote verification during pruning, shared caches, and aggressive GC.
- Two-user locking: owned/foreign locks, verification failure, writable/read-only transitions,
  and jj publication bypass of Git hook safeguards.
- Dirty payload preservation during failed refresh, partial transfer success, cancellation, disk
  exhaustion, and permission failure in the LFS object store. Do not fill the user's real disk.
- Remote include/exclude hydration, changed `.lfsconfig`, alternate fetch/push endpoints, SSH/HTTPS
  credential differences, custom transfer agents, and expired URLs.
- Pointer format boundaries at 1,024 bytes, legacy version URLs, extra/unknown fields, extensions,
  malicious sizes, and canonicalization when data enters through external Git LFS.
- Attributes from sparse/unavailable directories, conflicted attributes with different policies,
  imported shallow history, and partial-clone/promisor interactions.
- Cold-cache and large-tree performance, adversarial pattern counts, deep paths, memory use,
  network filesystems, and multi-gigabyte payloads.

## Hosting and release scope

- GitHub archive setting enabled for LFS inclusion, external LFS endpoints, forks, protected refs,
  concurrent pushes, and a server that does not enforce missing-object integrity.
- Actual quota exhaustion, purchase/overage behavior, and hosted rate-limit timing were deliberately
  not induced. Mock rejection covers only the failure boundary, not GitHub accounting.
- Full repository tests, clippy, MSRV, downstream library consumers, and the broader feature matrix.
- Windows debug CI completed: 33 focused upstream tests passed. The core sweep has 30 audited
  passes, six gaps, and four skips. Two original failures were path-separator assertion errors,
  corrected by inspecting command evidence; the Windows sweep was not rerun. See
  [Windows evidence](evidence/windows/README.md). ACL/read-only, CRLF conversion, case-only rename,
  Windows symlink behavior, and release-profile coverage remain open.
