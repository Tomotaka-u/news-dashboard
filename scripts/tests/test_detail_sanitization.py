import requests

import fetch_news


def test_request_exception_uses_hostname_without_sensitive_request_text():
    detail = fetch_news.summarize_error(
        requests.exceptions.ConnectionError("with url: /feed?token=SECRET123"),
        "https://user:pw@example.com/feed?token=SECRET123",
    )

    for forbidden in ("SECRET123", "token", "/feed", "user", "pw"):
        assert forbidden not in detail
    assert "example.com" in detail
    assert "ConnectionError" in detail


def test_http_error_uses_status_and_reason():
    response = requests.Response()
    response.status_code = 403
    response.reason = "Forbidden"

    detail = fetch_news.summarize_error(requests.exceptions.HTTPError(response=response), "https://example.com")

    assert detail == "HTTP 403 Forbidden"


def test_request_exception_uses_unknown_host_for_non_url():
    detail = fetch_news.summarize_error(
        requests.exceptions.ConnectionError("connection refused"), "not a url"
    )

    assert detail == "ConnectionError (unknown-host)"


def test_parse_error_redacts_url():
    detail = fetch_news.summarize_error(ValueError("bad https://example.com/path?token=SECRET123"), "https://example.com")

    assert "<url>" in detail
    assert "SECRET123" not in detail


def test_result_builder_redacts_urllib3_request_path_and_query():
    result = fetch_news.build_fetch_result(
        status="http_error",
        detail="HTTPSConnectionPool(host='example.com', port=443): Max retries exceeded with url: /feed?token=SECRET123 (Caused by X)",
    )

    assert "SECRET123" not in result["detail"]
    assert "token" not in result["detail"]
    assert "url:" not in result["detail"]
    assert "<url>" in result["detail"]
    assert "example.com" in result["detail"]
