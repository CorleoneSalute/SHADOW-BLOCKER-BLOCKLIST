# In-File Duplicate Domain Report

Generated: 2026-09-27 14:54 UTC

Domains that appear more than once within the SAME category
file - usually a copy-paste mistake in a large file. The build
already silently deduplicates these (no functional harm to
dist/), but they're worth cleaning up for a tidy source file.

"Exact match: yes" means every occurrence is byte-for-byte
identical (same case, same trailing "!" flag). "no" means they
differ - worth a closer look, since a mismatched "!" flag
changes which tier the domain ends up in.

1 duplicate domain(s) found across 1 file(s):

## Video-Streaming

| Domain | Lines | Exact match |
|---|---|---|
| ads.zee5.com | 358, 519 | no - differs |

