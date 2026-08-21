from pathlib import Path

from bs4 import BeautifulSoup

import fetch_news


FIXTURES = Path(__file__).parent / "fixtures"


def load_fixture(name):
    return BeautifulSoup((FIXTURES / name).read_text(encoding="utf-8"), "html.parser")


def test_extract_techcrunch_most_popular_in_order():
    items = fetch_news.extract_techcrunch_ranking(
        load_fixture("techcrunch-most-popular.html"), "https://techcrunch.com/"
    )

    assert [item["link"] for item in items] == [
        "https://techcrunch.com/2026/08/19/popular-one/",
        "https://techcrunch.com/2026/08/18/popular-two/",
        "https://techcrunch.com/2026/08/18/popular-three/",
        "https://techcrunch.com/2026/08/17/popular-four/",
        "https://techcrunch.com/2026/08/16/popular-five/",
    ]


def test_extract_gizmodo_daily_module_only():
    items = fetch_news.extract_gizmodo_ranking(
        load_fixture("gizmodo-ranking.html"), "https://www.gizmodo.jp/"
    )

    assert [item["link"] for item in items] == [
        f"https://www.gizmodo.jp/article/daily-{number}/"
        for number in ("one", "two", "three", "four", "five")
    ]
