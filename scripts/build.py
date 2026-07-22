#!/usr/bin/env python3
"""
Build script for the DNS blocklist project.
Reads canonical category master files from lists/categories/*.txt
and generates ready-to-use blocklists under dist/.
"""

import re
import sys
from pathlib import Path
from datetime import datetime, timezone

ROOT = Path(__file__).resolve().parent.parent
CATEGORIES_DIR = ROOT / "lists" / "categories"
DIST_DIR = ROOT / "dist"

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


def build():
    if not CATEGORIES_DIR.exists():
        print(f"ERROR: {CATEGORIES_DIR} not found", file=sys.stderr)
        sys.exit(1)

    master_files = sorted(CATEGORIES_DIR.glob("*.txt"))
    if not master_files:
        print(f"ERROR: no *.txt files found in {CATEGORIES_DIR}", file=sys.stderr)
        sys.exit(1)

    all_basic, all_aggressive = set(), set()
    stats = []
    had_invalid = False

    for master_path in master_files:
        category = master_path.stem
        basic, agg_only, invalid = parse_master_file(master_path)

        if invalid:
            had_invalid = True
            print(f"[WARN] {category}: {len(invalid)} invalid line(s) skipped:")
            for line in invalid:
                print(f"    {line!r}")

        aggressive = (basic | agg_only) if AGGRESSIVE_IS_SUPERSET else agg_only

        all_basic |= basic
        all_aggressive |= aggressive

        pretty_name = category.replace("-", " ").upper()
        write_variant(DIST_DIR / "basic", category, f"{pretty_name} BLOCKLIST - BASIC", basic)
        write_variant(DIST_DIR / "aggressive", category, f"{pretty_name} BLOCKLIST - AGGRESSIVE", aggressive)

        stats.append((category, len(basic), len(aggressive)))

    write_variant(DIST_DIR / "basic", "all", "FULL BLOCKLIST - BASIC", all_basic)
    write_variant(DIST_DIR / "aggressive", "all", "FULL BLOCKLIST - AGGRESSIVE", all_aggressive)

    col = max(len(c) for c, _, _ in stats) + 2
    print("\nBuild summary:")
    print(f"{'category':<{col}}{'basic':>10}{'aggressive':>12}")
    for category, b, a in stats:
        print(f"{category:<{col}}{b:>10}{a:>12}")
    print(f"{'TOTAL (unique)':<{col}}{len(all_basic):>10}{len(all_aggressive):>12}")

    if had_invalid:
        print("\nNote: some lines were skipped as invalid domains.", file=sys.stderr)


if __name__ == "__main__":
    build()
