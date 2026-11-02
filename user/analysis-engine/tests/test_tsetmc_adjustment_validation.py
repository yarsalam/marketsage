from __future__ import annotations

import sys
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parents[1] / "scripts"
sys.path.insert(0, str(SCRIPT_DIR))

from validate_tsetmc_adjustments import extract_list, parse_chart


def test_parse_chart_keeps_raw_positional_fields_and_keys_by_date():
    parsed = parse_chart("20201108,12000,11600,11800,11700,1234,11700;20201109,12100,11700,12000,12050,456,12050;")
    assert parsed["20201108"] == ["20201108", "12000", "11600", "11800", "11700", "1234", "11700"]
    assert parsed["20201109"][4] == "12050"


def test_parse_chart_skips_empty_and_malformed_rows():
    assert parse_chart(";bad,row;2020,1;") == {}


def test_extract_list_uses_expected_wrapper_key():
    assert extract_list({"priceAdjust": [{"dEven": 20201108}, "bad"]}, "priceAdjust") == [
        {"dEven": 20201108}
    ]


def test_extract_list_does_not_guess_an_arbitrary_nested_list():
    assert extract_list({"unexpected": [{"dEven": 20201108}]}, "priceAdjust") == []
