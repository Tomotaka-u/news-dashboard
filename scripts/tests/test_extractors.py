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


def test_extract_gizmodo_rejects_rank_gap():
    items = fetch_news.extract_gizmodo_ranking(
        load_fixture("gizmodo-ranking-rank-gap.html"), "https://www.gizmodo.jp/"
    )

    assert items == []


def test_extract_gizmodo_records_rank_gap_reason():
    fetch_news.extract_gizmodo_ranking(
        load_fixture("gizmodo-ranking-rank-gap.html"), "https://www.gizmodo.jp/"
    )

    assert fetch_news._RANKING_DIAG["reason"] == "gizmodo:rank_seq"


def test_extract_gizmodo_rejects_inactive_daily_tab():
    items = fetch_news.extract_gizmodo_ranking(
        load_fixture("gizmodo-ranking-daily-inactive.html"), "https://www.gizmodo.jp/"
    )

    assert items == []


def test_extract_gizmodo_rejects_tab_panel_mismatch():
    items = fetch_news.extract_gizmodo_ranking(
        load_fixture("gizmodo-ranking-tab-panel-mismatch.html"), "https://www.gizmodo.jp/"
    )

    assert items == []


def test_extract_gizmodo_rejects_rank_number_title():
    items = fetch_news.extract_gizmodo_ranking(
        load_fixture("gizmodo-ranking-title-is-rank-number.html"), "https://www.gizmodo.jp/"
    )

    assert items == []


def test_extract_gizmodo_requires_ranking_title_node():
    items = fetch_news.extract_gizmodo_ranking(
        load_fixture("gizmodo-ranking-title-node-missing.html"), "https://www.gizmodo.jp/"
    )

    assert items == []


def test_extract_fashionsnap_all_category_top_five_in_rank_order():
    items = fetch_news.extract_fashionsnap_ranking(
        load_fixture("fashionsnap-ranking-categories.html"), "https://www.fashionsnap.com/ranking/"
    )

    assert [item["link"] for item in items] == [
        f"https://www.fashionsnap.com/article/all-{number}/"
        for number in ("one", "two", "three", "four", "five")
    ]


def test_extract_fashionsnap_rejects_article_links_without_ranking_container():
    items = fetch_news.extract_fashionsnap_ranking(
        load_fixture("fashionsnap-ranking-no-container.html"),
        "https://www.fashionsnap.com/ranking/",
    )

    assert items == []


def test_extract_fashionsnap_uses_all_tab_index_when_it_is_second():
    items = fetch_news.extract_fashionsnap_ranking(
        load_fixture("fashionsnap-ranking-all-second.html"),
        "https://www.fashionsnap.com/ranking/",
    )

    assert [item["link"] for item in items] == [
        f"https://www.fashionsnap.com/article/all-{number}/"
        for number in ("one", "two", "three", "four", "five")
    ]


def test_extract_fashionsnap_rejects_monthly_initial_selection():
    items = fetch_news.extract_fashionsnap_ranking(
        load_fixture("fashionsnap-ranking-monthly-active.html"),
        "https://www.fashionsnap.com/ranking/",
    )

    assert items == []


def test_extract_fashionsnap_rejects_series_tab_count_mismatch():
    items = fetch_news.extract_fashionsnap_ranking(
        load_fixture("fashionsnap-ranking-series-mismatch.html"),
        "https://www.fashionsnap.com/ranking/",
    )

    assert items == []


def test_extract_fashionsnap_rejects_rank_title_href_mismatch():
    items = fetch_news.extract_fashionsnap_ranking(
        load_fixture("fashionsnap-ranking-href-mismatch.html"),
        "https://www.fashionsnap.com/ranking/",
    )

    assert items == []


def test_extract_fashionsnap_rejects_rank_gap_in_all_series():
    items = fetch_news.extract_fashionsnap_ranking(
        load_fixture("fashionsnap-ranking-all-rank-gap.html"),
        "https://www.fashionsnap.com/ranking/",
    )

    assert items == []


