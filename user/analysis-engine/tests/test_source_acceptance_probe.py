from gdelt_news_provider import GdeltError
from fred_alfred_provider import FredProviderError
from scripts.probe_source_acceptance_pack import (
    SOURCE_IDS,
    parse_source_selection,
    safe_error_detail,
)


def test_gdelt_safe_error_detail_is_available_for_sanitized_provider_errors():
    error = GdeltError("GDELT request failed (HTTP 429)")
    assert safe_error_detail("global.gdelt_doc_api", error) == (
        "GDELT request failed (HTTP 429)"
    )


def test_probe_does_not_expose_arbitrary_exception_details():
    error = RuntimeError("https://example.invalid/?token=must-not-leak")
    assert safe_error_detail("global.gdelt_doc_api", error) is None
    assert safe_error_detail("iran.codal", GdeltError("internal detail")) is None


def test_source_selection_can_limit_probe_to_one_source():
    assert parse_source_selection(["--source", "iran.codal"]) == {"iran.codal"}


def test_source_selection_can_include_multiple_sources():
    assert parse_source_selection([
        "--source", "iran.codal", "--source", "iran.tsetmc"
    ]) == {"iran.codal", "iran.tsetmc"}


def test_source_selection_defaults_to_full_pack():
    assert parse_source_selection([]) == set(SOURCE_IDS)



def test_fred_safe_error_detail_only_exposes_sanitized_provider_errors():
    error = FredProviderError("FRED network timeout (ConnectTimeout); no automatic retry was made")
    assert safe_error_detail("us.fred.alfred", error) == str(error)
    arbitrary = RuntimeError("api_key=must-not-leak")
    assert safe_error_detail("us.fred.alfred", arbitrary) is None
