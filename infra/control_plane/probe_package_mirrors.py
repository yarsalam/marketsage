#!/usr/bin/env python3
"""Probe candidate Python Simple API mirrors without installing packages.

Uses stdlib only, requires HTTPS for initial URLs and redirects, sends no
credentials, and prints HTTP status/latency/package-page visibility. It does
not download distributions.
"""
from __future__ import annotations

import sys
import time
import urllib.error
import urllib.request
from urllib.parse import urlsplit

MIRRORS = (
    ("novin", "https://mirror.novin.cloud/artifactory/api/pypi/pypi/simple/"),
    ("chabokan", "https://mirror2.chabokan.net/pypi/simple/"),
    ("hyperclouds", "https://pypi.hyperclouds.ir/simple/"),
)
PACKAGES = ("jsonschema", "jsonschema-specifications", "rpds-py", "attrs")
TIMEOUT_SECONDS = 12
USER_AGENT = "MarketSage-Package-Mirror-Probe/1.2"


class HTTPSOnlyRedirectHandler(urllib.request.HTTPRedirectHandler):
    """Reject insecure redirects and cap each package page at one redirect."""

    max_redirections = 1
    max_repeats = 1

    def redirect_request(self, req, fp, code, msg, headers, newurl):
        target = urlsplit(newurl)
        if (
            target.scheme.lower() != "https"
            or not target.hostname
            or target.username is not None
            or target.password is not None
        ):
            raise urllib.error.URLError("unsafe redirect blocked")
        return super().redirect_request(req, fp, code, msg, headers, newurl)


def probe(url: str) -> tuple[int | None, float, str]:
    started = time.monotonic()
    target = urlsplit(url)
    if (
        target.scheme.lower() != "https"
        or not target.hostname
        or target.username is not None
        or target.password is not None
    ):
        return None, time.monotonic() - started, "HTTPS_REQUIRED"

    request = urllib.request.Request(
        url,
        headers={"User-Agent": USER_AGENT, "Accept": "text/html"},
        method="GET",
    )
    opener = urllib.request.build_opener(HTTPSOnlyRedirectHandler())
    try:
        # urllib's default HTTPSHandler retains certificate verification.
        with opener.open(request, timeout=TIMEOUT_SECONDS) as response:
            response.read(2048)
            return response.status, time.monotonic() - started, ""
    except urllib.error.HTTPError as exc:
        return exc.code, time.monotonic() - started, f"HTTP {exc.code}"
    except Exception as exc:  # Never echo response bodies, URLs or exception text.
        return None, time.monotonic() - started, type(exc).__name__


def main() -> int:
    failures = 0
    print(
        "TLS verification: enabled; HTTPS only; max one redirect/page; credentials: none; "
        "install/download: no"
    )
    for name, base in MIRRORS:
        print(f"\n[{name}] {base}")
        for package in PACKAGES:
            status, elapsed, error = probe(f"{base}{package}/")
            state = f"HTTP {status}" if status is not None else f"ERROR {error}"
            print(f"  {package}: {state}; {elapsed:.2f}s")
            if status != 200:
                failures += 1
    print(f"\nNon-200 package pages: {failures}")
    return 0 if failures == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
