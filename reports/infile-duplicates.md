# In-File Duplicate Domain Report

Generated: 2026-09-27 14:35 UTC

Domains that appear more than once within the SAME category
file - usually a copy-paste mistake in a large file. The build
already silently deduplicates these (no functional harm to
dist/), but they're worth cleaning up for a tidy source file.

"Exact match: yes" means every occurrence is byte-for-byte
identical (same case, same trailing "!" flag). "no" means they
differ - worth a closer look, since a mismatched "!" flag
changes which tier the domain ends up in.

10 duplicate domain(s) found across 1 file(s):

## Video-Streaming

| Domain | Lines | Exact match |
|---|---|---|
| ads.disneyplus.com | 233, 483 | no - differs |
| ads.hbomax.com | 283, 500 | no - differs |
| ads.paramountplus.com | 300, 503 | no - differs |
| saa.paramountplus.com | 304, 504 | no - differs |
| saa.cbsi.com | 308, 505 | no - differs |
| ads.peacocktv.com | 327, 508 | no - differs |
| ads.hotstar.com | 355, 523 | no - differs |
| ads.zee5.com | 360, 527 | no - differs |
| ads.iqiyi.com | 372, 533 | no - differs |
| ads.crunchyroll.com | 449, 538 | no - differs |

