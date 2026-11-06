# Python package mirror strategy for zero-cost bootstrap

**Status:** candidate strategy; endpoint reachability from the owner's network is not yet verified.
**Scope:** Python dependency installation for infrastructure tooling and future isolated workers.
**Policy:** zero cost, no credentials, no insecure TLS bypass, no global pip configuration changes.

## Why this is now part of the bootstrap path

The 2026-11-06 validation attempt stopped before tests because pip timed out while reading PyPI metadata and then reported a resolver conflict involving `jsonschema` and transitive `rpds-py`. No tests ran. A domestic package mirror may remove the network bottleneck, but it must be probed from the actual execution network before being trusted.

## Candidate order

1. **Novin Cloud PyPI mirror** — documented endpoint:
   `https://mirror.novin.cloud/artifactory/api/pypi/pypi/simple/`
   Vendor documentation describes a public, unauthenticated mirror. Treat that as a vendor claim until independently probed.
2. **Chabokan PyPI mirror** — candidate endpoint:
   `https://mirror2.chabokan.net/pypi/simple/`
   Listed by Iranian developer resources; endpoint availability and package completeness must be tested.
3. **HyperClouds PyPI mirror** — candidate endpoint:
   `https://pypi.hyperclouds.ir/simple/`
   Listed by community mirror catalogs; verify TLS, freshness and package coverage before use.

Do not assume these endpoints are interchangeable, complete, always free, or reachable from every ISP. Jamko/ITO repository endpoints are additional research candidates, but must not be added until an exact current PyPI simple-index URL and its operational ownership are verified.

## Probe before installing

The probe script `infra/control_plane/probe_package_mirrors.py` checks only the Simple API package pages for:
- `jsonschema`
- `jsonschema-specifications`
- `rpds-py`
- `attrs`

It uses standard TLS certificate verification, bounded timeouts and no credentials. It does not install packages, execute downloaded code, alter pip configuration or transmit project data. Record HTTP status, latency and whether each package page is discoverable. A successful page response does not prove that every compatible wheel is present; the actual wheel download/install remains a separate acceptance check.

## Safe install policy

- Use a per-command `--index-url` or a temporary isolated pip configuration. Do not modify global `pip.conf` as the first step.
- Do not use `--trusted-host`, `--break-system-packages`, disable certificate checks, or fall back silently to an untrusted index.
- Do not combine an internal mirror and public PyPI using `--extra-index-url` for this private build: pip's index selection can create dependency-confusion exposure. Select one explicitly verified index for each run.
- Keep dependency constraints reviewed and reproducible. Do not loosen constraints just to force resolution.
- Prefer pinned versions and, when practical, a hash-locked requirements file / verified wheelhouse. A mirror is a transport/cache, not a trust root for package integrity.
- If the first mirror lacks a package, record the exact missing distribution and test the next candidate explicitly. Never silently install a similarly named package.
- Never put credentials, private repository URLs, source code, raw market data or secrets in mirror requests.

## Acceptance gate

A mirror is eligible for the infrastructure bootstrap only after:
1. DNS and TLS validation succeed from the actual worker network.
2. All required package pages respond successfully.
3. Compatible wheels for the worker's Python version and architecture are available (or a reviewed source-build toolchain is available).
4. The exact locked dependency set installs in a clean isolated environment.
5. The manifest and lifecycle unittest modules run and their exit code/test count are recorded against an immutable commit SHA.

Until those checks pass, classify the blocker as package-mirror/bootstrap availability, not a code/test failure. Keep GitHub Actions dispatch disabled and the cost ceiling at zero.

## References checked 2026-11-06

- Novin Cloud mirror documentation: https://docs.novin.cloud/en/mirrors/about/
- Novin Cloud endpoint and pip usage: https://novin.cloud/blog/pip-mirror-iran
- Chabokan candidate endpoint: https://howsam.org/install-python-packages-without-internet/comment-page-1/
- Community catalog for Iranian mirrors: https://github.com/MiravaOrg/Mirava/blob/main/README.fa.md

These references identify candidates; they are not uptime, completeness, security-audit or SLA guarantees.
