# In-File Duplicate Domain Report

Generated: 2026-10-06 02:48 UTC

Domains that appear more than once within the SAME category
file - usually a copy-paste mistake in a large file. The build
already silently deduplicates these (no functional harm to
dist/), but they're worth cleaning up for a tidy source file.

"Exact match: yes" means every occurrence is byte-for-byte
identical (same case, same trailing "!" flag). "no" means they
differ - worth a closer look, since a mismatched "!" flag
changes which tier the domain ends up in.

5 duplicate domain(s) found across 3 file(s):

## AD-Network

| Domain | Lines | Exact match |
|---|---|---|
| epom.com | 1564, 2420 | yes |
| market.epom.com | 1565, 2421 | yes |

## Content-Creation-Live-Streaming

| Domain | Lines | Exact match |
|---|---|---|
| ads.rmbl.ws | 38, 44 | yes |
| analytics.livestream.com | 84, 92 | yes |

## Reward-Apps

| Domain | Lines | Exact match |
|---|---|---|
| sweepstakesaday.com | 122, 124 | yes |

