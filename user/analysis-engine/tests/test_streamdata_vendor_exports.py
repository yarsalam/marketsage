from __future__ import annotations

import csv
import importlib.util
from pathlib import Path

SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "audit_streamdata_vendor_exports.py"
SPEC = importlib.util.spec_from_file_location("audit_streamdata_vendor_exports", SCRIPT)
assert SPEC and SPEC.loader
audit_module = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(audit_module)
audit_exports = audit_module.audit_exports

FILES = {
    "gold_fund_ayar": "Ayar_Gold_Fund_1D_StreamData.csv",
    "bitcoin_btcusdt": "BTCUSDT_1D_StreamData.csv",
    "gold_18k": "Gold18_1D_StreamData.csv",
    "free_usd": "US_Dollar_1D_StreamData.csv",
}
HEADER = "<DTYYYYMMDD>,<TIME>,<OPEN>,<HIGH>,<LOW>,<CLOSE>,<VOL>\n"


def write_export(path: Path, body: str) -> None:
    path.write_text(HEADER + body, encoding="utf-8")


def test_audits_streamdata_export_without_guessing_units_or_timezone(tmp_path):
    data_dir = tmp_path / "input"
    out_dir = tmp_path / "out"
    data_dir.mkdir()
    rows = (
        "20261015,033000,100,120,90,110,1000\n"
        "20261016,033000,110,130,100,125,1200\n"
        # The third row intentionally has close > high and must be flagged, not fixed.
        "20261017,033000,125,126,120,129,900\n"
    )
    for key, filename in FILES.items():
        write_export(data_dir / filename, rows if key == "gold_fund_ayar" else
                     "20261015,033000,100,120,90,110,1000\n"
                     "20261016,033000,110,130,100,125,1200\n")

    report = audit_exports(data_dir, out_dir)
    item = report["assets"]["gold_fund_ayar"]

    assert item["row_count"] == 3
    assert item["ohlc_consistency_anomaly_rows"] == 1
    assert item["rows_with_missing_or_non_numeric_or_nonpositive_ohlc"] == 0
    assert item["eligible_for_scoring"] is False
    assert item["source_price_unit"] is None
    assert item["source_currency"] is None
    assert item["timezone"] is None
    assert report["policy"]["missing_dates_filled"] is False
    assert report["policy"]["unit_and_currency_inferred"] is False

    output = out_dir / "gold_fund_ayar.candidate.csv"
    with output.open("r", encoding="utf-8", newline="") as handle:
        parsed = list(csv.DictReader(handle))
    bad = parsed[2]
    assert bad["close_raw"] == "129"
    assert bad["ohlc_consistency_ok"] == "false"
    assert bad["eligible_for_scoring"] == "false"
    assert bad["source_price_unit"] == ""


def test_missing_vendor_file_is_reported_and_never_approved(tmp_path):
    data_dir = tmp_path / "empty"
    data_dir.mkdir()
    report = audit_exports(data_dir, tmp_path / "out")

    assert all(item["status"] == "missing_file" for item in report["assets"].values())
    assert all(item["eligible_for_scoring"] is False for item in report["assets"].values())


def test_rejects_invalid_large_return_threshold(tmp_path):
    try:
        audit_exports(tmp_path, tmp_path / "out", large_return_threshold=0)
    except ValueError as exc:
        assert "large_return_threshold" in str(exc)
    else:
        raise AssertionError("invalid threshold should be rejected")
