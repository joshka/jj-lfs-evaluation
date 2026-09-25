# Git LFS evaluation plan and coverage

Target: [PR 9635][pr] at `d8a56d1a38cae110529ef8e67e72e3e2057ed3ca`.
This document records the plan actually used, its completion evidence, and the remaining matrix.
The [report](README.md) makes the merge recommendation; this plan defines what each result means.

## Evaluation contract

Two questions are independent:

1. Does configurable snapshot exclusion preserve correct repository state and working-copy safety?
1. Can a developer complete everyday LFS workflows using jj plus explicit Git LFS operations?

Automatic clean/smudge, transfer, and locking are not silently promoted into requirements for this
snapshot-only PR. However, unrecorded edits must not be overwritten without protection, explicit
commands must have intelligible outcomes, and the documented manual workflow must preserve pointers.

A passing command is insufficient. Every applicable scenario checks actual bytes, pointer identity,
path presence, tree content, exit codes, and messages. When recovery matters, inspect prior revisions
and external LFS objects, not just the final working copy.

## Test method

1. Pin source SHA, parent SHA, tool versions, build profile, and binary hashes.
1. Create an independent repository for each scenario. Seed real Git LFS objects and pointer blobs
   through Git LFS, except when deliberately constructing malformed or missing-object cases.
1. Isolate Git and jj configuration, disable signing, and keep remotes disposable. Use sequential
   version-control operations within each repository. Never change the user's existing projects.
1. Establish the initial tree and disk hashes before the operation under test.
1. Execute the scenario; retain arguments, exit code, stdout/stderr, elapsed time, and byte hashes.
1. Inspect repository content without inadvertently taking an extra snapshot when snapshot ordering
   is the subject of the test. The attributes-removal case uses `--ignore-working-copy` for this.
1. Compare significant regressions with the exact parent. Label the installed Homebrew comparison
   used in calibration as preliminary, not a substitute for that parent comparison.
1. Repeat profile-sensitive and platform-sensitive findings. Retain setup errors and fix the harness
   separately; do not silently turn a setup error into a product pass.
1. Reduce confirmed findings and identify the missing upstream regression test. Do not fix the PR.

The core runner writes `environment.json`, per-case command records, and `results.json`.
`PASS` means the stated expectation held; `FAIL` identifies a gap against that expectation;
`ERROR` means a command/setup exception needs interpretation. `OBSERVED` can include an explicitly
skipped platform probe. The consolidated CSV normalizes that skipped probe to `SKIP`.

Product findings intentionally do not make the core harness process fail; setup errors do. Consumers
must inspect the JSON, not use a green CI job as a claim that every scenario passed. The current
Windows workflow preserves artifacts for that inspection.

## Executed core matrix

All rows below are expanded into individual cases in [scenario-matrix.csv](scenario-matrix.csv).
The macOS release and modern Linux runs each attempted all 40 cases.

| Group | Scenario IDs | Expected property |
| --- | --- | --- |
| Repeated snapshots | S01 | Hydrated bytes and stored pointer survive ordinary work |
| Excluded mutations | S02 variants | Characterize modify, delete, rename, and new-file exclusion |
| Pattern semantics | A01 variants | Git-compatible behavior for the supported attribute sources |
| Other attribute sources | A02, A03 | Identify local/global attribute coverage gaps |
| Attribute transitions | A04, A05, A06 | Stable snapshots and explicit LFS/ordinary transitions |
| Symlinks and traversal | A07, A08, A09 | Correct path types and ignored-directory traversal |
| Path-kind transition | A10 | File-to-directory change does not violate internal state |
| Configuration | C01, C03 | Explicit disable works; invalid types fail helpfully |
| Explicit tracking | C02 | Tracking either succeeds or explains its exclusion |
| Pointer states | P01, P02, P03 | Literal, malformed-looking, and empty content are preserved |
| Missing object | P04 | Failure leaves pointer intact; restored object hydrates |
| Sparse checkout | W01, W02 | Rehydration works; dirty content remains recoverable |
| Additional workspace | W03 | Correct Git context, hydration, and stored pointer |
| Auxiliary snapshots | W04 | `jj run` captures ordinary edits but preserves pointers |
| Filesystem diagnostics | D01, D02 | Read errors are actionable; executable-bit behavior is known |
| Snapshot overhead | N01 | Paired warm timings with filtering enabled and disabled |

A01 expands into nested unset/set overrides, root macros, unspecified state, last-rule precedence,
quoted spaces, Unicode, directory-only rules, recursive patterns, case-sensitive matching,
boolean filter state, and subdirectory-relative patterns.

