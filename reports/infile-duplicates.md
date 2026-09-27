# In-File Duplicate Domain Report

Generated: 2026-09-27 14:48 UTC

Domains that appear more than once within the SAME category
file - usually a copy-paste mistake in a large file. The build
already silently deduplicates these (no functional harm to
dist/), but they're worth cleaning up for a tidy source file.

"Exact match: yes" means every occurrence is byte-for-byte
identical (same case, same trailing "!" flag). "no" means they
differ - worth a closer look, since a mismatched "!" flag
changes which tier the domain ends up in.

9 duplicate domain(s) found across 1 file(s):

## Video-Streaming

| Domain | Lines | Exact match |
|---|---|---|
| ads.hbomax.com | 283, 499 | no - differs |
| ads.paramountplus.com | 300, 502 | no - differs |
| saa.paramountplus.com | 304, 503 | no - differs |
| saa.cbsi.com | 308, 504 | no - differs |
| ads.peacocktv.com | 327, 507 | no - differs |
| ads.hotstar.com | 355, 522 | no - differs |
| ads.zee5.com | 360, 526 | no - differs |
| ads.iqiyi.com | 372, 532 | no - differs |
| ads.crunchyroll.com | 449, 537 | no - differs |

