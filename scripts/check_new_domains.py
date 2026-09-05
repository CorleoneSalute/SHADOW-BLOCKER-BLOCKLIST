#!/usr/bin/env python3
"""
Checks external blocklist sources for domains that are new since the
last run, by diffing each source's full current domain set against a
saved snapshot - not by parsing git commit patches, which GitHub
silently truncates for large diffs.

For each candidate domain:
  - Checks whether its core domain (last two labels, e.g. example.com
    for sub.example.com) already appears somewhere in this project's
    lists/categories/. Split into "core domain already covered" vs
    "new platform".
  - Flags domains whose core label looks algorithmically generated
    (high character entropy, low vowel ratio) as possibly obfuscated
    tracking infrastructure worth extra scrutiny. This is a heuristic
    signal, not a classification - false positives/negatives happen.

Also compares each source's total domain count to its previous run.
If it drops by more than 50%, that's flagged as a likely sign the
source changed its file format or location rather than a real content
change, since silent parsing failures look identical to "no domains
found" otherwise.

Does not add anything automatically - purely a signal for manual
research, consistent with this project's independent-verification
approach.

State (previous snapshots) is stored under reports/.snapshots/ and
must be committed alongside the report, so each run only needs to
diff against the last one.

Run:
    python3 scripts/check_new_domains.py
"""

import math
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

DROP_WARNING_THRESHOLD = 0.5

MIN_LABEL_LENGTH_FOR_CHECK = 6
ENTROPY_THRESHOLD = 3.2
VOWEL_RATIO_THRESHOLD = 0.25

SOURCES = [
    {"name": "AdGuard SDNS Filter",
     "raw_url": "https://adguardteam.github.io/AdGuardSDNSFilter/Filters/filter.txt",
     "format": "adblock"},
    {"name": "StevenBlack", "owner": "StevenBlack", "repo": "hosts",
     "path": "hosts", "format": "hosts"},
    {"name": "EasyPrivacy", "owner": "easylist", "repo": "easylist",
     "path": "easyprivacy/easyprivacy_general.txt", "format": "adblock"},
    {"name": "1Hosts Lite", "owner": "badmojr", "repo": "1Hosts",
     "path": "Lite/domains.txt", "format": "plain"},
    {"name": "no-google", "owner": "nickspaargaren", "repo": "no-google",
     "path": "categories/domains.txt", "format": "hosts"},
    {"name": "HaGeZi Multi Ultimate",
     "raw_url": "https://raw.githubusercontent.com/hagezi/dns-blocklists/main/adblock/ultimate.txt",
     "format": "adblock"},

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


def base_domain(domain: str) -> str:
    parts = domain.split(".")
    if len(parts) < 2:
        return domain
    return ".".join(parts[-2:])


def shannon_entropy(s: str) -> float:
    if not s:
        return 0.0
    freq = {}
    for c in s:
        freq[c] = freq.get(c, 0) + 1
    length = len(s)
    entropy = 0.0
    for count in freq.values():
        p = count / length
        entropy -= p * math.log2(p)
    return entropy


def looks_algorithmically_generated(domain: str) -> bool:
    label = base_domain(domain).split(".")[0]
    if len(label) < MIN_LABEL_LENGTH_FOR_CHECK:
        return False
    entropy = shannon_entropy(label)
    vowels = sum(1 for c in label if c in "aeiou")
    vowel_ratio = vowels / len(label)
    return entropy > ENTROPY_THRESHOLD or vowel_ratio < VOWEL_RATIO_THRESHOLD


def fetch_raw(src):
    if "raw_url" in src:
        url = src["raw_url"]
    else:
        url = f"https://raw.githubusercontent.com/{src['owner']}/{src['repo']}/HEAD/{src['path']}"
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
    if "raw_url" in src:
        key = src["raw_url"]
    else:
        key = f"{src['owner']}_{src['repo']}_{src['path']}"
    slug = re.sub(r"[^A-Za-z0-9._-]", "_", key)
    return SNAPSHOT_DIR / f"{slug}.txt"


def load_snapshot(path):
    if not path.exists():
        return None
    return set(path.read_text(encoding="utf-8").splitlines())


def save_snapshot(path, domains):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(sorted(domains)) + "\n", encoding="utf-8")


