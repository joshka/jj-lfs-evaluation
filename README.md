# jj Git LFS readiness evaluation

Evaluation date: 25 September 2026. Target: [PR 9635][pr], commit
`d8a56d1a38cae110529ef8e67e72e3e2057ed3ca`. No implementation fixes were made.

**Recommendation: do not merge the pinned head unchanged.** Its core snapshot exclusion works,
including real GitHub round trips, but checkout and rebase can silently destroy edited hydrated
assets that jj has stopped recording. The documentation also recommends an operation that deletes
committed pointers. These need attention before the change becomes the default for LFS repositories.

This is a useful partial integration, not native LFS transport. Native clean/smudge, automatic
uploads, and every advanced LFS feature need not be implemented to merge it. Safe handling of
unrecorded working-copy bytes and accurate instructions do need a clear contract.

**Semver: breaking for `jj-lib` consumers.** The PR adds a required public
`TreeStateSettings.ignore_filters` field and a variant to the public, exhaustive `SnapshotError`
enum. Existing external struct literals and exhaustive matches can stop compiling. A pre-1.0 minor
release, such as 0.46.0 from 0.45.x, is the appropriate increment rather than a patch release.
The public type shapes were also checked against released v0.45.1. No downstream crate
compilation was performed. The CLI also
changes default behavior for matching paths. Integrate that assessment with the actual release train.

## Deliverables

- [Test plan and remaining coverage](test-plan.md).
- [Core scenario matrix](scenario-matrix.csv): every core scenario, by platform/profile.
- [Model calibration and delegation assessment](model-calibration.md).
- [Reusable core harness](harness/evaluate.py).
- [Pinned PR metadata](evidence/pr.json) and [patch](evidence/pr.diff).
- [Release results](evidence/macos-release/results.json) and
  [Linux results](evidence/linux-modern/results.json).

This repository is the publication copy. Logs and historical scripts are sanitized;
see [publication notes](PUBLICATION.md) for transformations and scan results.
The original evidence and disposable repositories are retained locally by the evaluator.
The supported runnable interface is [the core harness](harness/evaluate.py). Historical worker
scripts are archived as `.py.txt` evidence and require adaptation before reuse.

## Evidence and scope

The exact parent, `e9f48b3e4c1c5e816fbbfbfd06c154a6a96b0215`, was built for regression comparisons.
A standard release build and a debug build were made from the PR. Source archives were checked after
execution: all 710 original files were unchanged. Generated build artifacts are additional files.
See [source integrity](evidence/verification/source-integrity.json).

The core sweep contains **40 distinct scenarios**, repeated across these environments:

| Environment | Met expectation | Gap | Setup error | Skipped |
| --- | ---: | ---: | ---: | ---: |
| macOS, PR release | 34 | 6 | 0 | 0 |
| macOS, PR debug, corrected checks | 33 | 7 | 0 | 0 |
| Linux, modern Git, PR debug | 32 | 7 | 0 | 1 |

A gap is not automatically a merge blocker. Some expectations intentionally ask for fuller Git
compatibility than the PR implements. The finding dispositions below provide that distinction.
The Linux skip is the Unix permission probe: its container ran as root. macOS exercised that probe.
Initial harness mistakes and corrected assertions are retained rather than hidden; see the plan.

Additional independent probes cover six workflow types, three path-kind transitions, nine lifecycle
scenarios, seven controlled transport failures, seven hosted transport/locking/archive checks, six
performance/configuration probes, and a direct jj-clone/hydration journey. These overlap with the core
sweep; their counts must not be summed as independent coverage or a statistical pass rate.

Versions:

- macOS arm64: Git 2.55.0, Git LFS 3.8.0, Rust 1.98.1; PR and parent report jj 0.45.1.
- Linux arm64, Ubuntu 26.04 container: Git 2.53.0, Git LFS 3.7.1, Python 3.14.4.
- An initial Debian/bookworm run used Git 2.39.5 and Git LFS 3.3.0. Additional colocated workspace
  creation failed with an explicit Git >= 2.42 requirement. The modern-container run removed that
  environment limitation. Both runs are retained.
- Windows: the initial attempt did not execute because a runner was unavailable. A follow-up on
  [the now-public test repository][windows-run] is in progress; its results will be added.

## Findings to address before merging

### F01: Checkout, rebase, and sparse removal can lose edited assets

**Priority: P1. Recommendation: merge blocker. Responsibility: regression introduced by exclusion.**

Start with committed LFS pointers for two asset versions. Hydrate the first, edit its payload, run
`jj status`, then switch to the second revision. The PR reports a clean asset, keeps the original
pointer in the prior revision, and successfully replaces the edited bytes with the second pointer.
The edited bytes are no longer on disk or in the jj revision inspected by the reproduction.
A rebase that changes the asset has the same destructive consequence. Removing a dirty asset from
sparse patterns also deletes its only working-copy copy without storing the edit.

