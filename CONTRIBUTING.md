# Contributing

This repository is maintained by a single person. Community
suggestions are welcome, but all additions and changes are reviewed
and applied by the maintainer — pull requests that edit `lists/` or
`research/` directly will generally not be merged as-is.

## Reporting a false positive

Open an issue with:
- The domain
- The platform/app it belongs to
- Why you believe it affects core functionality (not just telemetry)

Confirmed false positives are removed promptly.

## Suggesting a domain for an existing category

Open an issue with:
- The domain
- The platform/app and category it belongs to
- How you identified it as tracking-related (and whether it should be
  aggressive-only)

## Suggesting a new category or platform

Open an issue with:
- The platform(s) you researched
- The domains you believe are tracking-related, and why
- Any supporting material (documentation, network traces, etc.)

If accepted, the maintainer will add the domains to
[`lists/categories/`](lists/categories/) and the supporting material
to [`research/`](research/).

## Style reference

For context, entries follow this format — one domain per line, no
wildcards or protocol prefixes, with `!` marking aggressive-only
domains
