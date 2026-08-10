#!/usr/bin/env python3
"""
Checks whether every domain in lists/categories/ still resolves via DNS.
Does NOT delete or modify anything - writes a report of domains that
failed to resolve after multiple retries, for manual review.

Also detects wildcard DNS: if a domain's base domain (last two labels)
resolves for ANY random subdomain, none of its subdomains can be
trusted as "confirmed alive" - they're flagged separately for manual
review instead of being marked as resolving.

Run:
    python3 scripts/check_dead_domains.py
"""

import random
import socket
import string
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
RANDOM_LABEL_LENGTH = 24


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


def base_domain(domain: str) -> str:
    """Best-effort base domain: last two labels.
    Not perfect for multi-part TLDs (e.g. co.uk) but good enough
    for flagging wildcard DNS in practice."""
    parts = domain.split(".")
    if len(parts) < 2:
        return domain
    return ".".join(parts[-2:])


def resolves(hostname: str) -> bool:
    socket.setdefaulttimeout(TIMEOUT_SECONDS)
    for attempt in range(RETRIES):
        try:
            socket.getaddrinfo(hostname, None)
            return True
        except Exception:
            if attempt < RETRIES - 1:
                time.sleep(RETRY_DELAY_SECONDS)
    return False


def has_wildcard_dns(base: str) -> bool:
    """Test a random, essentially-guaranteed-not-to-exist subdomain.
    If it resolves, the base domain uses wildcard DNS and none of its
    subdomains can be trusted as individually confirmed."""
    random_label = "".join(
        random.choices(string.ascii_lowercase + string.digits, k=RANDOM_LABEL_LENGTH)
    )
    probe = f"{random_label}.{base}"
    return resolves(probe)


def check_all():
    if not CATEGORIES_DIR.exists():
        print(f"ERROR: {CATEGORIES_DIR} not found", file=sys.stderr)
        sys.exit(1)

    entries = []
    for master_path in sorted(CATEGORIES_DIR.glob("*.txt")):
        category = master_path.stem
        for domain in parse_master_file(master_path):
            entries.append((category, domain))

    unique_bases = sorted(set(base_domain(d) for _, d in entries))
    print(f"Checking {len(unique_bases)} base domains for wildcard DNS...")

    wildcard_bases = set()
    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as pool:
        futures = {pool.submit(has_wildcard_dns, base): base for base in unique_bases}
        for future in as_completed(futures):
            base = futures[future]
            try:
                if future.result():
                    wildcard_bases.add(base)
            except Exception:
                pass

    if wildcard_bases:
        print(f"  {len(wildcard_bases)} base domain(s) use wildcard DNS "
              f"(their subdomains can't be auto-verified)")

    print(f"Checking {len(entries)} domains across "
          f"{len(set(c for c, _ in entries))} categories...")

    dead = []
    wildcard_flagged = []
    to_check = [(c, d) for c, d in entries if base_domain(d) not in wildcard_bases]
    for category, domain in entries:
        if base_domain(domain) in wildcard_bases:
            wildcard_flagged.append((category, domain))

    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as pool:
        futures = {
            pool.submit(resolves, domain): (category, domain)
            for category, domain in to_check
        }
        checked = 0
        for future in as_completed(futures):
            category, domain = futures[future]
            checked += 1
            if checked % 200 == 0:
                print(f"  ...{checked}/{len(to_check)} checked")
            try:
                ok = future.result()
            except Exception:
                ok = False
            if not ok:
                dead.append((category, domain))

    dead.sort()
    wildcard_flagged.sort()

    REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
    now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    lines = [
        "# Dead Domain Report",
        "",
        f"Generated: {now}",
        f"Checked: {len(entries)} domains across "
        f"{len(set(c for c, _ in entries))} categories",
        f"Not resolving after {RETRIES} attempts: {len(dead)}",
        f"Skipped (wildcard DNS on base domain, unverifiable): {len(wildcard_flagged)}",
        "",
        "This report does NOT auto-remove anything. Review each entry",
        "manually before deleting it from lists/categories/ - a domain",
        "can temporarily fail to resolve for reasons unrelated to being",
        "dead (geo-blocking, resolver issues, maintenance windows).",
        "",
        "## Not resolving",
        "",
        "| Category | Domain |",
        "|---|---|",
    ]
    for category, domain in dead:
        lines.append(f"| {category} | {domain} |")

    lines += [
        "",
        "## Wildcard DNS - could not be individually verified",
        "",
        "These domains belong to a base domain that resolves for ANY",
        "random subdomain, so DNS resolution can't confirm whether the",
        "specific subdomain is real or was ever real. Review manually",
        "(e.g. check whether the domain appears in browser network logs",
        "for the platform, or in the original research source).",
        "",
        "| Category | Domain | Base domain |",
        "|---|---|---|",
    ]
    for category, domain in wildcard_flagged:
        lines.append(f"| {category} | {domain} | {base_domain(domain)} |")

    REPORT_PATH.write_text("\n".join(lines) + "\n", encoding="utf-8")

    print(f"\n{len(dead)} domain(s) did not resolve.")
    print(f"{len(wildcard_flagged)} domain(s) flagged as wildcard-unverifiable.")
    print(f"See {REPORT_PATH.relative_to(ROOT)}")


