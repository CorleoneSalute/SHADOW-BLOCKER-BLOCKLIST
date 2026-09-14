#!/usr/bin/env python3
"""
Build script for the DNS blocklist project.
Reads canonical category master files from lists/categories/*.txt
and generates ready-to-use blocklists under dist/.

Also detects:
- Cross-category duplicates: a domain appearing in more than one
  category file's basic tier. Not always a mistake (shared
  infrastructure happens), but worth a look.
  -> reports/duplicate-domains.md
- In-file duplicates: a domain appearing more than once within the
  SAME category file (a common copy-paste mistake in large files).
  The build already silently deduplicates these (no functional harm),
  but they're worth cleaning up. Flags whether every occurrence is
  byte-for-byte identical, or differs (case, or a mismatched "!"
  aggressive-only flag - the latter actually matters, since it changes
  which tier the domain ends up in).
  -> reports/infile-duplicates.md

Also keeps each master file's own header in sync: if a category's
"# Total domains: N" line no longer matches its actual domain count,
both that line and "# Last update: ..." are rewritten. Untouched
categories are left alone.
"""

import re
import shutil
import sys
from pathlib import Path
from datetime import datetime, timezone

ROOT = Path(__file__).resolve().parent.parent
CATEGORIES_DIR = ROOT / "lists" / "categories"
DIST_DIR = ROOT / "dist"
DUPLICATE_REPORT_PATH = ROOT / "reports" / "duplicate-domains.md"
INFILE_DUP_REPORT_PATH = ROOT / "reports" / "infile-duplicates.md"

AGGRESSIVE_IS_SUPERSET = True
AGGRESSIVE_FLAG = "!"

DOMAIN_RE = re.compile(
    r"^(?=.{1,253}$)(?!-)[A-Za-z0-9-]{1,63}(?<!-)"
    r"(\.(?!-)[A-Za-z0-9-]{1,63}(?<!-))+$"
)


def parse_master_file(path: Path):
    basic, aggressive_only, invalid = set(), set(), []
    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue
        is_aggressive_only = False
        if line.endswith(AGGRESSIVE_FLAG):
            is_aggressive_only = True
            line = line[: -len(AGGRESSIVE_FLAG)].strip()
        domain = line.lower()
        if not DOMAIN_RE.match(domain):
            invalid.append(raw_line)
            continue
        if is_aggressive_only:
            aggressive_only.add(domain)
        else:
            basic.add(domain)
    return basic, aggressive_only, invalid


def find_infile_duplicates(path: Path):
    """Detects domains appearing more than once within the same master
    file. Returns a list of dicts:
      {"domain": str, "lines": [(line_no, raw_text), ...], "exact_match": bool}
    exact_match is True only if every occurrence's raw text (case and
    the trailing "!" flag included) is byte-for-byte identical."""
    occurrences = {}  # domain_lower -> [(line_no, raw_text), ...]
    for line_no, raw_line in enumerate(
        path.read_text(encoding="utf-8").splitlines(), start=1
    ):
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue
        domain_part = line[:-1].strip() if line.endswith(AGGRESSIVE_FLAG) else line
        domain_lower = domain_part.lower()
        if not DOMAIN_RE.match(domain_lower):
            continue
        occurrences.setdefault(domain_lower, []).append((line_no, line))

    duplicates = []
    for domain_lower, entries in occurrences.items():
        if len(entries) > 1:
            raw_texts = {text for _, text in entries}
            duplicates.append({
                "domain": domain_lower,
                "lines": entries,
                "exact_match": len(raw_texts) == 1,
            })
    return duplicates


def to_plain(domains):
    return "\n".join(sorted(domains))


def to_hosts(domains):
    return "\n".join(f"0.0.0.0 {d}" for d in sorted(domains))


def to_adblock(domains):
    return "\n".join(f"||{d}^" for d in sorted(domains))


FORMATS = (("domains", to_plain), ("hosts", to_hosts), ("adblock", to_adblock))


