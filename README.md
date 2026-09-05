# Shadow Blocker Blocklist

![Build](https://github.com/CorleoneSalute/SHADOW-BLOCKER-BLOCKLIST/actions/workflows/build.yml/badge.svg)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

**Leave the shadows behind. Block trackers. Protect your privacy.**

A DNS blocklist targeting tracking, telemetry, analytics, and
ad-serving domains — covering mainstream platforms, regional services,
and niche app categories not typically covered by general-purpose
blocklists.

## Methodology

Each entry in this list is the result of independent, per-platform
research rather than aggregation from existing third-party sources.
For every platform covered, the relevant subdomain infrastructure was
mapped and manually reviewed before any domain was classified as
tracking-related. The source material behind each category is
published in [`research/`](research/) for independent verification.

## Tiers

| Tier | Description |
|---|---|
| **Basic** | Confirmed tracking domains with minimal risk of affecting app functionality. |
| **Aggressive** | Basic tier plus additional domains that carry a small risk of affecting edge-case functionality (e.g. consent banners, A/B test flags, personalization). |

The Aggressive tier always includes everything in Basic.

## Formats

Each category, and the combined list across all categories, is
published in three formats, for both tiers:

| Format | Path pattern | Compatible with |
|---|---|---|
| Plain domain list | `dist/<tier>/domains/<category>.txt` | Custom scripts, dnsmasq |
| Hosts file | `dist/<tier>/hosts/<category>.txt` | Pi-hole, most hosts-based blockers |
| Adblock syntax | `dist/<tier>/adblock/<category>.txt` | AdGuard Home, AdGuard, uBlock Origin |

## Usage

**Pi-hole or other hosts-based tools** — add as an adlist source:
```
https://raw.githubusercontent.com/CorleoneSalute/SHADOW-BLOCKER-BLOCKLIST/main/dist/basic/hosts/all.txt
```

**AdGuard Home, AdGuard, or uBlock Origin** — add as a filter list:
```
https://raw.githubusercontent.com/CorleoneSalute/SHADOW-BLOCKER-BLOCKLIST/main/dist/basic/adblock/all.txt
```

Replace `basic` with `aggressive` for the stricter tier. To use a
single category instead of the full list, replace `all.txt` with the
category filename, for example:
```
https://raw.githubusercontent.com/CorleoneSalute/SHADOW-BLOCKER-BLOCKLIST/main/dist/basic/hosts/Cloud-Storage.txt
```

## Repository structure

```
research/            source material behind each category (verification trail)
lists/categories/    canonical master lists (source of truth)
scripts/build.py     generates dist/ from lists/categories/
dist/                generated output — do not edit directly
reports/             new-domain reports — see "Keeping this up to date"

```

## Categories

90+ categories spanning mainstream and regional platforms, including
session replay & heatmap tools, data brokers, mental health apps,
consent management platforms, and other niches not typically covered
elsewhere. See [`lists/categories/`](lists/categories/) for the
complete list.

## Roadmap

The following categories are under active research and intentionally
not yet published. Categories with system-wide or platform-wide reach
carry a higher risk of false positives that could affect core
functionality, so each domain is being individually verified before
release.

- Android
- Telehealth & Digital Health
- Email Marketing
- Windows
- Job & Recruitment
- Adult Ecosystem
- Grocery & Food Delivery
- Video Editing & Creative Software
- News

## Acknowledgments

This project is built on independent, from-scratch research rather
than aggregation, but the approach was informed by ideas and
techniques observed in the wider DNS-blocking community. Specific
references:

- [hagezi/dns-blocklists](https://github.com/hagezi/dns-blocklists) —
  some of the project's "native" lists were referenced when
  researching platforms with complex, multi-layered infrastructure.
  
- [v2fly/domain-list-community](https://github.com/v2fly/domain-list-community) —
  referenced for locating core domains of certain platforms.

Domain research and false-positive verification also relied on a
range of publicly available cybersecurity and privacy resources.

## Keeping this up to date

New domains and categories are added through two parallel processes:

**Manual research.** New platforms and emerging tracking techniques
are identified by following cybersecurity and technology news sources,
then researched and classified individually using this project's
methodology (see [Methodology](#methodology) above).

**Automated new-domain signals.** A daily job checks several external
blocklists for domains added in the last 24 hours that aren't yet
covered here, and writes candidates to
`reports/new-domain-suggestions.md`. This is a research signal only —
nothing is added automatically. Every candidate is independently
researched and classified (platform, purpose, tier) before it's added
to a category file, the same as any other domain in this project.

Sources checked for new-domain signals:
[AdGuard SDNS Filter](https://github.com/AdguardTeam/AdGuardSDNSFilter),
[StevenBlack](https://github.com/StevenBlack/hosts),
[EasyPrivacy](https://github.com/easylist/easylist),
[1Hosts](https://github.com/badmojr/1Hosts),
[no-google](https://github.com/nickspaargaren/no-google), and
[hagezi/dns-blocklists](https://github.com/hagezi/dns-blocklists)

## Contributing

Reports of false positives, missing domains, or new platform research
are welcome. See [`CONTRIBUTING.md`](CONTRIBUTING.md).

## License

[MIT](LICENSE)
