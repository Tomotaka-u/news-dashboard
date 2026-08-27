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
    monkeypatch.delenv("NEWS_MIN_TOTAL_ITEMS", raising=False)
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


def capture_sns_data(monkeypatch):
    captured = {}

    class CapturingTemplate:
        def render(self, **kwargs):
            captured["sns_data"] = kwargs["sns_data"]
            return "<html></html>"

    class CapturingEnvironment:
        def __init__(self, *args, **kwargs):
            pass

        def get_template(self, name):
            assert name == "index.html.j2"
            return CapturingTemplate()

    monkeypatch.setattr(fetch_news, "Environment", CapturingEnvironment)
    return captured


def test_sns_fetch_is_disabled_by_default_and_keeps_category_contract(monkeypatch, tmp_path, capsys):
    configure(monkeypatch, 20)
    captured = capture_sns_data(monkeypatch)
    monkeypatch.setenv("XAI_API_KEY", "fixture-key-must-not-be-read")
    secret_reads = []
    original_get = fetch_news.os.environ.get

    def tracking_get(key, default=None):
        if key in {"XAI_API_KEY", "XAI_MODEL"}:
            secret_reads.append(key)
        return original_get(key, default)

    monkeypatch.setattr(fetch_news.os.environ, "get", tracking_get)

    assert fetch_news.SNS_FETCH_ENABLED is False

    class NoPostSession:
        post_calls = 0

        def post(self, *args, **kwargs):
            self.post_calls += 1
            raise AssertionError("xAI HTTP requests must be disabled by default")

    session = NoPostSession()
    fetch_news.run(session=session, output_dir=tmp_path)

    assert "[SNS SKIP] Automated xAI SNS fetching is disabled." in capsys.readouterr().out
    assert session.post_calls == 0
    assert secret_reads == []
    assert captured["sns_data"] == [
        {
            "key": category["key"],
            "label": category["label"],
            "badge": category["badge"],
            "accent_color": category["accent_color"],
            "icon_gradient": category["icon_gradient"],
            "posts": [],
        }
        for category in fetch_news.SNS_CATEGORIES
    ]


def test_sns_fetch_enabled_override_uses_all_legacy_category_requests(monkeypatch, tmp_path):
    configure(monkeypatch, 20)
    captured = capture_sns_data(monkeypatch)
    monkeypatch.setenv("XAI_API_KEY", "fixture-key")
    monkeypatch.setattr(fetch_news, "SNS_FETCH_ENABLED", True, raising=False)

    class FakeResponse:
        def raise_for_status(self):
            pass

        def json(self):
            return {
                "output": [{
                    "type": "message",
                    "role": "assistant",
                    "content": [{"type": "output_text", "text": "[]"}],
                }],
            }

    class RecordingSession:
        def __init__(self):
            self.post_calls = []

        def post(self, url, **kwargs):
            self.post_calls.append({"url": url, **kwargs})
            return FakeResponse()

    session = RecordingSession()

    fetch_news.run(session=session, output_dir=tmp_path)

    assert len(session.post_calls) == len(fetch_news.SNS_CATEGORIES) == 5
    assert {call["url"] for call in session.post_calls} == {
        "https://api.x.ai/v1/responses",
    }
    assert [category["key"] for category in captured["sns_data"]] == [
        category["key"] for category in fetch_news.SNS_CATEGORIES
    ]
    assert all(category["posts"] == [] for category in captured["sns_data"])
