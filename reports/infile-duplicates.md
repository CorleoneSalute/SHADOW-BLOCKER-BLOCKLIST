# In-File Duplicate Domain Report

Generated: 2026-09-27 14:31 UTC

Domains that appear more than once within the SAME category
file - usually a copy-paste mistake in a large file. The build
already silently deduplicates these (no functional harm to
dist/), but they're worth cleaning up for a tidy source file.

"Exact match: yes" means every occurrence is byte-for-byte
identical (same case, same trailing "!" flag). "no" means they
differ - worth a closer look, since a mismatched "!" flag
changes which tier the domain ends up in.

12 duplicate domain(s) found across 2 file(s):

## Smart-TV

| Domain | Lines | Exact match |
|---|---|---|
| ads.aimitv.com | 76, 597 | no - differs |

## Video-Streaming

| Domain | Lines | Exact match |
|---|---|---|
| rum.netflix.com | 173, 479 | no - differs |
| ads.disneyplus.com | 233, 484 | no - differs |
| ads.hbomax.com | 283, 501 | no - differs |
| ads.paramountplus.com | 300, 504 | no - differs |
| saa.paramountplus.com | 304, 505 | no - differs |
| saa.cbsi.com | 308, 506 | no - differs |
| ads.peacocktv.com | 327, 509 | no - differs |
| ads.hotstar.com | 355, 524 | no - differs |
| ads.zee5.com | 360, 528 | no - differs |
| ads.iqiyi.com | 372, 534 | no - differs |
| ads.crunchyroll.com | 449, 539 | no - differs |