if __name__ == "__main__":
    check_all()
                print(f"  ...{checked}/{len(to_check)} checked")
            try:
                ok = future.result()
            except Exception:
                ok = False
            if not ok:
                dead.append((category, domain))

    dead.sort()
    wildcard_flagged.sort()

    REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
    now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    lines = [
        "# Dead Domain Report",
        "",
        f"Generated: {now}",
        f"Checked: {len(entries)} domains across "
        f"{len(set(c for c, _ in entries))} categories",
        f"Not resolving after {RETRIES} attempts: {len(dead)}",
        f"Skipped (wildcard DNS on base domain, unverifiable): {len(wildcard_flagged)}",
        "",
        "This report does NOT auto-remove anything. Review each entry",
        "manually before deleting it from lists/categories/ - a domain",
        "can temporarily fail to resolve for reasons unrelated to being",
        "dead (geo-blocking, resolver issues, maintenance windows).",
        "",
        "## Not resolving",
        "",
        "| Category | Domain |",
        "|---|---|",
    ]
    for category, domain in dead:
        lines.append(f"| {category} | {domain} |")

    lines += [
        "",
        "## Wildcard DNS - could not be individually verified",
        "",
        "These domains belong to a base domain that resolves for ANY",
        "random subdomain, so DNS resolution can't confirm whether the",
        "specific subdomain is real or was ever real. Review manually",
        "(e.g. check whether the domain appears in browser network logs",
        "for the platform, or in the original research source).",
        "",
        "| Category | Domain | Base domain |",
        "|---|---|---|",
    ]
    for category, domain in wildcard_flagged:
        lines.append(f"| {category} | {domain} | {base_domain(domain)} |")

    REPORT_PATH.write_text("\n".join(lines) + "\n", encoding="utf-8")

    print(f"\n{len(dead)} domain(s) did not resolve.")
    print(f"{len(wildcard_flagged)} domain(s) flagged as wildcard-unverifiable.")
    print(f"See {REPORT_PATH.relative_to(ROOT)}")


if __name__ == "__main__":
    check_all()
            except Exception:
                pass

    if wildcard_bases:
        print(f"  {len(wildcard_bases)} base domain(s) use wildcard DNS "
              f"(their subdomains can't be auto-verified)")

    print(f"Checking {len(entries)} domains across "
          f"{len(set(c for c, _ in entries))} categories...")

    dead = []
    wildcard_flagged = []
    to_check = [(c, d) for c, d in entries if base_domain(d) not in wildcard_bases]
    for category, domain in entries:
        if base_domain(domain) in wildcard_bases:
            wildcard_flagged.append((category, domain))

    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as pool:
        futures = {
            pool.submit(resolves, domain): (category, domain)
            for category, domain in to_check
        }
        checked = 0
        for future in as_completed(futures):
            category, domain = futures[future]
            checked += 1
            if checked % 200 == 0:
                print(f"  ...{checked}/{len(to_check)} checked")
            try:
                ok = future.result()
            except Exception:
                ok = False
            if not ok:
                dead.append((category, domain))

    dead.sort()
    wildcard_flagged.sort()

    REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
    now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    lines = [
        "# Dead Domain Report",
        "",
        f"Generated: {now}",
        f"Checked: {len(entries)} domains across "
        f"{len(set(c for c, _ in entries))} categories",
        f"Not resolving after {RETRIES} attempts: {len(dead)}",
        f"Skipped (wildcard DNS on base domain, unverifiable): {len(wildcard_flagged)}",
        "",
        "This report does NOT auto-remove anything. Review each entry",
        "manually before deleting it from lists/categories/ - a domain",
        "can temporarily fail to resolve for reasons unrelated to being",
        "dead (geo-blocking, resolver issues, maintenance windows).",
        "",
        "## Not resolving",
        "",
        "| Category | Domain |",
        "|---|---|",
    ]
    for category, domain in dead:
        lines.append(f"| {category} | {domain} |")

    lines += [
        "",
        "## Wildcard DNS - could not be individually verified",
        "",
        "These domains belong to a base domain that resolves for ANY",
        "random subdomain, so DNS resolution can't confirm whether the",
        "specific subdomain is real or was ever real. Review manually",
        "(e.g. check whether the domain appears in browser network logs",
        "for the platform, or in the original research source).",
        "",
        "| Category | Domain | Base domain |",
        "|---|---|---|",
    ]
    for category, domain in wildcard_flagged:
        lines.append(f"| {category} | {domain} | {base_domain(domain)} |")

    REPORT_PATH.write_text("\n".join(lines) + "\n", encoding="utf-8")

    print(f"\n{len(dead)} domain(s) did not resolve.")
    print(f"{len(wildcard_flagged)} domain(s) flagged as wildcard-unverifiable.")
    print(f"See {REPORT_PATH.relative_to(ROOT)}")


if __name__ == "__main__":
    check_all()        "|---|---|",
    ]
    for category, domain in dead:
        lines.append(f"| {category} | {domain} |")

    REPORT_PATH.write_text("\n".join(lines) + "\n", encoding="utf-8")

    print(f"\n{len(dead)} domain(s) did not resolve. "
          f"See {REPORT_PATH.relative_to(ROOT)}")


if __name__ == "__main__":
    check_all()
