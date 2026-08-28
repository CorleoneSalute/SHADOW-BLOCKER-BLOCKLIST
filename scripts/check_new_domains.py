#!/usr/bin/env python3
"""
Checks external blocklist sources for domains that are new since the
last run, by diffing each source's full current domain set against a
saved snapshot - not by parsing git commit patches, which GitHub
silently truncates for large diffs (a real API limitation that caused
the previous version of this script to miss almost everything from
large sources like StevenBlack/hosts or EasyPrivacy).

Reports domains that are NOT already present in this project's
lists/categories/. Does not add anything automatically - purely a
signal for manual research, consistent with this project's
independent-verification approach.

State (previous snapshots) is stored under reports/.snapshots/ and
must be committed alongside the report, so each run only needs to
diff against the last one.

Run:
    python3 scripts/check_new_domains.py
"""

import re
import urllib.request
from pathlib import Path
from datetime import datetime, timezone

ROOT = Path(__file__).resolve().parent.parent
CATEGORIES_DIR = ROOT / "lists" / "categories"
REPORT_PATH = ROOT / "reports" / "new-domain-suggestions.md"
SNAPSHOT_DIR = ROOT / "reports" / ".snapshots"
AGGRESSIVE_FLAG = "!"

DOMAIN_RE = re.compile(
    r"^(?=.{1,253}$)(?!-)[A-Za-z0-9-]{1,63}(?<!-)"
    r"(\.(?!-)[A-Za-z0-9-]{1,63}(?<!-))+$"
)

# owner, repo, path, format: "hosts" | "adblock" | "plain" | "dnsmasq"
# "group" is optional - sources sharing a group are nested under one
# header in the report instead of each getting a top-level section.
SOURCES = [
    {"name": "AdGuard SDNS Filter", "owner": "AdguardTeam", "repo": "AdGuardSDNSFilter",
     "path": "Filters/filter.txt", "format": "adblock"},
    {"name": "StevenBlack", "owner": "StevenBlack", "repo": "hosts",
     "path": "hosts", "format": "hosts"},
    {"name": "EasyPrivacy", "owner": "easylist", "repo": "easylist",
     "path": "easyprivacy/easyprivacy_general.txt", "format": "adblock"},
    {"name": "1Hosts Lite", "owner": "badmojr", "repo": "1Hosts",
     "path": "Lite/domains.txt", "format": "plain"},
    {"name": "no-google", "owner": "nickspaargaren", "repo": "no-google",
     "path": "categories/domains.txt", "format": "hosts"},
    {"name": "a-dove-is-dumb (Adobe)", "owner": "ignaciocastro", "repo": "a-dove-is-dumb",
     "path": "list.txt", "format": "hosts"},

    {"name": "Samsung", "group": "HaGeZi Native Lists",
     "owner": "hagezi", "repo": "dns-blocklists",
     "path": "dnsmasq/native.samsung.txt", "format": "dnsmasq"},
    {"name": "Xiaomi", "group": "HaGeZi Native Lists",
     "owner": "hagezi", "repo": "dns-blocklists",
     "path": "dnsmasq/native.xiaomi.txt", "format": "dnsmasq"},
    {"name": "Huawei", "group": "HaGeZi Native Lists",
     "owner": "hagezi", "repo": "dns-blocklists",
     "path": "dnsmasq/native.huawei.txt", "format": "dnsmasq"},
    {"name": "Oppo/Realme", "group": "HaGeZi Native Lists",
     "owner": "hagezi", "repo": "dns-blocklists",
     "path": "dnsmasq/native.oppo-realme.txt", "format": "dnsmasq"},
    {"name": "Vivo", "group": "HaGeZi Native Lists",
     "owner": "hagezi", "repo": "dns-blocklists",
     "path": "dnsmasq/native.vivo.txt", "format": "dnsmasq"},
    {"name": "LG WebOS", "group": "HaGeZi Native Lists",
     "owner": "hagezi", "repo": "dns-blocklists",
     "path": "dnsmasq/native.lgwebos.txt", "format": "dnsmasq"},
    {"name": "TikTok", "group": "HaGeZi Native Lists",
     "owner": "hagezi", "repo": "dns-blocklists",
     "path": "dnsmasq/native.tiktok.extended.txt", "format": "dnsmasq"},
]


def load_existing_domains():
    existing = set()
    for master_path in CATEGORIES_DIR.glob("*.txt"):
        for raw_line in master_path.read_text(encoding="utf-8").splitlines():
            line = raw_line.strip()
            if not line or line.startswith("#"):
                continue
            if line.endswith(AGGRESSIVE_FLAG):
                line = line[: -len(AGGRESSIVE_FLAG)].strip()
            existing.add(line.lower())
    return existing


