# In-File Duplicate Domain Report

Generated: 2026-10-02 14:55 UTC

Domains that appear more than once within the SAME category
file - usually a copy-paste mistake in a large file. The build
already silently deduplicates these (no functional harm to
dist/), but they're worth cleaning up for a tidy source file.

"Exact match: yes" means every occurrence is byte-for-byte
identical (same case, same trailing "!" flag). "no" means they
differ - worth a closer look, since a mismatched "!" flag
changes which tier the domain ends up in.

2 duplicate domain(s) found across 1 file(s):

## Content-Creation-Live-Streaming

| Domain | Lines | Exact match |
|---|---|---|
| ads.rmbl.ws | 38, 44 | yes |
| analytics.livestream.com | 83, 91 | yes |

