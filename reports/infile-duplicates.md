# In-File Duplicate Domain Report

Generated: 2026-09-20 17:25 UTC

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
| ads.aimitv.com | 76, 594 | no - differs |

## Video-Streaming

| Domain | Lines | Exact match |
|---|---|---|
| rum.netflix.com | 172, 473 | no - differs |
| ads.disneyplus.com | 230, 478 | no - differs |
| ads.hbomax.com | 280, 495 | no - differs |
| ads.paramountplus.com | 297, 498 | no - differs |
| saa.paramountplus.com | 301, 499 | no - differs |
| saa.cbsi.com | 305, 500 | no - differs |
| ads.peacocktv.com | 324, 503 | no - differs |
| ads.hotstar.com | 352, 518 | no - differs |
| ads.zee5.com | 357, 522 | no - differs |
| ads.iqiyi.com | 369, 528 | no - differs |
| ads.crunchyroll.com | 443, 533 | no - differs |