def render_header(title: str, count: int) -> str:
    now = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    return (
        "# ============================================================\n"
        f"# {title}\n"
        f"# Total domains: {count}\n"
        f"# Generated: {now} (UTC) - auto-generated, do not edit by hand\n"
        "# Source: lists/categories/ (canonical master files)\n"
        "# ============================================================\n\n"
    )


def write_variant(out_dir: Path, category: str, title: str, domains):
    for fmt_name, formatter in FORMATS:
        fmt_dir = out_dir / fmt_name
        fmt_dir.mkdir(parents=True, exist_ok=True)
        out_path = fmt_dir / f"{category}.txt"
        body = formatter(domains)
        out_path.write_text(
            render_header(title, len(domains)) + body + ("\n" if body else ""),
            encoding="utf-8",
        )


def update_master_header(path: Path, total_count: int) -> bool:
    """Rewrites 'Total domains' and 'Last update' in a master file's
    own header to match its current content - but only if the count
    actually changed, so untouched categories don't get their date
    bumped just because build.py ran on every category this time."""
    text = path.read_text(encoding="utf-8")

    total_pattern = re.compile(r"(?im)^(#\s*Total domains:\s*)(\d+)\s*$")
    update_pattern = re.compile(r"(?im)^(#\s*Last update:\s*).+$")

    match = total_pattern.search(text)
    if not match:
        return False

    existing_count = int(match.group(2))
    if existing_count == total_count:
        return False

    now_str = datetime.now(timezone.utc).strftime("%Y/%m/%d")
    new_text = total_pattern.sub(lambda m: f"{m.group(1)}{total_count}", text)
    new_text = update_pattern.sub(lambda m: f"{m.group(1)}{now_str}", new_text)
    path.write_text(new_text, encoding="utf-8")
    return True


def write_duplicate_report(domain_categories: dict):
    duplicates = {
        d: sorted(cats) for d, cats in domain_categories.items() if len(cats) > 1
    }
    DUPLICATE_REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
    now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    lines = [
        "# Duplicate Domain Report",
        "",
        f"Generated: {now}",
        "",
        "Domains that appear in more than one category file's basic",
        "tier. Not always a mistake - shared infrastructure between",
        "platforms happens - but worth a quick look.",
        "",
    ]
    if not duplicates:
        lines.append("No cross-category duplicates found.")
    else:
        lines.append(f"{len(duplicates)} duplicate domain(s) found:")
        lines.append("")
        lines.append("| Domain | Categories |")
        lines.append("|---|---|")
        for domain in sorted(duplicates):
            lines.append(f"| {domain} | {', '.join(duplicates[domain])} |")
    DUPLICATE_REPORT_PATH.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return duplicates


def write_infile_duplicate_report(infile_duplicates):
    INFILE_DUP_REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
    now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    lines = [
        "# In-File Duplicate Domain Report",
        "",
        f"Generated: {now}",
        "",
        "Domains that appear more than once within the SAME category",
        "file - usually a copy-paste mistake in a large file. The build",
        "already silently deduplicates these (no functional harm to",
        "dist/), but they're worth cleaning up for a tidy source file.",
        "",
        "\"Exact match: yes\" means every occurrence is byte-for-byte",
        "identical (same case, same trailing \"!\" flag). \"no\" means they",
        "differ - worth a closer look, since a mismatched \"!\" flag",
        "changes which tier the domain ends up in.",
        "",
    ]
    if not infile_duplicates:
        lines.append("No in-file duplicates found.")
    else:
        total = sum(len(d) for _, d in infile_duplicates)
        lines.append(f"{total} duplicate domain(s) found across "
                      f"{len(infile_duplicates)} file(s):")
        lines.append("")
        for category, dups in infile_duplicates:
            lines.append(f"## {category}")
            lines.append("")
            lines.append("| Domain | Lines | Exact match |")
            lines.append("|---|---|---|")
            for d in dups:
                line_strs = ", ".join(str(ln) for ln, _ in d["lines"])
                exact = "yes" if d["exact_match"] else "no - differs"
                lines.append(f"| {d['domain']} | {line_strs} | {exact} |")
            lines.append("")
    INFILE_DUP_REPORT_PATH.write_text("\n".join(lines) + "\n", encoding="utf-8")