S02 tests intentionally characterize exclusion, not full edit/delete/rename support. Their passing
status must be read together with F01 and the publication workflow: jj does not record those asset
changes merely because it safely ignores the hydrated bytes during that particular snapshot.

## Executed supplementary investigations

### Working-copy operations

Independent worker probes exercised revision switch, rebase, explicit restore, squash, split,
untrack, a conflicted attributes scenario, and hydration in an additional workspace. Switch, rebase,
and untrack were repeated against the exact parent. Read
[evidence/workflows-sol/v4/comparison.json](evidence/workflows-sol/v4/comparison.json) for the
strongest regression comparisons; the broader exploratory run is retained under `v3`.

Squash/split left edited bytes on disk without recording them in the PR fixture. Explicit restore
of an empty child did not change the excluded bytes. These observations are not proof of safety for
all conflict or checkout variants. The dangerous boundary is a later operation that replaces them.

File-to-directory, directory-to-file, and file-to-symlink changes were tested in debug and release
builds, including repeated snapshots and manual restoration. These tests distinguished a debug
assertion from an actual release crash.

### Lifecycle and interoperability

Nine lifecycle scenarios covered:

- Unbookmarked changes and abandoned changes under ordinary, recent, and forced pruning.
- Operation recovery after forced pruning of an LFS payload.
- Absolute shared/custom storage and skip-smudge state.
- jj snapshot/checkout when `git-lfs` is absent from PATH.
- Stored-pointer behavior with fetch exclusion configured and objects already local.
- Git LFS migration import before jj, import after jj, and export after jj.

Fetch selection was not validated against a remote in that lifecycle probe. Forced pruning is
explicitly dangerous; classify it against the [prune manual][prune], not as a default-prune bug.
Migration checks follow the external workflow described by the [migration manual][migrate].

### GitHub end-to-end workflows

The test repository exercised initial Git/LFS upload, independent Git clones, ordinary jj
publication, missing-object rejection, explicit object-upload recovery, default source archive
content, and lock/list/unlock. A separate direct jj clone verified the install/pull hydration journey.
Only small payloads were uploaded.

The source-archive result is about GitHub's default repository setting. It does not establish support
for every combination described by the [archive documentation][archives]. A successful lock API call
is not evidence that jj checks another user's lock before publication.

### External transport failures

A loopback-only server provided batch HTTP 401, 403, 404, 429, and 500; HTTP 200 with per-object 404;
and a download with corrupt bytes. The [batch protocol][batch] motivates distinguishing HTTP success
from per-object success. These checks used bounded subprocess timeouts and no real credentials.

Assertions covered unchanged pointers on disk and in jj, empty/correct object cache state, failure
exit codes, and useful Git LFS diagnostics. They do not test a jj LFS transfer client, which this PR
does not provide.

### Performance and configuration

The release build was used for a 64 MiB deterministic asset; 3,000-file repositories with empty,
5,000-pattern, and 60-directory attribute layouts; debug output for an excluded path; and a custom
`crypt` filter selection. The core sweep also measured a 120-directory layout.

Use the paired raw timings, not cross-repository absolute times, to discuss overhead. No peak-RSS
claim or production-scale latency guarantee is supported by this sample.

## Corrections made to the evaluation

These corrections changed the test interpretation or harness, not the implementation:

- The initial workspace expectation copied the documentation's missing-`.git` limitation. Live
  inspection showed a `.git` file for colocated additional workspaces. The corrected scenario checks
  successful external hydration and pointer preservation. This exposed documentation drift.
- The first sparse assertion treated removal from disk as failure even when the parent stored the
  edited bytes. The corrected assertion checks recoverability. The parent passes; the PR fails.
- The initial A10 command exception was recorded as `ERROR`. After inspecting its panic, it became
  an explicit product `FAIL` with captured return code. Release testing narrowed the crash claim.
- The core performance fixture text initially said “debug binary” even in the release run. The binary
  path/hash and build provenance were correct; the reusable script now says “same binary.”
- Luna's initial local-attribute probe also matched a root rule. The parent caught that confound and
  required a path matching only `.git/info/attributes`. The earlier evidence remains available.
- The first Docker command's login shell could not find cargo. It was corrected without a source
  change. The first Linux Git version was too old for colocated workspace creation, prompting the
  modern Git run rather than interpreting that environment error as an LFS regression.

## Remaining scenarios and their priority

