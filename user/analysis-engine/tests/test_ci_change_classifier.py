from __future__ import annotations

import subprocess
import sys
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parents[1] / "scripts"
sys.path.insert(0, str(SCRIPT_DIR))

from ci_change_classifier import JOB_KEYS, classify_paths  # noqa: E402


def test_docs_only_runs_analysis_validation() -> None:
    result = classify_paths(["docs/iran-property-auto-candidate-screen-2026-11.md"])
    assert result == {
        "analysis": True,
        "backend": False,
        "frontend": False,
        "admin": False,
        "production": False,
    }


def test_workspace_change_runs_only_its_workspace() -> None:
    result = classify_paths(["user/user-backend/src/main.ts"])
    assert result == {
        "analysis": False,
        "backend": True,
        "frontend": False,
        "admin": False,
        "production": False,
    }


def test_shared_workflow_change_runs_all_jobs() -> None:
    result = classify_paths([".github/workflows/ci.yml"])
    assert all(result[key] for key in JOB_KEYS)


def test_root_lockfile_runs_all_jobs() -> None:
    result = classify_paths(["pnpm-lock.yaml"])
    assert all(result[key] for key in JOB_KEYS)


def test_production_config_only_runs_image_validation() -> None:
    result = classify_paths(["docker-compose.production.yml"])
    assert result == {
        "analysis": False,
        "backend": False,
        "frontend": False,
        "admin": False,
        "production": True,
    }


def test_unknown_path_fails_open_to_full_ci() -> None:
    result = classify_paths(["new-root-area/config.toml"])
    assert all(result[key] for key in JOB_KEYS)


def test_empty_diff_skips_all_optional_jobs() -> None:
    result = classify_paths([])
    assert not any(result.values())


def test_cli_writes_github_outputs(tmp_path: Path) -> None:
    files = tmp_path / "changed.txt"
    output = tmp_path / "github-output.txt"
    files.write_text("docs/README.md\n", encoding="utf-8")

    subprocess.run(
        [
            sys.executable,
            str(SCRIPT_DIR / "ci_change_classifier.py"),
            "--files-file",
            str(files),
            "--github-output",
            str(output),
        ],
        check=True,
    )

    values = dict(line.split("=", 1) for line in output.read_text(encoding="utf-8").splitlines())
    assert values["analysis"] == "true"
    assert values["production"] == "false"
