from datetime import datetime, timezone

import pytest

from codal_adapter import CODALDataError, parse_search_xml
from source_registry import source_scoring_gate
from temporal_data import PointInTimeStore


XML = """<?xml version="1.0" encoding="utf-8"?>
<ArrayOfCodalLetterHeaderDto>
  <CodalLetterHeaderDto>
    <TracingNo>1234567</TracingNo>
    <Symbol>فولاد</Symbol>
    <Title>گزارش فعالیت ماهانه</Title>
    <LetterCode>ن-۱۰</LetterCode>
    <PublishDateTime>۱۴۰۵/۰۷/۲۴ ۱۲:۲۶:۳۱</PublishDateTime>
    <SentDateTime>۱۴۰۵/۰۷/۲۴ ۱۲:25:00</SentDateTime>
    <Url>/Reports/Decision.aspx?LetterSerial=abc</Url>
  </CodalLetterHeaderDto>
</ArrayOfCodalLetterHeaderDto>"""


def test_parse_codal_keeps_source_time_untrusted_and_quarantines_record():
    captured = datetime(2026, 10, 16, 12, tzinfo=timezone.utc)
    records = parse_search_xml(XML, retrieved_at=captured)
    assert len(records) == 1
    record = records[0]
    assert record.record_key == "فولاد:1234567"
    assert record.source_id == "iran.codal"
    assert record.published_at is None
    assert record.observed_at == captured
    assert record.payload["publish_datetime_source_text"] == "۱۴۰۵/۰۷/۲۴ ۱۲:۲۶:۳۱"
    assert record.payload["normalization_status"] == "candidate_quarantined"
    assert source_scoring_gate("iran.codal")["eligible_for_production_scoring"] is False


@pytest.mark.parametrize("payload", ["", "<broken>", "<root><x>no letters</x></root>"])
def test_rejects_invalid_or_empty_search_responses(payload):
    with pytest.raises(CODALDataError):
        parse_search_xml(payload, retrieved_at=datetime.now(timezone.utc))


def test_requires_timezone_aware_retrieval_time():
    with pytest.raises(CODALDataError, match="timezone-aware"):
        parse_search_xml(XML, retrieved_at=datetime(2026, 10, 16))


def test_rejects_duplicate_tracing_numbers():
    entry = XML[XML.index("<CodalLetterHeaderDto>"):XML.index("</ArrayOfCodalLetterHeaderDto>")]
    duplicate = XML.replace("</ArrayOfCodalLetterHeaderDto>", entry + "</ArrayOfCodalLetterHeaderDto>")
    with pytest.raises(CODALDataError, match="duplicate TracingNo"):
        parse_search_xml(duplicate, retrieved_at=datetime.now(timezone.utc))


def test_rejects_missing_identity_fields():
    bad = XML.replace("<TracingNo>1234567</TracingNo>", "<TracingNo>x</TracingNo>")
    with pytest.raises(CODALDataError, match="TracingNo"):
        parse_search_xml(bad, retrieved_at=datetime.now(timezone.utc))


def test_candidate_records_can_be_stored_without_becoming_scoring_eligible(tmp_path):
    store = PointInTimeStore(tmp_path / "codal.sqlite3")
    records = parse_search_xml(XML, retrieved_at=datetime.now(timezone.utc))
    store.append(records[0])
    assert store.summary()["record_versions"] == 1
    assert source_scoring_gate("iran.codal")["eligible_for_production_scoring"] is False
