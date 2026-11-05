import hashlib
import subprocess
from pathlib import Path

import pytest

from research.provenance import capture_git_provenance


def test_capture_git_provenance_records_clean_revision(monkeypatch, tmp_path):
    responses = [
        subprocess.CompletedProcess(["git", "rev-parse", "HEAD"], 0, "a" * 40 + "\n", ""),
        subprocess.CompletedProcess(["git", "status", "--porcelain"], 0, "", ""),
    ]

    def fake_run(*args, **kwargs):
        assert kwargs["cwd"] == tmp_path.resolve()
        return responses.pop(0)

    monkeypatch.setattr("research.provenance.subprocess.run", fake_run)
    result = capture_git_provenance(tmp_path)

    assert result["code_commit"] == "a" * 40
    assert result["git_worktree_clean"] is True
    assert result["git_status_entry_count"] == 0
    assert result["git_status_sha256"] == hashlib.sha256(b"").hexdigest()


def test_capture_git_provenance_hashes_dirty_status_without_exposing_paths(monkeypatch, tmp_path):
    status = " M private_prices.csv\n?? local-output/\n"
    responses = [
        subprocess.CompletedProcess(["git", "rev-parse", "HEAD"], 0, "c" * 40 + "\n", ""),
        subprocess.CompletedProcess(["git", "status", "--porcelain"], 0, status, ""),
    ]

    def fake_run(*args, **kwargs):
        return responses.pop(0)

    monkeypatch.setattr("research.provenance.subprocess.run", fake_run)
    result = capture_git_provenance(tmp_path)

    assert result["git_worktree_clean"] is False
    assert result["git_status_entry_count"] == 2
    assert result["git_status_sha256"] == hashlib.sha256(status.encode()).hexdigest()
    assert "private_prices.csv" not in str(result)
    assert "local-output" not in str(result)


def test_capture_git_provenance_rejects_invalid_commit(monkeypatch, tmp_path):
    responses = [
        subprocess.CompletedProcess(["git", "rev-parse", "HEAD"], 0, "not-a-sha\n", ""),
        subprocess.CompletedProcess(["git", "status", "--porcelain"], 0, "", ""),
    ]

    def fake_run(*args, **kwargs):
        return responses.pop(0)

    monkeypatch.setattr("research.provenance.subprocess.run", fake_run)
    with pytest.raises(RuntimeError, match="full lowercase commit SHA"):
        capture_git_provenance(tmp_path)
