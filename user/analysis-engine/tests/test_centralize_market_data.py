from __future__ import annotations

import importlib.util
from pathlib import Path

import pytest


SCRIPT_PATH = Path(__file__).resolve().parents[1] / "scripts" / "centralize_market_data.py"
SPEC = importlib.util.spec_from_file_location("centralize_market_data", SCRIPT_PATH)
assert SPEC is not None and SPEC.loader is not None
centralizer = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(centralizer)


def test_sync_tree_copies_and_is_idempotent(tmp_path: Path) -> None:
    source = tmp_path / "source"
    destination = tmp_path / "destination"
    (source / "nested").mkdir(parents=True)
    (source / "nested" / "prices.csv").write_text("date,close\n2026-01-01,100\n", encoding="utf-8")

    first = centralizer.sync_tree(source, destination)
    assert first["status"] == "copied_and_verified"
    assert first["copied_count"] == 1
    assert first["file_count"] == 1
    assert (destination / "nested" / "prices.csv").read_text(encoding="utf-8") == (
        "date,close\n2026-01-01,100\n"
    )

    second = centralizer.sync_tree(source, destination)
    assert second["status"] == "already_current"
    assert second["copied_count"] == 0
    assert second["already_present_count"] == 1


def test_sync_tree_refuses_to_overwrite_conflicting_destination(tmp_path: Path) -> None:
    source = tmp_path / "source"
    destination = tmp_path / "destination"
    source.mkdir()
    destination.mkdir()
    (source / "same.csv").write_text("close\n100\n", encoding="utf-8")
    (destination / "same.csv").write_text("close\n999\n", encoding="utf-8")

    with pytest.raises(centralizer.DataConflictError):
        centralizer.sync_tree(source, destination)

    assert (destination / "same.csv").read_text(encoding="utf-8") == "close\n999\n"


def test_sync_tree_reports_missing_source_without_deleting_destination(tmp_path: Path) -> None:
    missing_source = tmp_path / "not-there"
    destination = tmp_path / "destination"
    destination.mkdir()
    sentinel = destination / "keep.txt"
    sentinel.write_text("preserve", encoding="utf-8")

    result = centralizer.sync_tree(missing_source, destination)

    assert result["status"] == "source_missing"
    assert sentinel.read_text(encoding="utf-8") == "preserve"
