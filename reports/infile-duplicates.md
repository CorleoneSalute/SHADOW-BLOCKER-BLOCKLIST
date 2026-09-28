# In-File Duplicate Domain Report

Generated: 2026-09-28 19:04 UTC

Domains that appear more than once within the SAME category
file - usually a copy-paste mistake in a large file. The build
already silently deduplicates these (no functional harm to
dist/), but they're worth cleaning up for a tidy source file.

"Exact match: yes" means every occurrence is byte-for-byte
identical (same case, same trailing "!" flag). "no" means they
differ - worth a closer look, since a mismatched "!" flag
changes which tier the domain ends up in.

3 duplicate domain(s) found across 1 file(s):

## Social-Media

| Domain | Lines | Exact match |
|---|---|---|
| frontier4-pp-lf.amemv.com | 925, 941 | yes |
| frontier4-pp-lq.amemv.com | 926, 942 | yes |
| frontier4-pp.amemv.com | 927, 943 | yes |