def build():
    if not CATEGORIES_DIR.exists():
        print(f"ERROR: {CATEGORIES_DIR} not found", file=sys.stderr)
        sys.exit(1)

    master_files = sorted(CATEGORIES_DIR.glob("*.txt"))
    if not master_files:
        print(f"ERROR: no *.txt files found in {CATEGORIES_DIR}", file=sys.stderr)
        sys.exit(1)

    if DIST_DIR.exists():
        shutil.rmtree(DIST_DIR)

    all_basic, all_aggressive = set(), set()
    stats = []
    had_invalid = False
    domain_categories = {}  # domain -> set of category names it appears in
    headers_updated = []
    infile_duplicates = []  # (category, [dup dicts])

    for master_path in master_files:
        category = master_path.stem
        basic, agg_only, invalid = parse_master_file(master_path)

        if invalid:
            had_invalid = True
            print(f"[WARN] {category}: {len(invalid)} invalid line(s) skipped:")
            for line in invalid:
                print(f"    {line!r}")

        dups = find_infile_duplicates(master_path)
        if dups:
            infile_duplicates.append((category, dups))
            print(f"[WARN] {category}: {len(dups)} in-file duplicate domain(s)")

        aggressive = (basic | agg_only) if AGGRESSIVE_IS_SUPERSET else agg_only

        all_basic |= basic
        all_aggressive |= aggressive

        for domain in basic:
            domain_categories.setdefault(domain, set()).add(category)

        total_in_file = len(basic) + len(agg_only)
        if update_master_header(master_path, total_in_file):
            headers_updated.append(category)

        pretty_name = category.replace("-", " ").upper()
        write_variant(DIST_DIR / "basic", category, f"{pretty_name} BLOCKLIST - BASIC", basic)
        write_variant(DIST_DIR / "aggressive", category, f"{pretty_name} BLOCKLIST - AGGRESSIVE", aggressive)

        stats.append((category, len(basic), len(aggressive)))

    write_variant(DIST_DIR / "basic", "all", "FULL BLOCKLIST - BASIC", all_basic)
    write_variant(DIST_DIR / "aggressive", "all", "FULL BLOCKLIST - AGGRESSIVE", all_aggressive)

    duplicates = write_duplicate_report(domain_categories)
    write_infile_duplicate_report(infile_duplicates)

    col = max(len(c) for c, _, _ in stats) + 2
    print("\nBuild summary:")
    print(f"{'category':<{col}}{'basic':>10}{'aggressive':>12}")
    for category, b, a in stats:
        print(f"{category:<{col}}{b:>10}{a:>12}")
    print(f"{'TOTAL (unique)':<{col}}{len(all_basic):>10}{len(all_aggressive):>12}")

    if headers_updated:
        print(f"\nUpdated 'Total domains'/'Last update' header in "
              f"{len(headers_updated)} master file(s): {', '.join(headers_updated)}")

    if duplicates:
        print(f"\n[WARN] {len(duplicates)} domain(s) appear in more than one "
              f"category - see reports/duplicate-domains.md")

    if infile_duplicates:
        total_infile = sum(len(d) for _, d in infile_duplicates)
        print(f"[WARN] {total_infile} in-file duplicate(s) across "
              f"{len(infile_duplicates)} file(s) - see reports/infile-duplicates.md")

    if had_invalid:
        print(
            "\nNote: some lines were skipped as invalid domains. "
            "Fix them in lists/categories/ and re-run.",
            file=sys.stderr,
        )


if __name__ == "__main__":
    build()
