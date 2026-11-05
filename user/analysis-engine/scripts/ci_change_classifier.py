#!/usr/bin/env python3
"""Classify changed repository paths into bounded MarketSage CI jobs."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Iterable

JOB_KEYS = ("analysis", "backend", "frontend", "admin", "production")
SHARED_FILES = {
    ".npmrc",
    "package.json",
    "pnpm-lock.yaml",
    "pnpm-workspace.yaml",
    "pnpmfile.cjs",
    "tsconfig.base.json",
}


def normalize_path(value: str) -> str:
    path = value.strip().replace("\\", "/")
    while path.startswith("./"):
        path = path[2:]
    return path.rstrip("/")


def classify_paths(paths: Iterable[str]) -> dict[str, bool]:
    normalized = sorted({normalize_path(path) for path in paths if normalize_path(path)})
    if not normalized:
        return {key: False for key in JOB_KEYS}

    if any(path.startswith(".github/workflows/") or path in SHARED_FILES for path in normalized):
        return {key: True for key in JOB_KEYS}

    analysis = False
    backend = False
    frontend = False
    admin = False
    production = False

    for path in normalized:
        if (
            path.startswith(("user/analysis-engine/", "docs/", "scripts/"))
            or path in {"README.md", "pyproject.toml", "pytest.ini", "requirements.txt"}
            or path.startswith("requirements")
        ):
            analysis = True

        if path.startswith("user/user-backend/"):
            backend = True
        if path.startswith("user/user-frontend/"):
            frontend = True
        if path.startswith("admin-panel/"):
            admin = True

        name = Path(path).name
        if (
            path.startswith("deploy/")
            or name == "Dockerfile"
            or name == ".dockerignore"
            or name in {".env.production.example", ".env.staging.example"}
            or (name.startswith("docker-compose") and name.endswith((".yml", ".yaml")))
        ):
            production = True

    flags = {
        "analysis": analysis,
        "backend": backend,
        "frontend": frontend,
        "admin": admin,
        "production": production,
    }

    # Unknown paths fail open to full CI; a new repository area must not be
    # silently excluded from validation by an incomplete path map.
    if not any(flags.values()):
        return {key: True for key in JOB_KEYS}
    return flags


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--files-file", type=Path)
    parser.add_argument("--github-output", type=Path)
    parser.add_argument("--all", action="store_true", help="run every CI job when the base SHA is unavailable")
    args = parser.parse_args()

    if args.all:
        flags = {key: True for key in JOB_KEYS}
    else:
        if args.files_file is None:
            parser.error("--files-file is required unless --all is supplied")
        flags = classify_paths(args.files_file.read_text(encoding="utf-8").splitlines())

    if args.github_output:
        with args.github_output.open("a", encoding="utf-8") as handle:
            for key in JOB_KEYS:
                handle.write(f"{key}={'true' if flags[key] else 'false'}\n")
    else:
        print(json.dumps(flags, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
