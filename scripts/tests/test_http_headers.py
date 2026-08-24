import fetch_news


class FakeResponse:
    content = b"<rss><channel><item><title>Title</title><link>https://example.com/item</link></item></channel></rss>"

    def raise_for_status(self):
        return None


class FakeSession:
    def __init__(self):
        self.headers = None

    def get(self, *args, **kwargs):
        self.headers = kwargs["headers"]
        return FakeResponse()


def test_build_http_session_sets_default_headers():
    session = fetch_news.build_http_session()

    assert session.headers["User-Agent"] == fetch_news.USER_AGENT
    assert session.headers["Accept-Language"] == "ja,en;q=0.8"


def test_fetch_feed_passes_feed_accept_header():
    session = FakeSession()

    fetch_news.fetch_feed(session, {"url": "https://example.com/feed"})

    assert session.headers == {"Accept": fetch_news.FEED_ACCEPT}


def test_fetch_ranking_passes_html_accept_header(monkeypatch):
    session = FakeSession()
    monkeypatch.setitem(fetch_news.RANKING_EXTRACTORS, "fixture", lambda soup, url: [])

    fetch_news.fetch_ranking(session, {
        "ranking_url": "https://example.com/ranking",
        "ranking_type": "fixture",
    })

    assert session.headers == {"Accept": fetch_news.HTML_ACCEPT}
