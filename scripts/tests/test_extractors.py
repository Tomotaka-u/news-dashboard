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
        "https://www.gizmodo.jp/article/mont-bell_items_products/",
        "https://www.gizmodo.jp/article/iphone12-6years-review/",
        "https://www.gizmodo.jp/article/cabletime-screendock/",
        "https://www.gizmodo.jp/article/apple-might-finally-let-you-copy-and-paste-from-iphone-to-windows/",
        "https://www.gizmodo.jp/article/machi-ya-ceilingfanlight-review-967443/",
    ]


def test_extract_gizmodo_uses_daily_tab_index_when_it_is_second():
    items = fetch_news.extract_gizmodo_ranking(
        load_fixture("gizmodo-ranking-daily-second.html"), "https://www.gizmodo.jp/"
    )

    assert [item["link"] for item in items] == [
        f"https://www.gizmodo.jp/article/daily-second-{number}/"
        for number in ("one", "two", "three", "four", "five")
    ]


def test_extract_gizmodo_requires_daily_tab():
    items = fetch_news.extract_gizmodo_ranking(
        load_fixture("gizmodo-ranking-no-daily.html"), "https://www.gizmodo.jp/"
    )

    assert items == []


def test_extract_fashionsnap_weekly_top_five_in_rank_order():
    items = fetch_news.extract_fashionsnap_ranking(
        load_fixture("fashionsnap-ranking.html"), "https://www.fashionsnap.com/ranking/"
    )

    assert [item["link"] for item in items] == [
        "https://www.fashionsnap.com/article/henai-tsuduki/",
        "https://www.fashionsnap.com/article/2026-08-18/hiroki-tsuzuki-refer-a-case-to-prosecutors/",
        "https://www.fashionsnap.com/article/2026-08-03/hiroki-tsuzuki-orion/",
        "https://www.fashionsnap.com/article/2026-08-15/pointless-journey-apparel-collection/",
        "https://www.fashionsnap.com/article/uniqlo-loungewear/",
    ]


def test_extract_fashionsnap_rejects_article_links_without_ranking_container():
    items = fetch_news.extract_fashionsnap_ranking(
        load_fixture("fashionsnap-ranking-no-container.html"),
        "https://www.fashionsnap.com/ranking/",
    )

    assert items == []


def test_extract_fashionsnap_uses_weekly_tab_index_when_both_panels_exist():
    items = fetch_news.extract_fashionsnap_ranking(
        load_fixture("fashionsnap-ranking-weekly-second.html"),
        "https://www.fashionsnap.com/ranking/",
    )

    assert [item["link"] for item in items] == [
        f"https://www.fashionsnap.com/article/weekly-second-{number}/"
        for number in ("one", "two", "three", "four", "five")
    ]


def test_extract_nikkei_today_top_five_in_rank_order():
    items = fetch_news.extract_nikkei_ranking(
        load_fixture("nikkei-ranking.html"), "https://www.nikkei.com/access/"
    )

    assert [item["link"] for item in items] == [
        "https://www.nikkei.com/article/DGXZQOUB236YJ0T20C26A7000000/",
        "https://www.nikkei.com/article/DGXZQOUB182HG0Y6A810C2000000/",
        "https://www.nikkei.com/article/DGKKZO98332440T20C26A8NN1000/",
        "https://www.nikkei.com/article/DGXZQOGM1803Y0Y6A810C2000000/",
        "https://www.nikkei.com/article/DGKKZO98334710U6A820C2MM8000/",
    ]