def check_all():
    existing = load_existing_domains()
    existing_bases = {base_domain(d) for d in existing}
    print(f"Loaded {len(existing)} existing domains "
          f"({len(existing_bases)} distinct core domains) from lists/categories/")

    results = []
    drop_warnings = []

    for src in SOURCES:
        print(f"Checking {src['name']}...")
        try:
            content = fetch_raw(src)
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

        if len(previous) > 0 and len(current) < len(previous) * (1 - DROP_WARNING_THRESHOLD):
            drop_warnings.append(
                f"{src['name']}: domain count dropped from {len(previous)} to "
                f"{len(current)} ({(1 - len(current) / len(previous)) * 100:.0f}% decrease) "
                f"- possible source format or location change, worth checking manually."
            )

        newly_added = current - previous
        missing = sorted(d for d in newly_added if d not in existing)
        known_base, new_base_normal, new_base_random = [], [], []
        for d in missing:
            if base_domain(d) in existing_bases:
                known_base.append(d)
            elif looks_algorithmically_generated(d):
                new_base_random.append(d)
            else:
                new_base_normal.append(d)

        save_snapshot(snap_path, current)
        results.append((src.get("group"), src["name"], "ok",
                         (known_base, new_base_normal, new_base_random)))

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
    ]

    if drop_warnings:
        lines.append("## ⚠ Possible source issues")
        lines.append("")
        for w in drop_warnings:
            lines.append(f"- {w}")
        lines.append("")

    lines += [
        "Each candidate is split into three groups:",
        "- Core domain already covered: likely just a missing subdomain",
        "  for a platform already researched in this project.",
        "- New platform: the core domain isn't present at all.",
        "- Possibly obfuscated: the domain name looks algorithmically",
        "  generated (high character randomness, few vowels) rather",
        "  than a real word or brand - a heuristic signal only, not a",
        "  classification. Often worth researching first, since these",
        "  are sometimes deliberately obscured tracking infrastructure.",
        "",
    ]

    def render_domain_table(domains):
        block = ["| Domain |", "|---|"]
        for domain in domains:
            block.append(f"| {domain} |")
        block.append("")
        return block

    def render_source_block(name, status, payload, heading_level):
        block = [f"{'#' * heading_level} {name}", ""]
        if status == "first_run":
            block.append("First run for this source - baseline snapshot saved, "
                          "nothing to compare against yet.")
            block.append("")
        elif status == "error":
            block.append(f"Could not check: {payload}")
            block.append("")
        else:
            known_base, new_normal, new_random = payload
            if not known_base and not new_normal and not new_random:
                block.append("No new candidate domains since the last run.")
                block.append("")
            else:
                if new_random:
                    block.append("**Possibly obfuscated:**")
                    block.append("")
                    block += render_domain_table(new_random)
                if new_normal:
                    block.append("**New platform (core domain not in lists/categories/):**")
                    block.append("")
                    block += render_domain_table(new_normal)
                if known_base:
                    block.append("**Core domain already covered:**")
                    block.append("")
                    block += render_domain_table(known_base)
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

    total_known = sum(len(p[0]) for _, _, s, p in results if s == "ok")
    total_new = sum(len(p[1]) for _, _, s, p in results if s == "ok")
    total_random = sum(len(p[2]) for _, _, s, p in results if s == "ok")
    print(f"\n{total_known} known-core candidate(s), {total_new} new-platform "
          f"candidate(s), {total_random} possibly-obfuscated candidate(s).")
    if drop_warnings:
        print(f"{len(drop_warnings)} source(s) flagged for a large domain-count drop.")
    print(f"See {REPORT_PATH.relative_to(ROOT)}")


if __name__ == "__main__":
    check_all()
