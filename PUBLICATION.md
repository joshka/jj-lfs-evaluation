# Publication and privacy notes

This repository contains a curated publication copy of the evaluation. The original evidence is
retained locally and is not uploaded. No implementation changes are included.

## Transformations

- Replace the evaluator's machine identity in nested operation-log JSON with `eval@example.invalid`.
- Normalize temporary lab paths to `/tmp/jj-lfs-evaluation` for readability and portability.
  These are historical transcript paths, not a claim that a reader has that directory.
- Omit account-specific runner diagnostics. A short sanitized summary records that the initial
  Windows attempt did not execute. The original unavailable run was removed from the test repository.
- Keep minimal PR and commit metadata. Omit copied discussion archives and commit messages whose
  author/contact metadata is unnecessary to reproduce the evaluation.
- Omit local packaging and hosted-clone helper scripts. Archive historical worker scripts as
  `.py.txt`; their environment-specific commands require adaptation before reuse.
- Omit filesystem metadata files. The runnable core harness accepts explicit binary and output paths.

Public GitHub repository names, source revisions, software versions, and technical test observations
remain available for verification. Synthetic email addresses use the reserved `example.invalid`
domain. The owner permits `joshka` file paths; path normalization is for portability.

Sanitized transcripts preserve the observed commands, failures, and results apart from these
transformations. They are not byte-identical to the private originals. `SHA256SUMS` records this
publication's files and excludes itself and version-control internals.

## Publication checks

Gitleaks 8.30.1 scanned the publication files before upload with full secret redaction enabled and
reported no findings. A separate email and machine-identifier inventory checked text and nested JSON;
only the synthetic address `eval@example.invalid` remained in the initial publication inventory.
An independent agent also reviewed the publication copy. The final upload includes a fresh scan after
any additional evidence is added.

These checks cover credentials, nonpublic email addresses, account information, hostnames, and
unnecessary machine metadata. Pattern-based scanning cannot prove that arbitrary text contains no
private information; curated scope and manual review complement it.

The disposable test repository was scanned separately, including its history, before being made
public for Windows CI. Its author identity uses a public GitHub noreply address or synthetic identity.

The published core harness was rerun from this directory against the pinned release binary using
six documented cases. It produced two passes and four previously documented gaps, with no setup
errors. This verifies that the portable entry point still runs; it adds no new independent scenarios.

## Windows follow-up

The completed Windows run contributes selected per-case JSON and status summaries. Fixture email
strings and runner host labels were sanitized. Raw job logs and disposable repository internals are
not copied here. The GitHub Actions run is public in the authorized test repository; those public
runner logs are distinct from the curated evidence in this report.

Two Windows failures were false positives caused by comparing slash-form paths with backslash-form
CLI output. Original results are preserved beside an audited status list. The published core harness
now normalizes Windows path separators for that comparison; the Windows run was not repeated after
this assertion correction. No jj implementation was changed.