def fetch_raw(owner, repo, path):
    url = f"https://raw.githubusercontent.com/{owner}/{repo}/HEAD/{path}"
    req = urllib.request.Request(url, headers={"User-Agent": "shadow-blocker-blocklist-bot"})
    with urllib.request.urlopen(req, timeout=30) as resp:
        return resp.read().decode("utf-8", errors="replace")


def extract_domains(content, fmt):
    domains = set()
    for raw_line in content.splitlines():
        line = raw_line.strip()
        if not line:
            continue

        if fmt == "hosts":
            m = re.match(r"^(?:0\.0\.0\.0|127\.0\.0\.1|::1)\s+(\S+)", line)
            if m:
                d = m.group(1).lower()
                if d != "localhost" and DOMAIN_RE.match(d):
                    domains.add(d)

        elif fmt == "adblock":
            if line.startswith(("!", "#", "@@")):
                continue
            m = re.match(r"^\|\|([a-zA-Z0-9.-]+)\^", line)
            if m:
                d = m.group(1).lower()
                if DOMAIN_RE.match(d):
                    domains.add(d)

        elif fmt == "plain":
            if line.startswith(("#", "!")):
                continue
            d = line.lower()
            if DOMAIN_RE.match(d):
                domains.add(d)

        elif fmt == "dnsmasq":
            if line.startswith("#"):
                continue
            m = re.match(r"^local=/([a-zA-Z0-9.-]+)/$", line)
            if m:
                d = m.group(1).lower()
                if DOMAIN_RE.match(d):
                    domains.add(d)

    return domains


def snapshot_path(src):
    slug = f"{src['owner']}_{src['repo']}_{src['path']}".replace("/", "_")
    return SNAPSHOT_DIR / f"{slug}.txt"


def load_snapshot(path):
    if not path.exists():
        return None  # no prior snapshot - first run for this source
    return set(path.read_text(encoding="utf-8").splitlines())


def save_snapshot(path, domains):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(sorted(domains)) + "\n", encoding="utf-8")


def check_all():
    existing = load_existing_domains()
    print(f"Loaded {len(existing)} existing domains from lists/categories/")

    # status: "ok" | "first_run" | "error"
    results = []
    for src in SOURCES:
        print(f"Checking {src['name']}...")
        try:
            content = fetch_raw(src["owner"], src["repo"], src["path"])
        except Exception as e:
            results.append((src.get("group"), src["name"], "error", str(e)))
            continue

        current = extract_domains(content, src["format"])
        snap_path = snapshot_path(src)
        previous = load_snapshot(snap_path)

        if previous is None:
            save_snapshot(snap_path, current)
            results.append((src.get("group"), src["name"], "first_run", None))
            continue

        newly_added = current - previous
        missing = sorted(d for d in newly_added if d not in existing)
        save_snapshot(snap_path, current)
        results.append((src.get("group"), src["name"], "ok", missing))

    REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
    now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    lines = [
        "# New Domain Suggestions",
        "",
        f"Generated: {now}",
        "",
        "Domains that appeared in the sources below since the last run,",
        "and are NOT currently in this project's lists/categories/. This",
        "is a research signal only - nothing is added automatically. Each",
        "entry should be independently researched and classified before",
        "being added to a category file.",
        "",
        "Detection compares each source's full current domain list against",
        "a saved snapshot from the previous run, instead of parsing git",
        "diffs - GitHub silently omits diff content for large file changes,",
        "which made the previous version of this script miss almost",
        "everything from large sources.",
        "",
    ]

    def render_source_block(name, status, payload, heading_level):
        block = [f"{'#' * heading_level} {name}", ""]
        if status == "first_run":
            block.append("First run for this source - baseline snapshot saved, "
                          "nothing to compare against yet.")
        elif status == "error":
            block.append(f"Could not check: {payload}")
        elif not payload:
            block.append("No new candidate domains since the last run.")
        else:
            block.append("| Domain |")
            block.append("|---|")
            for domain in payload:
                block.append(f"| {domain} |")
        block.append("")
        return block

    seen_groups = []
    ungrouped = []
    grouped = {}
    for group, name, status, payload in results:
        if group is None:
            ungrouped.append((name, status, payload))
        else:
            if group not in grouped:
                grouped[group] = []
                seen_groups.append(group)
            grouped[group].append((name, status, payload))

    for name, status, payload in ungrouped:
        lines += render_source_block(name, status, payload, heading_level=2)

    for group in seen_groups:
        lines.append(f"## {group}")
        lines.append("")
        for name, status, payload in grouped[group]:
            lines += render_source_block(name, status, payload, heading_level=3)

    REPORT_PATH.write_text("\n".join(lines) + "\n", encoding="utf-8")
    total = sum(len(p) for _, _, s, p in results if s == "ok" and p)
    print(f"\n{total} candidate domain(s) across all sources. "
          f"See {REPORT_PATH.relative_to(ROOT)}")


if __name__ == "__main__":
    check_all()