The exact parent snapshots the modified raw bytes before changing the checkout, leaving them
recoverable. That breaks LFS pointer semantics, so it is not a good solution, but it proves that the
PR changes recoverability. Intentional snapshot exclusion explains the omission; it does not make
subsequent silent overwriting safe.

Evidence:

- [Exact-parent workflow comparison](evidence/workflows-sol/v4/comparison.json).
- [Exact-parent command transcript](evidence/workflows-sol/v4/transcript.json).
- [Release sparse-loss case](evidence/macos-release/W02-sparse-dirty.json).
- [Parent sparse recovery](evidence/base-sparse-recheck/W02-sparse-dirty.json).

Required regression coverage should assert preservation or a clear refusal on revision switch,
rebase, sparse exclusion, and other checkout paths when disk content contains an unrecorded edit.
Do not merely assert that the pointer stays unchanged. The policy can remain snapshot-only, but it
needs a safe boundary for overwriting external content.

### F02: The documented untrack workaround deletes committed pointers

**Priority: P1 documentation defect. Recommendation: correct before merge.**

The Git compatibility documentation says existing tracked LFS paths may need `jj file untrack`.
On the pinned head, a committed LFS pointer is already excluded from snapshot updates.
`jj file untrack asset.bin` succeeds, removes that pointer from the current revision, and reports
`D asset.bin`. Hydrated bytes remain on disk. Publishing that revision would publish a deletion.
The exact parent refuses because the path is not ignored.

This is not evidence that `untrack` itself should preserve tracked content: removing a path is its
purpose. The defect is prescribing that destructive operation as a prerequisite for LFS exclusion.
See [the exact-parent comparison](evidence/workflows-sol/v4/comparison.json) and
[the pinned documentation][compat-source].

Replace that guidance with a tested workflow that verifies pointer preservation and explains how
asset updates enter Git history through external Git LFS tooling. Test the instructions end to end.

### F03: File-to-directory transitions violate working-copy state invariants

**Priority: P2. Recommendation: fix before merge. Responsibility: PR regression.**

Replace tracked `asset.bin` with `asset.bin/child.txt`, keeping `*.bin filter=lfs`.
The debug build panics on repeated `jj status` calls at `local_working_copy.rs:1464`, exit 101.
Its cached file-state paths contain both the old file and the child; the tree contains only the child.
The exact parent processes the transition.

The standard release build completes this transition and can recover when the original path is
restored. **A release crash was not demonstrated.** The debug assertion still exposes a real
bookkeeping invariant violation, not an ordinary rejected operation.

See [debug evidence](evidence/transitions-sol/debug/comparison.json),
[release evidence](evidence/transitions-sol/release/comparison.json), and
[the core reproduction](evidence/macos-recheck/A10-file-directory.json).
Test both directions of path-kind changes and subsequent snapshots/checkouts.

### F04: Removing attributes produces two different snapshots without further edits

**Priority: P2. Recommendation: resolve before merge or explicitly settle the intended contract.**

Delete `.gitattributes` while a tracked asset is hydrated. The first `jj status` records only the
attribute deletion and retains the old pointer. The next status, with no disk changes, replaces the
pointer with raw payload bytes. A third is stable. Disk-first lookup falls back to the old tree on
the first snapshot, so the old policy outlives the deleted file for one command.

The exact parent does not show this two-step transition. The result depends on how many commands
snapshot before a user describes or publishes a change. Explicitly emptying/unsetting the rule does
not have the same delayed behavior.

See [release evidence](evidence/macos-release/A04-removed.json) and
[parent comparison](evidence/base-comparison/A04-removed.json). Add coverage that checks tree IDs
and stored content after successive snapshots, rather than calling another snapshotting command to
inspect the first result.

### F05: LFS patterns hide symlinks that Git would version

**Priority: P2. Recommendation: fix or explicitly narrow the policy before merge.**

A new symlink named `link.bin` is silently omitted under `*.bin filter=lfs`. Git stages it as a
symlink, mode 120000; the exact parent tracks it. Git's LFS content filter does not clean a symlink
into a pointer. Applying path exclusion indiscriminately therefore loses ordinary symlink tracking.
An existing filtered file replaced with a symlink similarly leaves the old pointer in jj's tree.

See [new-symlink reproduction](evidence/macos-release/A08-symlink-asset.json),
[parent comparison](evidence/base-comparison/A08-symlink-asset.json), and
[path-kind probes](evidence/transitions-sol/release/comparison.json). This is distinct from symlinked
`.gitattributes` files, which the PR correctly does not follow in the tested case.

## Diagnostics and compatibility gaps

