import fetch_news
from bs4 import BeautifulSoup
from pathlib import Path


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


def test_fail_detail_is_stdout_only_and_consumed(monkeypatch, capsys):
    monkeypatch.setitem(
        fetch_news.RANKING_EXTRACTORS,
        "fixture",
        lambda soup, url: fetch_news._ranking_fail("fixture:anchor"),
    )

    result = fetch_news.fetch_ranking(
        FakeSession(),
        {"name": "Fixture", "ranking_url": "https://example.com/ranking", "ranking_type": "fixture"},
    )

    assert capsys.readouterr().out == "[RANKING FAIL DETAIL] Fixture: anchor=fixture:anchor\n"
    assert result == {
        "items": [],
        "status": "empty",
        "detail": "parser 'fixture' returned 0 items",
    }
    assert fetch_news._RANKING_DIAG["reason"] is None


def test_fetch_ranking_resets_stale_fail_detail(monkeypatch, capsys):
    fetch_news._RANKING_DIAG["reason"] = "stale:anchor"
    monkeypatch.setitem(fetch_news.RANKING_EXTRACTORS, "fixture", lambda soup, url: [])

    fetch_news.fetch_ranking(
        FakeSession(),
        {"name": "Fixture", "ranking_url": "https://example.com/ranking", "ranking_type": "fixture"},
    )

    assert capsys.readouterr().out == ""
    assert fetch_news._RANKING_DIAG["reason"] is None


def test_strict_extractor_entry_resets_previous_fail_reason():
    fixtures = Path(__file__).parent / "fixtures"
    negative_soup = BeautifulSoup(
        (fixtures / "gizmodo-ranking-rank-gap.html").read_text(encoding="utf-8"), "html.parser"
    )
    positive_soup = BeautifulSoup(
        (fixtures / "gizmodo-ranking.html").read_text(encoding="utf-8"), "html.parser"
    )

    assert fetch_news.extract_gizmodo_ranking(negative_soup, "https://www.gizmodo.jp/") == []
    assert fetch_news._RANKING_DIAG["reason"] == "gizmodo:rank_seq"
    assert len(fetch_news.extract_gizmodo_ranking(positive_soup, "https://www.gizmodo.jp/")) == 5
    assert fetch_news._RANKING_DIAG["reason"] is None
