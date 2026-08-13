#!/usr/bin/env python3
"""
Checks 6 external blocklist repos for domains added in the last 24
hours, and reports which of those domains are NOT already present in
this project's lists/categories/. Does not add anything automatically
- purely a signal for manual research, consistent with this project's
independent-verification approach.

Requires GITHUB_TOKEN in the environment (GitHub Actions provides this
automatically) to avoid low unauthenticated API rate limits.

Run:
    python3 scripts/check_new_domains.py
"""

import json
import os
import re
import sys
import urllib.parse
import urllib.request
from pathlib import Path
from datetime import datetime, timedelta, timezone

ROOT = Path(__file__).resolve().parent.parent
CATEGORIES_DIR = ROOT / "lists" / "categories"
REPORT_PATH = ROOT / "reports" / "new-domain-suggestions.md"
AGGRESSIVE_FLAG = "!"

DOMAIN_RE = re.compile(
    r"^(?=.{1,253}$)(?!-)[A-Za-z0-9-]{1,63}(?<!-)"
    r"(\.(?!-)[A-Za-z0-9-]{1,63}(?<!-))+$"
)

# owner, repo, path, format: "hosts" | "adblock" | "plain"
SOURCES = [
    {"name": "AdGuard SDNS Filter", "owner": "AdguardTeam", "repo": "AdGuardSDNSFilter",
     "path": "Filters/filter.txt", "format": "adblock"},
    {"name": "StevenBlack/hosts", "owner": "StevenBlack", "repo": "hosts",
     "path": "hosts", "format": "hosts"},
    {"name": "EasyPrivacy", "owner": "easylist", "repo": "easylist",
     "path": "easyprivacy/easyprivacy_general.txt", "format": "adblock"},
    {"name": "1Hosts Lite", "owner": "badmojr", "repo": "1Hosts",
     "path": "Lite/domains.txt", "format": "plain"},
    {"name": "no-google", "owner": "nickspaargaren", "repo": "no-google",
     "path": "categories/domains.txt", "format": "hosts"},
    {"name": "a-dove-is-dumb (Adobe)", "owner": "ignaciocastro", "repo": "a-dove-is-dumb",
     "path": "list.txt", "format": "hosts"},
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


def api_get(url, token):
    req = urllib.request.Request(
        url,
        headers={
            "Accept": "application/vnd.github+json",
            "Authorization": f"Bearer {token}" if token else "",
            "X-GitHub-Api-Version": "2022-11-28",
            "User-Agent": "shadow-blocker-blocklist-bot",
        },
    )
    with urllib.request.urlopen(req, timeout=20) as resp:
        return json.loads(resp.read().decode())


def get_recent_commits(owner, repo, path, since_iso, token):
    url = (
        f"https://api.github.com/repos/{owner}/{repo}/commits"
        f"?path={urllib.parse.quote(path)}&since={since_iso}&per_page=100"
    )
    return api_get(url, token)


def get_commit_patch(owner, repo, sha, path, token):
    url = f"https://api.github.com/repos/{owner}/{repo}/commits/{sha}"
    data = api_get(url, token)
    for f in data.get("files", []):
        if f.get("filename") == path:
            return f.get("patch", "") or ""
    return ""


def extract_added_domains(patch_text, fmt):
    domains = set()
    for line in patch_text.splitlines():
        if not line.startswith("+") or line.startswith("+++"):
            continue
        content = line[1:].strip()
        if not content:
            continue

        if fmt == "hosts":
            m = re.match(r"^(?:0\.0\.0\.0|127\.0\.0\.1|::1)\s+(\S+)", content)
            if m:
                d = m.group(1).lower()
                if d != "localhost" and DOMAIN_RE.match(d):
                    domains.add(d)

        elif fmt == "adblock":
            if content.startswith(("!", "#", "@@")):
                continue
            m = re.match(r"^\|\|([a-zA-Z0-9.-]+)\^", content)
            if m:
                d = m.group(1).lower()
                if DOMAIN_RE.match(d):
                    domains.add(d)

        elif fmt == "plain":
            if content.startswith(("#", "!")):
                continue
            d = content.lower()
            if DOMAIN_RE.match(d):
                domains.add(d)

    return domains


def check_all():
    token = os.environ.get("GITHUB_TOKEN", "")
    since_iso = (datetime.now(timezone.utc) - timedelta(hours=24)).strftime(
        "%Y-%m-%dT%H:%M:%SZ"
    )
    existing = load_existing_domains()
    print(f"Loaded {len(existing)} existing domains from lists/categories/")

    sections = []
    for src in SOURCES:
        print(f"Checking {src['name']}...")
        try:
            commits = get_recent_commits(
                src["owner"], src["repo"], src["path"], since_iso, token
            )
        except Exception as e:
            sections.append((src["name"], None, str(e)))
            continue

        new_domains = {}
        for c in commits:
            sha = c["sha"]
            try:
                patch = get_commit_patch(
                    src["owner"], src["repo"], sha, src["path"], token
                )
            except Exception:
                continue
            for d in extract_added_domains(patch, src["format"]):
                new_domains.setdefault(d, c["html_url"])

        missing = sorted(
            (d, url) for d, url in new_domains.items() if d not in existing
        )
        sections.append((src["name"], missing, None))

    REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
    now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    lines = [
        "# New Domain Suggestions",
        "",
        f"Generated: {now}",
        "",
        "Domains added to the sources below in the last 24 hours that",
        "are NOT currently in this project's lists/categories/. This is",
        "a research signal only - nothing is added automatically. Each",
        "entry should be independently researched and classified before",
        "being added to a category file.",
        "",
    ]

    for name, missing, error in sections:
        lines.append(f"## {name}")
        lines.append("")
        if error is not None:
            lines.append(f"Could not check: {error}")
        elif not missing:
            lines.append("No new candidate domains in the last 24 hours.")
        else:
            lines.append("| Domain | Seen in commit |")
            lines.append("|---|---|")
            for domain, url in missing:
                lines.append(f"| {domain} | [link]({url}) |")
        lines.append("")

    REPORT_PATH.write_text("\n".join(lines) + "\n", encoding="utf-8")
    total = sum(len(m) for _, m, e in sections if e is None and m)
    print(f"\n{total} candidate domain(s) across all sources. "
          f"See {REPORT_PATH.relative_to(ROOT)}")


if __name__ == "__main__":
    check_all()
