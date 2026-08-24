import json

import pytest

import fetch_news


SITE = {
    "name": "Fixture Feed",
    "url": "https://example.com/feed",
    "category": "tech",
    "type": "rss",
    "site_url": "https://example.com",
    "accent_color": "#123456",
}


def configure_success(monkeypatch):
    monkeypatch.setattr(fetch_news, "SITES", [SITE])
    monkeypatch.setenv("NEWS_MIN_TOTAL_ITEMS", "1")
    monkeypatch.setattr(fetch_news, "fetch_all_sns", lambda session: [])
    monkeypatch.setattr(
        fetch_news,
        "fetch_feed",
        lambda session, site: fetch_news.build_fetch_result(
            items=[{"title": "Fixture item", "link": "https://example.com/item"}]
        ),
    )


def test_atomic_write_replaces_both_files_without_temp_files(monkeypatch, tmp_path):
    configure_success(monkeypatch)

    fetch_news.run(session=object(), output_dir=tmp_path)

    assert sorted(path.name for path in tmp_path.iterdir()) == ["index.html", "status.json"]
    status_text = (tmp_path / "status.json").read_text(encoding="utf-8")
    assert status_text.endswith("\n")
    assert list(json.loads(status_text)) == sorted(json.loads(status_text))


def test_second_temp_write_preserves_existing_files_and_removes_temp_files(monkeypatch, tmp_path):
    configure_success(monkeypatch)
    index_path = tmp_path / "index.html"
    status_path = tmp_path / "status.json"
    index_path.write_text("existing-index", encoding="utf-8")
    status_path.write_text("existing-status", encoding="utf-8")
    original_write_tmp = fetch_news._write_tmp
    calls = 0

    def fail_on_second_write(path, text):
        nonlocal calls
        calls += 1
        if calls == 2:
            raise OSError("status temporary write failed")
        return original_write_tmp(path, text)

    monkeypatch.setattr(fetch_news, "_write_tmp", fail_on_second_write)

    with pytest.raises(OSError, match="status temporary write failed"):
        fetch_news.run(session=object(), output_dir=tmp_path)

    assert index_path.read_text(encoding="utf-8") == "existing-index"
    assert status_path.read_text(encoding="utf-8") == "existing-status"
    assert list(tmp_path.glob("*.tmp")) == []
