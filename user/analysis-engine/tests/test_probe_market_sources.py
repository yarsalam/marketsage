from __future__ import annotations

import importlib.util
from pathlib import Path

SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "probe_market_sources.py"
SPEC = importlib.util.spec_from_file_location("probe_market_sources", SCRIPT)
assert SPEC and SPEC.loader
probe = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(probe)


def test_json_shape_reports_metadata_without_payload():
    result = probe.shape_info(b'{"data":[{"secret":"do-not-copy"}]}', "application/json", "json")
    assert result["shape_valid"] is True
    assert result["row_count"] == 1
    assert "secret" not in str(result)


def test_invalid_json_is_rejected():
    result = probe.shape_info(b"not json", "text/plain", "json")
    assert result["shape_valid"] is False


def test_html_shape_requires_nonempty_body():
    assert probe.shape_info(b"<html>ok</html>", "text/html", "html")["shape_valid"] is True
    assert probe.shape_info(b"", "text/html", "html")["shape_valid"] is False


def test_tindex_is_skipped_when_not_configured(monkeypatch):
    monkeypatch.delenv("TINDEX_API_BASE_URL", raising=False)
    monkeypatch.delenv("TINDEX_API_TOKEN", raising=False)
    spec = {"url_env": "TINDEX_API_BASE_URL", "path": "/api/public/currency-rates"}
    assert probe.safe_url(spec) == (None, "not_configured")


def test_tindex_requires_both_origin_and_token(monkeypatch):
    monkeypatch.setenv("TINDEX_API_BASE_URL", "https://tindex.app")
    monkeypatch.delenv("TINDEX_API_TOKEN", raising=False)
    spec = {"url_env": "TINDEX_API_BASE_URL", "path": "/api/public/currency-rates"}
    assert probe.safe_url(spec) == (None, "incomplete_credentials")


def test_tindex_rejects_origin_with_path(monkeypatch):
    monkeypatch.setenv("TINDEX_API_BASE_URL", "https://tindex.app/some/path")
    monkeypatch.setenv("TINDEX_API_TOKEN", "test-token-not-real")
    spec = {"url_env": "TINDEX_API_BASE_URL", "path": "/api/public/currency-rates"}
    assert probe.safe_url(spec) == (None, "invalid_origin_config")


def test_tindex_constructs_url_without_exposing_token(monkeypatch):
    monkeypatch.setenv("TINDEX_API_BASE_URL", "https://tindex.app/")
    monkeypatch.setenv("TINDEX_API_TOKEN", "test-token-not-real")
    spec = {"url_env": "TINDEX_API_BASE_URL", "path": "/api/public/currency-rates"}
    url, error = probe.safe_url(spec)
    assert error is None
    assert url == "https://tindex.app/api/public/currency-rates"
    assert "test-token-not-real" not in str(url)