The completed report identifies concrete blockers; it does not claim exhaustive coverage. These
scenarios remain explicit follow-up work rather than implicit passes.

### Required when validating a proposed fix

1. F01 across checkout, edit, rebase, sparse changes, undo, and workspace updates, including dirty
   hydrated bytes, literal pointers, unchanged hydrated bytes, and missing local objects.
1. Attribute deletion/rename and simultaneous content edits, with tree equality after repeated
   snapshots. Include the attribute file itself being filtered or becoming a directory.
1. Symlink and file/directory transitions under both profiles, followed by checkout and recovery.
1. Explicit file tracking/untracking instructions, verifying exported pointer trees before push.
1. Windows path handling, CRLF, case-only renames, and read-only assets on the corrected head.
1. Rebase onto current main, resolve its integration conflicts, then repeat these critical scenarios.

### High-value expansion before broader everyday-use claims

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

### Hosting and release scope

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

## Reproduction

Use a fresh output directory; the core harness intentionally refuses to overwrite existing fixtures.
Build the pinned PR first, then pass its binary path:

```sh
python3 harness/evaluate.py \
  --jj /path/to/pinned/jj \
  --out /tmp/jj-lfs-repeat-unique \
  --only S01,A04,A08,A10,C02,W02
```

Run this from the repository root. Omit `--only` for all 40 scenarios. Prerequisites are
Python 3, Git, Git LFS, and the selected jj binary. Scenarios create their own local signing/config
settings. They intentionally mutate or remove only files inside their disposable output fixtures.

For Linux, the tested runner used a binary built in a Rust/bookworm container and ran it in an Ubuntu
26.04 container with current Git/LFS. The initial and modern versions are recorded in their
`environment.json` files. Rebuild from the pinned source for other architectures.

The hosted worker report records its manual commands. Do not rerun publication probes against an
unrelated repository. Historical worker scripts are archived as `.py.txt` and depend on the original
fixture layout.

## Reference basis

Documentation was reviewed as of this evaluation. Git/LFS versions matter: in particular, current
[LFS pull][pull] and [checkout][checkout] documentation describes index/attribute behavior that
changes with Git version. Tests record those versions rather than treating Git as a timeless oracle.

- [Git attributes][attributes]: matching, precedence, macros, and path-type expectations.
- [LFS pointer specification][spec]: pointers, clean/smudge, and pre-push handoff.
- [LFS pull][pull] and [checkout][checkout]: hydration and missing-object behavior.
- [LFS configuration][config]: storage, remotes, include/exclude, and lock verification.
- [LFS prune][prune] and [migration][migrate]: lifecycle operations and limits of recovery.
- [LFS batch API][batch]: request errors versus per-object errors and object verification.
- [GitHub upload failures][upload]: missing-object diagnostics and recovery.
- [GitHub archive behavior][archives]: pointer versus payload archive content.
- [GitHub LFS billing][billing]: reason to keep hosted payloads small and avoid quota exhaustion.
- [Previous review concerns][old-concern] and [prior regression fixes][prior-fixes].

[pr]: https://github.com/jj-vcs/jj/pull/9635
[attributes]: https://git-scm.com/docs/gitattributes
[spec]: https://github.com/git-lfs/git-lfs/blob/main/docs/spec.md
[pull]: https://github.com/git-lfs/git-lfs/blob/main/docs/man/git-lfs-pull.adoc
[checkout]: https://github.com/git-lfs/git-lfs/blob/main/docs/man/git-lfs-checkout.adoc
[config]: https://github.com/git-lfs/git-lfs/blob/main/docs/man/git-lfs-config.adoc
[prune]: https://github.com/git-lfs/git-lfs/blob/main/docs/man/git-lfs-prune.adoc
[migrate]: https://github.com/git-lfs/git-lfs/blob/main/docs/man/git-lfs-migrate.adoc
[batch]: https://github.com/git-lfs/git-lfs/blob/main/docs/api/batch.md
[upload]: https://docs.github.com/en/repositories/working-with-files/managing-large-files/resolving-git-large-file-storage-upload-failures
[archives]: https://docs.github.com/en/repositories/managing-your-repositorys-settings-and-features/managing-repository-settings/managing-git-lfs-objects-in-archives-of-your-repository
[billing]: https://docs.github.com/en/billing/concepts/product-billing/git-lfs
[old-concern]: https://github.com/jj-vcs/jj/pull/9068#issuecomment-4099481480
[prior-fixes]: https://github.com/jj-vcs/jj/pull/9676
