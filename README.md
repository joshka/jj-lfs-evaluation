# jj Git LFS evaluation

[PR 9635](https://github.com/jj-vcs/jj/pull/9635), head `d8a56d1a38ca` · 25 September 2026.
Tested on macOS, Linux, and Windows. No implementation fixes made.

**Do not merge this head unchanged:** checkout can discard edited hydrated assets, and the documented
untrack procedure removes committed pointers. Existing pointers survive ordinary snapshots, but that
does not make asset editing safe.

- **[Findings](FINDINGS.md)** — failures first; commands, outcomes, impact, and working workflows.
- **[Test cases](TEST-CASES.md)** — every core case in ID order, plus supplementary investigations.
- **[Methodology](METHODOLOGY.md)** — environments, result counts, run record, and test corrections.
- **[Remaining coverage](FOLLOW-UP.md)** — what has not been tested and what proposed fixes need.

[Machine-readable matrix](scenario-matrix.csv) · [Runnable harness](harness/evaluate.py) ·
[Privacy and publication notes](PUBLICATION.md)