### F06: Explicit tracking can succeed without tracking or an explanation

`jj file track new.bin` returns 0, prints no error or explanation, and leaves the file absent from
the revision when it matches the ignored filter. Normal status omits the path too. A separate
`--debug status` probe emitted generic lock events, but did not name the skipped file or filter.

This is a P2 usability/observability defect. At minimum, explicit requests should explain the
exclusion and how to handle it. A nonzero result or a useful diagnostic would make the operation
reviewable. Routine status output need not become noisy for every hydrated asset.
See [tracking evidence](evidence/macos-release/C02-force-track.json) and
[diagnostic probe](evidence/performance-sol/results.json).

### F07: Local and global attributes are not used

With an LFS filter rule solely in `.git/info/attributes` or `core.attributesFile`, Git reports
`filter=lfs` but jj snapshots raw payload bytes. The PR reads repository `.gitattributes` files;
it does not claim full attribute implementation. This is a compatibility limitation, not a new
regression relative to the parent.

Deferral is reasonable if the support boundary is explicit. Without that explanation, users can
reasonably assume a file recognized by Git LFS is protected from raw snapshots. Tests should lock
down both supported precedence and unsupported sources. Evidence:
[local attributes](evidence/macos-release/A02-info-attributes.json),
[global attributes](evidence/macos-release/A03-global-attributes.json).

### F08: Documentation and PR description are partly stale

The pinned documentation says jj-created workspaces have no `.git` context. A colocated workspace
in this build has a `.git` file and `git lfs checkout` hydrates successfully. The limitation needs
qualification by repository/workspace layout. See
[workspace evidence](evidence/macos-release/W03-workspace.json).

The PR body and commit message say symlinked attributes are followed and all attribute files are
parsed on every snapshot. The implementation checks symlink metadata and loads rules lazily for
visited paths. Describe the current implementation rather than inherited limitations.

The older discussion already raised checkout behavior and the `file_states` cache as risks;
[that discussion][old-concern] directly motivated the transition probes here. Earlier fixes and
reports in [PR 9676][prior-fixes] were treated as regression coverage, not new findings.

## What works

The core path succeeds: existing hydrated LFS files remain hydrated on disk, their stored pointers
stay intact across repeated snapshots and unrelated edits, and filtered deletion does not spuriously
remove an existing pointer. Newly filtered paths are excluded. These are useful properties for
read-mostly assets and ordinary code work in an LFS repository.

The passing attribute matrix includes nested overrides, unset/unspecified values, root macros,
last-rule precedence, quoted spaces, Unicode filenames, recursive patterns, directory-only patterns,
and custom filter selection. Explicit opt-out snapshots raw bytes as configured. That option is
broad: a hosted test initially picked up another hydrated asset as raw content, so it is not a safe
standalone recipe for adding just one pointer.

Other positive evidence:

- Temporary `jj run` snapshots preserve filtered pointers while capturing ordinary edits.
- Missing local objects leave pointers intact; restoring the object allows external hydration.
- Empty LFS files, malformed pointer-like disk content, and literal pointers do not corrupt the
  existing stored pointer during exclusion. This is preservation, not pointer validation by jj.
- Unreadable attributes fail with path context on macOS; invalid filter configuration identifies
  the key and fails. Synthetic parser/store error tests also pass.
- Absolute custom LFS storage, skip-smudge, import migration before/after jj initialization, and
  export migration followed by `jj git import` worked in the bounded lifecycle probes.
- Ordinary and `--recent` pruning retained tested jj-only objects, including an abandoned change.
  Forced pruning could delete their payloads while operation recovery restored only the pointers.
  That is an operational caution, not an established ordinary-prune regression. Long-aged retention
  and all reachability configurations remain untested.

See [lifecycle results](evidence/lifecycle-sol/results.json).

## Hosted publication and failure handling

The [disposable repository][hosted-repo] exercised actual GitHub LFS storage with only
7,168 payload bytes uploaded. Git/LFS initial publication and independent fresh clones succeeded.
An ordinary jj change beside an existing LFS asset pushed successfully and cloned correctly.

Publishing a new pointer through `jj git push` did not upload its LFS object. GitHub rejected the
push with `GH008`, identified the missing object, and left the remote ref unchanged. Explicit
`git lfs push --object-id` followed by retry succeeded; another fresh clone hydrated both assets.
This confirms a workable manual handoff and GitHub's protection, not automatic LFS upload by jj.
Other servers must not be assumed to enforce the same check.

A direct `jj git clone` initially produced pointers, as expected. In the deliberately isolated
configuration, `git lfs pull` downloaded objects but returned 0 while saying LFS was not installed
for the repository and skipping checkout. `git lfs install --local` followed by another pull hydrated
both objects. Exit status alone is therefore insufficient for the documented hydration workflow.
See [initial journey](evidence/hosted-jj-clone/commands.json) and
[installed result](evidence/hosted-jj-clone/installed-results.json).

