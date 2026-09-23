# In-File Duplicate Domain Report

Generated: 2026-09-23 15:58 UTC

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
| rum.netflix.com | 173, 474 | no - differs |
| ads.disneyplus.com | 231, 479 | no - differs |
| ads.hbomax.com | 281, 496 | no - differs |
| ads.paramountplus.com | 298, 499 | no - differs |
| saa.paramountplus.com | 302, 500 | no - differs |
| saa.cbsi.com | 306, 501 | no - differs |
| ads.peacocktv.com | 325, 504 | no - differs |
| ads.hotstar.com | 353, 519 | no - differs |
| ads.zee5.com | 358, 523 | no - differs |
| ads.iqiyi.com | 370, 529 | no - differs |
| ads.crunchyroll.com | 444, 534 | no - differs |

