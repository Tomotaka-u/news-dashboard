from pathlib import Path

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


def items(count):
    return [
        {"title": f"Fixture item {index}", "link": f"https://example.com/{index}"}
        for index in range(count)
    ]


def configure(monkeypatch, count):
    monkeypatch.setattr(fetch_news, "SITES", [SITE])
    monkeypatch.setattr(
        fetch_news,
        "fetch_feed",
        lambda session, site: fetch_news.build_fetch_result(items=items(count)),
    )


def test_gate_failure_preserves_existing_files_and_skips_sns(monkeypatch, tmp_path):
    configure(monkeypatch, 19)
    index_path = tmp_path / "index.html"
    status_path = tmp_path / "status.json"
    index_path.write_bytes(b"existing-index")
    status_path.write_bytes(b"existing-status")
    before = {path.name: path.read_bytes() for path in tmp_path.iterdir()}

    def unexpected_sns_call(session):
        raise AssertionError("SNS must not run after a gate failure")

    monkeypatch.setattr(fetch_news, "fetch_all_sns", unexpected_sns_call)

    with pytest.raises(SystemExit) as exc_info:
        fetch_news.run(session=object(), output_dir=tmp_path)

    assert exc_info.value.code == 1
    assert {path.name: path.read_bytes() for path in tmp_path.iterdir()} == before


def test_gate_boundary_writes_index_and_status(monkeypatch, tmp_path):
    configure(monkeypatch, 20)
    monkeypatch.setattr(fetch_news, "fetch_all_sns", lambda session: [])

    status = fetch_news.run(session=object(), output_dir=tmp_path)

    assert status["gate"] == {"passed": True, "overall_total": 20, "min_total_items": 20}
    assert (tmp_path / "index.html").is_file()
    assert (tmp_path / "status.json").is_file()


def test_gate_reads_environment_override_at_runtime(monkeypatch, tmp_path):
    configure(monkeypatch, 20)
    monkeypatch.setenv("NEWS_MIN_TOTAL_ITEMS", "21")

    with pytest.raises(SystemExit) as exc_info:
        fetch_news.run(session=object(), output_dir=tmp_path)

    assert exc_info.value.code == 1
    assert list(tmp_path.iterdir()) == []


def test_invalid_gate_environment_value_is_not_silenced(monkeypatch, tmp_path):
    configure(monkeypatch, 20)
    monkeypatch.setenv("NEWS_MIN_TOTAL_ITEMS", "not-an-integer")

    with pytest.raises(ValueError):
        fetch_news.run(session=object(), output_dir=tmp_path)

    assert list(tmp_path.iterdir()) == []