The GitHub archive contained pointers under its default setting. The LFS lock/list/unlock API worked,
and the test lock was removed. These checks do not establish enforcement of another user's lock by
jj. See [hosted command evidence](evidence/hosted/commands.txt) and
[verified repository state](evidence/hosted/repository-state.json).

Seven loopback failure scenarios exercised batch HTTP 401, 403, 404, 429, 500, HTTP 200 with
per-object 404 errors, and corrupted downloaded content. Git LFS rejected every case; jj status,
stored pointers, on-disk pointers, and the empty object cache stayed intact. The errors came from
Git LFS, not a jj transfer implementation. The 429 case retried despite a configured retry limit,
but completed under the test guard. No credentials were embedded in mock URLs, so these probes do
not establish secret-redaction behavior. See [failure evidence](evidence/failures-sol/results).

## Performance and build validation

A 64 MiB hydrated asset retained its payload hash and a 133-byte stored pointer. A release status
completed in about 14 ms in that fixture and did not trigger the new-file size limit.

Five alternating warm runs using the same release binary produced these medians:

| Fixture | Filtering enabled | Filtering disabled |
| --- | ---: | ---: |
| 3,000 ordinary files, empty attributes | 18.5 ms | 18.1 ms |
| 3,000 ordinary files, 5,000 root patterns | 27.4 ms | 19.0 ms |
| 3,000 ordinary files, 60 nested attribute files | 19.6 ms | 18.5 ms |

The pattern-heavy case has measurable overhead in this sample, but not evidence of a prohibitive
slowdown. A separate 120-directory fixture was around 171 ms enabled versus 171 ms disabled.
These are local warm microbenchmarks, not a production throughput or memory guarantee. Peak RSS,
very deep trees, network filesystems, cold caches, and multi-gigabyte assets were not characterized.
See [raw performance data](evidence/performance-sol/results.json).

Relevant upstream verification passed:

- 26 attribute unit tests.
- 97 local-working-copy and concurrent-working-copy tests, including the five filtered cases.
- 40 `jj run` tests and 11 diff-edit tests, including both filtered temporary-snapshot regressions.
- Locked macOS debug/release builds and Linux debug build.
- `cargo check --locked -p jj-lib --no-default-features`.

That is 174 distinct relevant passing tests; the focused subsets are not counted twice.
The full repository suite, clippy, MSRV build, downstream compatibility builds, and Windows execution
were not performed. The no-Git check and backend tests address prior review concerns but do not
replace those remaining configurations. Logs are in [verification evidence](evidence/verification).

## Rebase onto main

A duplicate of the pinned change was replayed onto main at
`f1b29bced933e289096a9c98276153e29dd95674` in an isolated jj checkout. It conflicts in
`CHANGELOG.md` and `Cargo.lock`. No Rust source conflict was reported. The conflicts were preserved;
no resolutions or post-rebase build were made because this pass identifies issues rather than fixes
them. Thus main compatibility is not established by the pinned-head test results.
See [conflicts](evidence/verification/rebase-conflicts.txt).

## Recommended merge gate

1. Define and test a safe checkout boundary for modified excluded files: F01 is the primary blocker.
1. Correct the untrack recipe and provide a tested clone/edit/publish/recover workflow.
1. Repair the file-state invariant and cover path-kind transitions.
1. Settle deletion-of-attributes and symlink semantics with regression tests.
1. Give explicit tracking an actionable outcome and document unsupported attribute sources.
1. Resolve the main integration conflicts and run the critical suite on the resulting head.
1. Run Windows validation when execution is available, particularly read-only files, path handling,
   case changes, and CRLF interactions. Keep native LFS transport as a separate scope decision.

No review, issue, or comment was posted on the upstream PR, and its branch was not modified.
The [test repository][hosted-repo] is now public with the owner's authorization. The earlier
unexecuted CI run was removed from GitHub because its diagnostic contained account information.
Its original evidence remains local and is not included in this publication.

[pr]: https://github.com/jj-vcs/jj/pull/9635
[prior-fixes]: https://github.com/jj-vcs/jj/pull/9676
[old-concern]: https://github.com/jj-vcs/jj/pull/9068#issuecomment-4099481480
[compat-source]: https://github.com/jj-vcs/jj/blob/d8a56d1a38cae110529ef8e67e72e3e2057ed3ca/docs/git-compatibility.md#L77-L84
[hosted-repo]: https://github.com/joshka/jj-lfs-eval-20260925
[windows-run]: https://github.com/joshka/jj-lfs-eval-20260925/actions/runs/36173559917
