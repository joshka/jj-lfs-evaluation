# Windows evaluation of jj PR 9635

Run: <https://github.com/joshka/jj-lfs-eval-20260925/actions/runs/36173559917> on
`windows-latest` (`Windows-2025Server-10.0.26100-SP0`). The workflow downloaded the public
source archive at the pinned PR head
`d8a56d1a38cae110529ef8e67e72e3e2057ed3ca` and built `jj.exe` from that archive.
The binary SHA-256 was `4ca4451b07f8a8047012863cccd063fb88248370623bdaa8ed191e73e251db93`.
Git was `2.55.0.windows.5`; Git LFS was `3.7.1`.

The binary's `--version` string ended in `ae3af284876d7bad26eab4a7b55affab5c7db3b7`,
the **enclosing disposable CI repository** commit. The source archive was extracted beneath
that repository, so build metadata found its outer Git checkout. This suffix does not identify
the source revision; the archive URL and recorded `source.txt` identify the evaluated PR head.
The workflow did not edit the extracted source.

All focused upstream Windows gates passed:

| Gate | Result |
| --- | --- |
| `cargo check --locked -p jj-lib --no-default-features` | Passed |
| `cargo test --locked -p jj-lib --lib gitattributes` | 26 passed, 0 failed |
| `cargo test --locked -p jj-lib --test runner gitattributes` | 5 passed, 0 failed |
| CLI `gitattributes_filter_in_temp_snapshot` tests | 2 passed, 0 failed |
| `cargo build --locked -p jj-cli --bin jj` | Passed |

The independent harness executed **40 scenarios**. Its original artifact says **28 PASS,
8 FAIL, 4 OBSERVED, 0 ERROR**. Two FAIL labels are Windows separator comparisons in the
harness: `A01-directory-only` and `A01-nested-unset` searched `jj file list` for slash-form
paths, while Windows printed `assets\a.bin` and `sub\a.bin`. In both cases `jj status` also
showed the files added, consistent with `git check-attr` saying the filter is unspecified or
unset. A read-only audit of the recorded commands therefore classifies these two intended
attribute checks as PASS, yielding **30 PASS, 6 FAIL, 4 OBSERVED, 0 ERROR**. The original
results remain in `results-original.json`; `audited-results.json` records only these two
status corrections. No tests were rerun or source changed for this audit.

The six remaining failures are `A02-info-attributes`, `A03-global-attributes`,
`A04-removed`, `A10-file-directory`, `C02-force-track`, and `W02-sparse-dirty`.
`A10-file-directory` is a real `jj status` panic (exit 101) at
`lib/src/local_working_copy.rs:1464`: a tracked `asset.bin` replaced on disk by a directory
leaves the path in one snapshot set but not the other. The same PR scenario panicked in the
macOS recheck; the available base comparison passed on macOS. This is a PR regression supported
by cross-platform evidence, not a Windows-only finding. The other five failures were already
seen in non-Windows evaluation or involve documented compatibility gaps.

The four `OBSERVED` scenarios did not assert a Windows result: symlinked attributes and assets
were skipped because symlink privilege varies; Unix permission enforcement and executable-bit
behavior do not map directly to Windows. `W03-workspace` passed on Windows, including external
hydration in an additional colocated workspace. The A01 Windows separator issue is in the test
harness's parsing of CLI output, not evidence of an attribute-matching defect.

This run did **not** test CRLF conversion (`core.autocrlf=false` in fixtures), case-only renames,
or Windows readonly-attribute behavior. It did test native Windows path rendering and the
listed snapshot/temporary-workspace scenarios. Those gaps remain open platform coverage,
not inferred passes.

The public evidence here includes sanitized per-case JSON under `cases/`, the original and
audited status lists, `environment.json`, `source.txt`, and `check-outcomes.txt`. Raw GitHub
job logs and the full uploaded artifact remain outside this public directory. The sanitization
replaced the synthetic fixture email and any runner host labels; a scan found no credential
patterns or nonpublic email addresses in the selected case data.
