"""Reproducibility metadata helpers for local research runs."""
from __future__ import annotations

import hashlib
import subprocess
from pathlib import Path


def sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def capture_git_provenance(repository_root: Path) -> dict:
    """Capture the exact code commit and whether the working tree is reproducible.

    The status digest avoids placing local file names or paths in reports.
    Raises RuntimeError when the run is not inside a readable Git repository.
    """
    root = repository_root.expanduser().resolve()
    try:
        commit_result = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            cwd=root,
            check=True,
            capture_output=True,
            text=True,
        )
        status_result = subprocess.run(
            ["git", "status", "--porcelain", "--untracked-files=normal"],
            cwd=root,
            check=True,
            capture_output=True,
            text=True,
        )
    except (OSError, subprocess.CalledProcessError) as exc:
        raise RuntimeError(f"cannot capture Git provenance: {exc}") from exc

    commit = commit_result.stdout.strip()
    status = status_result.stdout
    if len(commit) != 40 or any(char not in "0123456789abcdef" for char in commit):
        raise RuntimeError("git rev-parse did not return a full lowercase commit SHA")

    entries = [line for line in status.splitlines() if line.strip()]
    return {
        "code_commit": commit,
        "git_worktree_clean": not entries,
        "git_status_sha256": sha256_bytes(status.encode("utf-8")),
        "git_status_entry_count": len(entries),
    }
