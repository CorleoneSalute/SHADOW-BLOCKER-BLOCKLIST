#!/usr/bin/env python3
"""
Checks whether every domain in lists/categories/ still resolves via DNS.
Does NOT delete anything — writes a report of domains that failed to
resolve after multiple retries, for manual review.

Run:
    python3 scripts/check_dead_domains.py
"""

import socket
import sys
import time
from pathlib import Path
from datetime import datetime, timezone
from concurrent.futures import ThreadPoolExecutor, as_completed

ROOT = Path(__file__).resolve().parent.parent
CATEGORIES_DIR = ROOT / "lists" / "categories"
REPORT_PATH = ROOT / "reports" / "dead-domains.md"

AGGRESSIVE_FLAG = "!"
RETRIES = 3
RETRY_DELAY_SECONDS = 2
TIMEOUT_SECONDS = 5
MAX_WORKERS = 20


def parse_master_file(path: Path):
    domains = []
    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue
        if line.endswith(AGGRESSIVE_FLAG):
            line = line[: -len(AGGRESSIVE_FLAG)].strip()
        domains.append(line.lower())
    return domains


def resolves(domain: str) -> bool:
    socket.setdefaulttimeout(TIMEOUT_SECONDS)
    for attempt in range(RETRIES):
        try:
            socket.getaddrinfo(domain, None)
            return True
        except Exception:
            if attempt < RETRIES - 1:
                time.sleep(RETRY_DELAY_SECONDS)
    return False


def check_all():
    if not CATEGORIES_DIR.exists():
        print(f"ERROR: {CATEGORIES_DIR} not found", file=sys.stderr)
        sys.exit(1)

    entries = []
    for master_path in sorted(CATEGORIES_DIR.glob("*.txt")):
        category = master_path.stem
        for domain in parse_master_file(master_path):
            entries.append((category, domain))

    print(f"Checking {len(entries)} domains across "
          f"{len(set(c for c, _ in entries))} categories...")

    dead = []
    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as pool:
        futures = {
            pool.submit(resolves, domain): (category, domain)
            for category, domain in entries
        }
        checked = 0
        for future in as_completed(futures):
            category, domain = futures[future]
            checked += 1
            if checked % 200 == 0:
                print(f"  ...{checked}/{len(entries)} checked")
            try:
                ok = future.result()
            except Exception:
                ok = False
            if not ok:
                dead.append((category, domain))

    dead.sort()

    REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
    now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    lines = [
        "# Dead Domain Report",
        "",
        f"Generated: {now}",
        f"Checked: {len(entries)} domains across "
        f"{len(set(c for c, _ in entries))} categories",
        f"Not resolving after {RETRIES} attempts: {len(dead)}",
        "",
        "This report does NOT auto-remove anything. Review each entry",
        "manually before deleting it from lists/categories/ — a domain",
        "can temporarily fail to resolve for reasons unrelated to being",
        "dead (geo-blocking, resolver issues, maintenance windows).",
        "",
        "| Category | Domain |",
        "|---|---|",
    ]
    for category, domain in dead:
        lines.append(f"| {category} | {domain} |")

    REPORT_PATH.write_text("\n".join(lines) + "\n", encoding="utf-8")

    print(f"\n{len(dead)} domain(s) did not resolve. "
          f"See {REPORT_PATH.relative_to(ROOT)}")


if __name__ == "__main__":
    check_all()
