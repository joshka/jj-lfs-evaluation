# Methodology and run record

## Scope

Evaluate snapshot exclusion and the manual Git LFS workflows around it. Automatic cleaning,
smudging, uploads, and lock enforcement are not assumed features of this PR. Working-copy safety,
pointer preservation, intelligible command outcomes, and accurate instructions are evaluated.

- PR: [9635](https://github.com/jj-vcs/jj/pull/9635).
- Head: `d8a56d1a38cae110529ef8e67e72e3e2057ed3ca`.
- Exact parent: `e9f48b3e4c1c5e816fbbfbfd06c154a6a96b0215`.
- Main integration target: `f1b29bced933e289096a9c98276153e29dd95674`.
- Evaluation date: 25 September 2026.

The [source-integrity check](evidence/verification/source-integrity.json) found no changes in the
710 archived source files checked after the local evaluation. Build outputs were additional files.
No implementation fix, upstream review, issue, or comment was published.

## Method

Each core case uses a fresh repository, isolated Git/jj configuration, deterministic payloads, and
sequential version-control operations. Git LFS creates the initial pointer and object. The test then
runs the pinned jj binary and inspects the stated combination of exit status, stderr, disk bytes,
stored bytes, path lists, and hashes. See [shared fixture](TEST-CASES.md#shared-fixture-and-commands).

Command records retain argv, working directory, stdout/stderr, return codes, and elapsed time.
Checks of successive snapshots use `--ignore-working-copy` to avoid taking an extra snapshot while
reading the previous result. Significant regressions were compared with the exact parent; release
builds distinguish debug assertions from release failures. Selected cases use real GitHub storage;
controlled transfer failures use only a loopback mock server.

The linked per-case record is the authority for an observation. A worker's PASS label is narrower
than a general workflow endorsement: some probes characterize exclusion or deliberate forced-prune
loss. The case reference states each actual criterion and its limits.

## Environments and results

| Configuration | PASS | FAIL | SKIP | Setup errors |
| --- | ---: | ---: | ---: | ---: |
| macOS arm64, release | 34 | 6 | 0 | 0 |
| macOS arm64, debug, corrected checks | 33 | 7 | 0 | 0 |
| Linux arm64, debug, modern Git | 32 | 7 | 1 | 0 |
| Windows x64, debug, audited assertions | 30 | 6 | 4 | 0 |

These are 40 repeated scenarios, not 160 independent tests. Supplementary probes overlap the core
cases and are not added to a combined pass rate. Windows originally reported 28 PASS, eight FAIL,
four OBSERVED, and zero ERROR; two failures were path-separator assertion mistakes corrected from
command evidence, without rerunning Windows. The four OBSERVED entries are explicit skips.

PASS means the case criterion held; FAIL means it did not. A FAIL may identify either a defect or
an unsupported compatibility feature. SKIP means no assertion was made. Setup errors are separated
from product failures. The harness exits nonzero for setup errors, not for ordinary FAIL results:
a green CI run is not an all-tests-passed claim.

Versions and provenance:

- macOS: Git 2.55.0, Git LFS 3.8.0, Rust 1.98.1; PR and parent report jj 0.45.1.
- Modern Linux: Ubuntu 26.04, Git 2.53.0, Git LFS 3.7.1, Python 3.14.4.
- Windows: Server 2025, Git 2.55.0.windows.5, Git LFS 3.7.1, Python 3.12.10.
  Source was extracted from the pinned PR archive beneath the CI repository. The binary's version
  suffix therefore identifies the enclosing CI commit, not the PR source revision.

[Binary hashes](evidence/verification/binary-sha256.txt),
[release environment](evidence/macos-release/environment.json),
[Linux environment](evidence/linux-modern/environment.json), and
[Windows provenance](evidence/windows/README.md) preserve the details.

## Run record and corrections

This is a record of evaluation stages, not an inferred minute-by-minute chronology. Earlier outputs
remain in evidence; final results use the corrected assertions and appropriate environment.

| Stage | Outcome used in this report |
| --- | --- |
| PR and parent builds | Exact-parent comparisons available for the principal regressions |
| Initial macOS core sweep | Exposed workflow gaps and a debug panic |
| Assertion review and release sweep | Corrected recovery checks; panic limited to debug |
| Initial Linux container | Git 2.39.5 could not create the required colocated workspace |
| Modern Linux container | Repeated all 40 cases with Git 2.53.0; one root-permission skip |
| Hosted and supplementary probes | Verified manual handoffs and bounded external failure handling |
| Main replay | Changelog/lockfile conflicts; no resolved build |
| Windows CI | 33 focused upstream tests passed; 40 core cases completed |
| Evidence presentation review | Reconciled timing prose with retained JSON; no new benchmark |

Specific corrections matter when reading earlier artifacts:

- **Workspace:** an initial expectation copied the docs' missing-`.git` limitation. Actual colocated
  workspaces have a `.git` file and support the tested external hydration.
- **Sparse loss:** the first check treated disk removal as failure even when bytes were stored.
  The corrected check tests recoverability. The parent passes; the PR fails.
- **Path-kind panic:** A10 initially appeared as a command ERROR. Inspection established a product
  panic; the corrected check records FAIL with exit 101. The release command succeeds.
- **Windows paths:** A01-directory-only and A01-nested-unset compared slash-form inputs with
  backslash-form output. The recorded output proves inclusion. The published harness now normalizes
  those comparisons; no Windows rerun is claimed.
- **Attribute-source calibration:** an early local-rule fixture also matched a root rule. The
  corrected fixture matches only `.git/info/attributes`; the earlier probe was confounded.
- **Performance:** a fixture description incorrectly said “debug” when used with a release binary.
  Binary provenance was unchanged. Earlier README timing figures also disagreed with the retained
  JSON; [X06](TEST-CASES.md#x06-performance-config) now uses that JSON directly.
- **Runner setup:** the first Docker login shell lacked cargo on PATH. An initial Windows attempt
  did not execute; its account-specific diagnostic is omitted from public evidence. Neither is a
  product result.

The [model-calibration record](model-calibration.md) discusses the delegated execution experiment.
It is separate from product findings and contains no measured cost or token-efficiency claim.

## Standalone finding reproductions

The [manual reproductions](TEST-CASES.md#manual-reproduction-setup) for all eight findings were
executed against the
pinned macOS debug binary with a 1,100-byte synthetic seed. Each reproduced its stated observation.
These are reduced confirmations of existing findings, not new core scenarios or a Windows rerun.
[Transcripts and binary hash](evidence/manual-reproductions) record the verification. Runner-specific
temporary paths and thread identifiers are normalized. Suggested fixes remain unimplemented.

## Limits and source basis

The source archive, build profile, configuration, platform, and fixture scope limit every result.
The full repository suite, downstream crate compilation, Windows release behavior, and several
advanced LFS workflows remain untested. [Remaining coverage](FOLLOW-UP.md) lists them explicitly.
[Publication notes](PUBLICATION.md) describe sanitization and distinguish original observations from
presentation corrections.

The test design drew on the following official documentation and prior review. These links identify
the design basis; test evidence establishes behavior of the pinned build, not a promise about future
Git, LFS, or jj releases.

- [Git attributes](https://git-scm.com/docs/gitattributes): matching, precedence, and path types.
- [LFS pointer specification](https://github.com/git-lfs/git-lfs/blob/main/docs/spec.md): stored data.
- [LFS pull](https://github.com/git-lfs/git-lfs/blob/main/docs/man/git-lfs-pull.adoc) and
  [checkout](https://github.com/git-lfs/git-lfs/blob/main/docs/man/git-lfs-checkout.adoc): hydration.
- [LFS configuration](https://github.com/git-lfs/git-lfs/blob/main/docs/man/git-lfs-config.adoc):
  storage, fetch selection, and locking configuration.
- [Prune](https://github.com/git-lfs/git-lfs/blob/main/docs/man/git-lfs-prune.adoc) and
  [migration](https://github.com/git-lfs/git-lfs/blob/main/docs/man/git-lfs-migrate.adoc): lifecycle.
- [Batch API](https://github.com/git-lfs/git-lfs/blob/main/docs/api/batch.md): HTTP and object errors.
- [GitHub upload failures][uploads] and [archive behavior][archives]: hosted workflow expectations.
- [Earlier checkout/cache concerns][prior] and [regression fixes][fixes]: probe selection.

[uploads]: https://docs.github.com/en/repositories/working-with-files/managing-large-files/resolving-git-large-file-storage-upload-failures
[archives]: https://docs.github.com/en/repositories/managing-your-repositorys-settings-and-features/managing-repository-settings/managing-git-lfs-objects-in-archives-of-your-repository
[prior]: https://github.com/jj-vcs/jj/pull/9068#issuecomment-4099481480
[fixes]: https://github.com/jj-vcs/jj/pull/9676
