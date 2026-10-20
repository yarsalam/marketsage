import subprocess
from pathlib import Path

import pytest


ENGINE_DIR = Path(__file__).resolve().parents[1]
RUNNER = ENGINE_DIR / "scripts" / "run_free_dataset_acceptance_pack.sh"


def run_runner(*args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["bash", str(RUNNER), *args],
        cwd=ENGINE_DIR,
        check=False,
        capture_output=True,
        text=True,
        timeout=5,
    )


def test_runner_refuses_mixed_vpn_groups_before_network_access():
    result = run_runner("--live-iran", "--live-foreign")
    assert result.returncode == 2
    assert "Refusing to mix Iranian and foreign providers" in result.stderr


@pytest.mark.parametrize(
    ("option", "required_group"),
    [
        ("--include-tindex", "--live-iran"),
        ("--include-fred", "--live-foreign"),
        ("--include-gdelt", "--live-foreign"),
        ("--tsetmc-query", "--live-iran"),
    ],
)
def test_runner_requires_provider_group_for_optional_probe_options(
    option: str, required_group: str
):
    args = [option]
    if option == "--tsetmc-query":
        args.append("فولاد")
    result = run_runner(*args)
    assert result.returncode == 2
    assert required_group in result.stderr


def test_runner_rejects_offline_and_live_modes_together():
    result = run_runner("--offline-only", "--live-foreign")
    assert result.returncode == 2
    assert "--offline-only cannot be combined" in result.stderr


def test_runner_requires_tindex_slug_option_to_be_in_guarded_tindex_mode():
    result = run_runner("--live-iran", "--tindex-slug", "GOLD-18K")
    assert result.returncode == 2
    assert "--tindex-slug requires --include-tindex" in result.stderr


def test_runner_rejects_tindex_slug_without_iran_group():
    result = run_runner("--tindex-slug", "GOLD-18K")
    assert result.returncode == 2
    assert "--tindex-slug requires --include-tindex" in result.stderr
