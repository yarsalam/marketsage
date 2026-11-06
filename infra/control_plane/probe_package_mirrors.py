#!/usr/bin/env python3
"""Probe candidate Python Simple API mirrors without installing packages.

Uses stdlib only, rejects HTTPS-to-HTTP redirect downgrades, sends no
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
USER_AGENT = "MarketSage-Package-Mirror-Probe/1.1"


class HTTPSOnlyRedirectHandler(urllib.request.HTTPRedirectHandler):
    """Reject redirects that would downgrade a request from HTTPS to HTTP."""

    def redirect_request(self, req, fp, code, msg, headers, newurl):
        if urlsplit(newurl).scheme.lower() != "https":
            raise urllib.error.URLError("non-https redirect blocked")
        return super().redirect_request(req, fp, code, msg, headers, newurl)


def probe(url: str) -> tuple[int | None, float, str]:
    request = urllib.request.Request(
        url,
        headers={"User-Agent": USER_AGENT, "Accept": "text/html"},
        method="GET",
    )
    started = time.monotonic()
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
        "TLS verification: enabled; HTTPS redirects only; credentials: none; "
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
