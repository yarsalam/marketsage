import httpx
import pytest

from codal_provider import CodalClient, CodalError


def test_search_sends_filters_and_keeps_publication_time_unknown():
    def handler(request):
        assert request.url.params["Symbol"] == "فولاد"
        assert request.url.params["PageNumber"] == "2"
        assert request.url.params["Length"] == "10"
        return httpx.Response(200, json={"Letters": []})
    with CodalClient(transport=httpx.MockTransport(handler)) as client:
        result = client.search_disclosures(symbol="فولاد", page=2, page_size=10)
    assert result["payload"] == {"Letters": []}
    assert result["publication_timestamp"] is None
    assert result["eligible_for_scoring"] is False


@pytest.mark.parametrize("kwargs", [
    {"page": 0}, {"page_size": 101}, {"start_date": "2026/10/01"},
    {"start_date": "2026-10-10", "end_date": "2026-10-01"},
])
def test_rejects_invalid_filters(kwargs):
    with CodalClient(transport=httpx.MockTransport(lambda _: httpx.Response(200, json={}))) as client:
        with pytest.raises(ValueError):
            client.search_disclosures(**kwargs)


def test_rejects_non_object_payload():
    with CodalClient(transport=httpx.MockTransport(lambda _: httpx.Response(200, json=[]))) as client:
        with pytest.raises(CodalError):
            client.search_disclosures()
