import fetch_news


class FakeResponse:
    content = b"<html><body><h2>Ranking</h2></body></html>"
    text = content.decode()

    def raise_for_status(self):
        return None


class FakeSession:
    def __init__(self):
        self.calls = 0

    def get(self, *args, **kwargs):
        self.calls += 1
        return FakeResponse()


def test_zero_items_stays_empty_without_fallback(monkeypatch):
    monkeypatch.setitem(fetch_news.RANKING_EXTRACTORS, "fixture", lambda soup, url: [])
    session = FakeSession()

    result = fetch_news.fetch_ranking(
        session,
        {"name": "Fixture", "ranking_url": "https://example.com/ranking", "ranking_type": "fixture"},
    )

    assert result["status"] == "empty"
    assert result["items"] == []
    assert session.calls == 1


def test_unknown_ranking_type_is_parse_error_without_request():
    session = FakeSession()

    result = fetch_news.fetch_ranking(
        session,
        {"name": "Fixture", "ranking_url": "https://example.com/ranking", "ranking_type": "unknown"},
    )

    assert result["status"] == "parse_error"
    assert result["items"] == []
    assert session.calls == 0


def test_result_builder_does_not_allow_empty_success():
    result = fetch_news.build_fetch_result()

    assert result == {
        "items": [],
        "status": "empty",
        "detail": "0 items after filtering",
    }
