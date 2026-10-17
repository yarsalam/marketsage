import httpx
import pytest

from gdelt_news_provider import GdeltDocClient, GdeltError, GdeltPayloadError, normalize_gdelt_articles


def test_search_uses_doc_api_and_normalizes_without_inventing_publication_time():
    def handler(request):
        assert request.url.host == "api.gdeltproject.org"
        assert request.url.path == "/api/v2/doc/doc"
        assert request.url.params["mode"] == "ArtList"
        assert request.url.params["format"] == "json"
        assert request.url.params["maxrecords"] == "20"
        assert request.url.params["startdatetime"] == "20261016000000"
        return httpx.Response(200, json={"articles": [{
            "url": "HTTPS://EXAMPLE.COM/news?id=1#fragment",
            "title": "Central bank announces rate decision",
            "domain": "example.com",
            "language": "English",
            "sourcecountry": "United States",
            "seendate": "20261016T103000",
        }]})
    with GdeltDocClient(transport=httpx.MockTransport(handler)) as client:
        rows = client.search_articles("central bank", max_records=20, start_datetime="20261016000000")
    assert len(rows) == 1
    assert rows[0]["url"] == "https://example.com/news?id=1"
    assert rows[0]["first_seen_at"] == "2026-10-16T10:30:00"
    assert rows[0]["publisher_published_at"] is None
    assert rows[0]["sentiment"] is None
    assert rows[0]["political_event_type"] is None
    assert rows[0]["verified"] is False
    assert rows[0]["eligible_for_scoring"] is False


def test_deduplicates_canonical_urls_and_drops_malformed_rows():
    rows = normalize_gdelt_articles({"articles": [
        {"url": "https://example.com/a#one", "title": "Headline one"},
        {"url": "https://example.com/a#two", "title": "Headline duplicate"},
        {"url": "javascript:alert(1)", "title": "Bad URL"},
        {"url": "https://example.com/b", "title": "  "},
    ]})
    assert len(rows) == 1
    assert rows[0]["title"] == "Headline one"


@pytest.mark.parametrize("payload", [None, {}, {"articles": {}}, {"articles": [None]}])
def test_rejects_malformed_response_envelope(payload):
    with pytest.raises(GdeltPayloadError):
        normalize_gdelt_articles(payload)


@pytest.mark.parametrize("kwargs", [
    {"query": ""}, {"query": "news", "max_records": 251},
    {"query": "news", "start_datetime": "2026-10-16"},
    {"query": "news", "start_datetime": "20261017000000", "end_datetime": "20261016000000"},
])
def test_rejects_invalid_query_arguments_before_network(kwargs):
    with GdeltDocClient(transport=httpx.MockTransport(
        lambda _: pytest.fail("network must not be called")
    )) as client:
        with pytest.raises(ValueError):
            client.search_articles(**kwargs)


def test_http_and_json_errors_are_reported_safely():
    with GdeltDocClient(transport=httpx.MockTransport(
        lambda _: httpx.Response(503, text="unavailable")
    )) as client:
        with pytest.raises(GdeltError, match="GDELT request failed"):
            client.search_articles("Iran politics")
    with GdeltDocClient(transport=httpx.MockTransport(
        lambda _: httpx.Response(200, text="not-json")
    )) as client:
        with pytest.raises(GdeltError, match="GDELT request failed"):
            client.search_articles("Iran politics")
