# In-File Duplicate Domain Report

Generated: 2026-11-13 06:46 UTC

Domains that appear more than once within the SAME category
file - usually a copy-paste mistake in a large file. The build
already silently deduplicates these (no functional harm to
dist/), but they're worth cleaning up for a tidy source file.

"Exact match: yes" means every occurrence is byte-for-byte
identical (same case, same trailing "!" flag). "no" means they
differ - worth a closer look, since a mismatched "!" flag
changes which tier the domain ends up in.

8 duplicate domain(s) found across 1 file(s):

## AD-Network

| Domain | Lines | Exact match |
|---|---|---|
| mgid.com | 207, 3492 | yes |
| dt07.net | 212, 3495 | yes |
| marketgid.com | 213, 3493 | yes |
| epom.com | 1568, 2424 | yes |
| market.epom.com | 1569, 2425 | yes |
| admaster.com.cn | 2764, 3441 | yes |
| platc-tester.com | 3159, 3161 | yes |
| adadapted.com | 3397, 3413 | yes |

