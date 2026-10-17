from gdelt_news_provider import GdeltError
from scripts.probe_source_acceptance_pack import safe_error_detail


def test_gdelt_safe_error_detail_is_available_for_sanitized_provider_errors():
    error = GdeltError("GDELT request failed (HTTP 429)")
    assert safe_error_detail("global.gdelt_doc_api", error) == (
        "GDELT request failed (HTTP 429)"
    )


def test_probe_does_not_expose_arbitrary_exception_details():
    error = RuntimeError("https://example.invalid/?token=must-not-leak")
    assert safe_error_detail("global.gdelt_doc_api", error) is None
    assert safe_error_detail("iran.codal", GdeltError("internal detail")) is None
