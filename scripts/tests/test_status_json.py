import json

import fetch_news


FEED_WITH_RANKING = {
    "name": "Shared Name",
    "url": "https://example.com/feed-a",
    "category": "tech",
    "type": "rss",
    "site_url": "https://example.com/a",
    "accent_color": "#123456",
    "ranking_url": "https://example.com/ranking-a",
    "ranking_type": "fixture",
}
HEALTHY_FEED = {
    "name": "Healthy Feed",
    "url": "https://example.com/feed-b",
    "category": "tech",
    "type": "rss",
    "site_url": "https://example.com/b",
    "accent_color": "#654321",
}


def test_status_schema_order_and_feed_status_not_overwritten(monkeypatch, tmp_path):
    monkeypatch.setattr(fetch_news, "SITES", [FEED_WITH_RANKING, HEALTHY_FEED])
    monkeypatch.setenv("NEWS_MIN_TOTAL_ITEMS", "1")
    monkeypatch.setattr(fetch_news, "fetch_all_sns", lambda session: [])

    def fake_feed(session, site):
        if site["name"] == "Shared Name":
            return fetch_news.build_fetch_result(status="empty", detail="feed is empty")
        return fetch_news.build_fetch_result(
            items=[{"title": "Healthy item", "link": "https://example.com/item"}]
        )

    monkeypatch.setattr(fetch_news, "fetch_feed", fake_feed)
    monkeypatch.setattr(
        fetch_news,
        "fetch_ranking",
        lambda session, site: fetch_news.build_fetch_result(
            items=[{"title": "Popular item", "link": "https://example.com/popular"}]
        ),
    )

    returned = fetch_news.run(session=object(), output_dir=tmp_path)
    written = json.loads((tmp_path / "status.json").read_text(encoding="utf-8"))

    assert written == returned
    assert set(written) == {"generated_at", "gate", "feeds", "rankings", "sources"}
    assert written["feeds"] == {"total_sources": 2, "ok_sources": 1}
    assert written["rankings"] == {"total_sources": 1, "ok_sources": 1}
    assert [(row["name"], row["kind"], row["status"], row["count"]) for row in written["sources"]] == [
        ("Shared Name", "feed", "empty", 0),
        ("Shared Name", "ranking", "ok", 1),
        ("Healthy Feed", "feed", "ok", 1),
    ]
    html = (tmp_path / "index.html").read_text(encoding="utf-8")
    assert "取得失敗" in html
    assert html.count("取得失敗") == 1
    assert 'title="feed is empty"' in html
    assert 'href="status.json"' in html


def test_failed_ranking_name_is_rendered(monkeypatch, tmp_path):
    monkeypatch.setattr(fetch_news, "SITES", [FEED_WITH_RANKING])
    monkeypatch.setenv("NEWS_MIN_TOTAL_ITEMS", "1")
    monkeypatch.setattr(fetch_news, "fetch_all_sns", lambda session: [])
    monkeypatch.setattr(
        fetch_news,
        "fetch_feed",
        lambda session, site: fetch_news.build_fetch_result(
            items=[{"title": "Healthy item", "link": "https://example.com/item"}]
        ),
    )
    monkeypatch.setattr(
        fetch_news,
        "fetch_ranking",
        lambda session, site: fetch_news.build_fetch_result(status="empty", detail="no popular items"),
    )

    fetch_news.run(session=object(), output_dir=tmp_path)

    html = (tmp_path / "index.html").read_text(encoding="utf-8")
    assert html.count("失敗: Shared Name (empty)") == 2


def test_incomplete_ranking_config_is_reported_as_skipped(monkeypatch, tmp_path):
    incomplete_site = {**HEALTHY_FEED, "ranking_type": "fixture"}
    monkeypatch.setattr(fetch_news, "SITES", [incomplete_site])
    monkeypatch.setenv("NEWS_MIN_TOTAL_ITEMS", "1")
    monkeypatch.setattr(fetch_news, "fetch_all_sns", lambda session: [])
    monkeypatch.setattr(
        fetch_news,
        "fetch_feed",
        lambda session, site: fetch_news.build_fetch_result(
            items=[{"title": "Healthy item", "link": "https://example.com/item"}]
        ),
    )

    status = fetch_news.run(session=object(), output_dir=tmp_path)

    assert status["rankings"] == {"total_sources": 1, "ok_sources": 0}
    assert status["sources"][1] == {
        "name": "Healthy Feed",
        "kind": "ranking",
        "status": "skipped",
        "count": 0,
        "detail": "missing ranking_url or ranking_type",
    }
