# Local verification notes

[中文](README.md) · English

The public repository retains manuals, official attribution, calling code and checking tools, not execution JSON, replies, reasoning bodies, HTTP records, usage statistics or execution source fingerprints. [Publishing policy](../en/docs/evidence-policy.md)

Original maintainer records live in Git-ignored `.local/evidence/` and are not included in clones or downloads. Readers can still read, query and run offline checks without them; missing local records cannot be treated as private test passes. Recheck changed calls rather than editing old fingerprints into success.

Live calls require user authorization and may incur charges or upload media. The file executor defaults to inventory; only explicit `--execute` makes calls. New reports default to the local directory and omit execution times and durations. Setup, commands and exit codes are in [reproduction](../en/docs/verification.md).

Relocation preserves original records for local maintenance without rewriting previously published Git history. Older history may still contain test times; hiding the current directory does not erase history.
