# Model calibration for the LFS evaluation

## Decision

Use **Luna/max to execute reviewed, explicit scripts and collect results**. Use **Sol/low for fixture
construction and adaptive diagnosis**. Keep scenario design, ambiguous safety decisions, and final
cross-checks with the coordinator. This pilot did not justify assigning most autonomous harness
construction to Luna without review.

These are observations from one small task sample, not a general ranking of model quality or cost.
Actual per-agent token charges were not exposed by the collaboration tools, so no dollar or token
saving is claimed. Final script runtimes are not total agent time and are not comparable cost metrics.

## Matched pilot

Independent agents received the same [four-case task](evidence/calibration-task.md.txt):

1. Preserve a committed pointer and hydrated bytes during repeated snapshots and ordinary edits.
1. Exercise attribute precedence and compare a rule present only in `.git/info/attributes`.
1. Fail hydration with a genuinely missing object, then recover after restoring it.
1. Modify a hydrated asset, switch revisions, and compare recoverability with an upstream binary.

The agents had separate repositories and were instructed not to read each other's outputs. Both
used `d8a56d1a38cae110529ef8e67e72e3e2057ed3ca`; the initial comparison binary was the installed
Homebrew jj. The stronger follow-up used a freshly built exact-parent binary.

Models were explicitly selected as `gpt-6-luna` with `max` reasoning and `gpt-6-sol` with `low`
reasoning, following the user's requested comparison. No model was silently substituted.

## Observations

| Case | Sol/low | Luna/max |
| --- | --- | --- |
| C1 pointer preservation | Correct result and hashes | Correct final result and hashes |
| C2 attribute-source gap | Found isolated-source discrepancy | Needed parent correction |
| C3 missing-object recovery | Distinguished no-op checkout | Repaired setup, then correct |
| C4 local-edit loss | Found loss and compared stored bytes | Found loss after correcting setup |

Sol completed the bounded pilot earlier and disclosed the important limits of its fixture. In C4 it
materialized the verified cached LFS payload after Git LFS checkout could not resolve the chosen Git
context; it did not claim that step exercised a successful external checkout. Its C2 precedence
fixture used a nested path rule in the root attributes file, so it did not independently establish
hierarchical subdirectory-file precedence. The coordinator's core matrix tested that separately.

Luna's first C3 attempt had not actually removed the cached object, and its initial C4 setup failed.
It identified and repaired those setup issues. More seriously, its C2 file was called
`info-only.bin` while the root attributes file already contained `*.bin filter=lfs`. It incorrectly
interpreted exclusion as evidence that jj honored the local attribute source. The coordinator found
this confound by reading the script and required `info-only.dat`, matching only the local rule.
The corrected run found the real compatibility gap.

This is the consequential difference: a test can appear to pass and still answer the wrong question.
Checking the independence of the test variable required an audit, not simply checking exit codes or
reading the agent's summary.

The earlier Luna artifacts were preserved with `initial-` and `pre-audit-` names. Its report labels
433.995 seconds as elapsed from first execution to the corrected full execution, excluding earlier
preparation. The final full script run took 33.862 seconds; Sol's final pilot execution took 7.24
seconds. Different fixture implementations and retries make these unsuitable as a speed benchmark.

Evidence: [Sol report](evidence/calibration-sol/report.md.txt),
[Sol script](evidence/calibration-sol/run.py.txt),
[Luna report](evidence/calibration-luna/report.md.txt),
[Luna script](evidence/calibration-luna/run_calibration.py.txt), and
[Luna corrected C2](evidence/calibration-luna/c2-audit-results.json).

## Mechanical follow-up

To separate script execution from fixture design, Luna then received an exact command using the
coordinator-reviewed core harness, with no permission to edit it. The six selected cases were S01,
the two nested A01 cases, A02, P04, and W02.

It executed the command and correctly reported **4 PASS, 2 FAIL, 0 ERROR**. The failures were the known
local-attribute gap and sparse removal of unrecorded edits. It did not turn these expected findings
into setup failures or claim all tests passed. See
[mechanical results](evidence/luna-mechanical/results.json).

That supports using Luna for well-specified execution with external assertions. It does not establish
that it can independently detect every missing assertion or design a valid comparison fixture.

## Delegation used for the larger evaluation

After the pilot, Sol handled adaptive workflow/recovery cases, exact-parent attribution, path-kind
transitions, lifecycle/configuration checks, hosted publication, controlled network failures, and
performance probes. The coordinator authored the reusable core matrix, ran platform/profile sweeps,
audited serious findings, and consolidated the report. Luna performed the fixed-script follow-up.

Coordinator review also corrected its own harness expectations: colocated workspaces had Git context
despite stale documentation, and sparse removal should pass when the parent saves edited bytes in
history. Multiple model tiers do not remove the need to inspect oracles and setup conditions.

A practical future split is:

- Luna: execute immutable reviewed scenarios, collect hashes/logs, summarize structured results, and
  flag deviations without changing the oracle.
- Sol: build fixtures from written scenarios, adapt failed setup, compare versions, and reduce a
  reproducible issue. Require captured evidence for claims and audit a sample of passes.
- Coordinator: choose scenarios, verify the test variable is isolated, resolve scope/compatibility
  questions, classify data-loss risk, and make the readiness recommendation.

Escalate immediately when a fixture cannot establish its precondition, a clean result contradicts
actual bytes, or a command changes unrecorded data. Do not let an execution worker silently weaken
an assertion to make its run pass.