def test_extract_fashionsnap_rejects_unknown_category_tab():
    items = fetch_news.extract_fashionsnap_ranking(
        load_fixture("fashionsnap-ranking-unknown-category.html"),
        "https://www.fashionsnap.com/ranking/",
    )

    assert items == []


def test_extract_fashionsnap_rejects_four_tabs_with_five_series():
    items = fetch_news.extract_fashionsnap_ranking(
        load_fixture("fashionsnap-ranking-series-excess.html"),
        "https://www.fashionsnap.com/ranking/",
    )

    assert items == []


def test_extract_fashionsnap_rejects_missing_all_tab():
    items = fetch_news.extract_fashionsnap_ranking(
        load_fixture("fashionsnap-ranking-all-missing.html"),
        "https://www.fashionsnap.com/ranking/",
    )

    assert items == []


def test_extract_fashionsnap_records_missing_all_tab_reason():
    fetch_news.extract_fashionsnap_ranking(
        load_fixture("fashionsnap-ranking-all-missing.html"),
        "https://www.fashionsnap.com/ranking/",
    )

    assert fetch_news._RANKING_DIAG["reason"] == "fashionsnap:all_tab"


def test_extract_fashionsnap_rejects_duplicate_all_tab():
    items = fetch_news.extract_fashionsnap_ranking(
        load_fixture("fashionsnap-ranking-all-duplicate.html"),
        "https://www.fashionsnap.com/ranking/",
    )

    assert items == []


def test_extract_fashionsnap_ignores_rehashed_classes():
    expected_items = fetch_news.extract_fashionsnap_ranking(
        load_fixture("fashionsnap-ranking-categories.html"), "https://www.fashionsnap.com/ranking/"
    )
    items = fetch_news.extract_fashionsnap_ranking(
        load_fixture("fashionsnap-ranking-rehashed-categories.html"),
        "https://www.fashionsnap.com/ranking/",
    )

    assert items == expected_items
    assert len(items) == 5


def test_extract_fashionsnap_rejects_rotated_weekly_hash():
    items = fetch_news.extract_fashionsnap_ranking(
        load_fixture("fashionsnap-ranking-weekly-hash-rotated.html"),
        "https://www.fashionsnap.com/ranking/",
    )

    assert items == []


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


def test_extract_nikkei_uses_second_matching_today_container():
    items = fetch_news.extract_nikkei_ranking(
        load_fixture("nikkei-ranking-second-container.html"), "https://www.nikkei.com/access/"
    )

    assert [item["link"] for item in items] == [
        "https://www.nikkei.com/article/DGXZQOUB236YJ0T20C26A7000000/",
        "https://www.nikkei.com/article/DGXZQOUB182HG0Y6A810C2000000/",
        "https://www.nikkei.com/article/DGKKZO98332440T20C26A8NN1000/",
        "https://www.nikkei.com/article/DGXZQOGM1803Y0Y6A810C2000000/",
        "https://www.nikkei.com/article/DGKKZO98334710U6A820C2MM8000/",
    ]


def test_extract_nikkei_rejects_no_matching_today_container():
    items = fetch_news.extract_nikkei_ranking(
        load_fixture("nikkei-ranking-no-match.html"), "https://www.nikkei.com/access/"
    )

    assert items == []


def test_extract_nikkei_records_no_matching_container_reason():
    fetch_news.extract_nikkei_ranking(
        load_fixture("nikkei-ranking-no-match.html"), "https://www.nikkei.com/access/"
    )

    assert fetch_news._RANKING_DIAG["reason"] == "nikkei:container"


def test_extract_nikkei_rejects_rank_gap():
    items = fetch_news.extract_nikkei_ranking(
        load_fixture("nikkei-ranking-rank-gap.html"), "https://www.nikkei.com/access/"
    )

    assert items == []


def test_extract_nikkei_rejects_rank_number_title():
    items = fetch_news.extract_nikkei_ranking(
        load_fixture("nikkei-ranking-title-is-rank-number.html"), "https://www.nikkei.com/access/"
    )

    assert items == []
