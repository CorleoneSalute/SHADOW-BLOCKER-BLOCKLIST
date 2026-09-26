# In-File Duplicate Domain Report

Generated: 2026-09-26 15:53 UTC

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
| rum.netflix.com | 173, 476 | no - differs |
| ads.disneyplus.com | 231, 481 | no - differs |
| ads.hbomax.com | 281, 498 | no - differs |
| ads.paramountplus.com | 298, 501 | no - differs |
| saa.paramountplus.com | 302, 502 | no - differs |
| saa.cbsi.com | 306, 503 | no - differs |
| ads.peacocktv.com | 325, 506 | no - differs |
| ads.hotstar.com | 353, 521 | no - differs |
| ads.zee5.com | 358, 525 | no - differs |
| ads.iqiyi.com | 370, 531 | no - differs |
| ads.crunchyroll.com | 446, 536 | no - differs |

