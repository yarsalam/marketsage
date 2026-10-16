import json

import data_quality_report as report


def test_report_warns_for_stale_series_and_ignores_unconnected_candidates():
    payload = {
        "sources": [
            {
                "source_id": "global.yahoo_finance.yfinance",
                "used_by_research_engine": True,
                "runtime_status": "data_present",
                "runtime_series": [
                    {"series_key": "SPY", "freshness": "stale"},
                    {"series_key": "BTC-USD", "freshness": "fresh"},
                ],
            },
            {
                "source_id": "iran.tsetmc",
                "used_by_research_engine": False,
                "runtime_status": "no_data_captured",
                "runtime_series": [],
            },
        ]
    }

    result = report.build_report(payload, generated_at="2026-10-16T00:00:00+00:00")

    assert result["status"] == "warning"
    assert result["warning_count"] == 1
    assert result["critical_count"] == 0
    assert result["alerts"][0]["code"] == "series_stale"
    assert result["alerts"][0]["series_key"] == "SPY"


def test_report_raises_critical_if_research_source_has_no_data():
    result = report.build_report({
        "sources": [{
            "source_id": "global.yahoo_finance.yfinance",
            "used_by_research_engine": True,
            "runtime_status": "no_data_captured",
            "runtime_series": [],
        }]
    })

    assert result["status"] == "critical"
    assert result["critical_count"] == 1
    assert result["alerts"][0]["code"] == "research_source_has_no_captured_data"


def test_report_warns_when_series_freshness_is_unknown():
    result = report.build_report({
        "sources": [{
            "source_id": "global.yahoo_finance.yfinance",
            "used_by_research_engine": True,
            "runtime_status": "data_present",
            "runtime_series": [{"series_key": "SPY", "freshness": "unknown"}],
        }]
    })

    assert result["status"] == "warning"
    assert result["alerts"][0]["code"] == "series_freshness_unknown"


def test_report_rejects_missing_sources_array():
    try:
        report.build_report({})
    except ValueError as exc:
        assert "sources list" in str(exc)
    else:
        raise AssertionError("Expected invalid payload to be rejected")


def test_cli_writes_atomic_json_report_and_returns_warning(monkeypatch, tmp_path, capsys):
    monkeypatch.setattr(report, "fetch_payload", lambda url, timeout: {
        "sources": [{
            "source_id": "global.yahoo_finance.yfinance",
            "used_by_research_engine": True,
            "runtime_status": "data_present",
            "runtime_series": [{"series_key": "SPY", "freshness": "stale"}],
        }]
    })
    output = tmp_path / "reports" / "quality.json"

    code = report.main(["--url", "http://example.test/data-quality", "--output", str(output)])

    assert code == 1
    saved = json.loads(output.read_text(encoding="utf-8"))
    assert saved["status"] == "warning"
    assert json.loads(capsys.readouterr().out)["status"] == "warning"
    assert not output.with_suffix(".json.tmp").exists()


def test_cli_returns_configuration_error_without_url(monkeypatch, capsys):
    monkeypatch.delenv("MARKET_SAGE_DATA_QUALITY_URL", raising=False)

    assert report.main([]) == 3
    assert "MARKET_SAGE_DATA_QUALITY_URL" in capsys.readouterr().err
