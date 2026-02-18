#!/usr/bin/env python3
"""Fetch RSS feeds and generate the news dashboard HTML."""

import os
import re
import sys
from datetime import datetime, timedelta, timezone
from urllib.parse import urljoin

import feedparser
import requests
from bs4 import BeautifulSoup
from jinja2 import Environment, FileSystemLoader

# Add scripts directory to path so config can be imported
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from config import CATEGORIES, MAX_ITEMS_PER_SITE, MAX_RANKING_ITEMS, SITES

JST = timezone(timedelta(hours=9))
USER_AGENT = "NewsDashboard/1.0 (+https://github.com/Tomotaka-u/news-dashboard)"
REQUEST_TIMEOUT = 15


def sanitize_text(text):
    """Normalize text spacing for consistent rendering and deduplication."""
    return re.sub(r"\s+", " ", text or "").strip()


def to_absolute_url(base_url, href):
    """Normalize a possibly-relative URL using a base URL."""
    href = (href or "").strip()
    if not href:
        return ""
    return urljoin(base_url, href)


def append_ranking_item(items, seen, title, href, base_url, min_title_length=1):
    """Append ranking item if it has a unique URL and meaningful title."""
    clean_title = sanitize_text(title)
    if len(clean_title) < min_title_length:
        return

    link = to_absolute_url(base_url, href)
    if not link or link in seen:
        return

    seen.add(link)
    items.append({"title": clean_title, "link": link})


def fetch_feed(site):
    """Fetch and parse an RSS feed for a single site."""
    try:
        resp = requests.get(
            site["url"],
            headers={"User-Agent": USER_AGENT},
            timeout=REQUEST_TIMEOUT,
        )
        resp.raise_for_status()
    except requests.exceptions.RequestException as exc:
        print(f"[FEED ERROR] {site['name']} request failed: {exc}")
        return []

    try:
        feed = feedparser.parse(resp.content)
        if getattr(feed, "bozo", False):
            print(f"[FEED WARN] {site['name']} malformed feed: {feed.bozo_exception}")

        items = []
        base_url = site.get("site_url", site["url"])
        for entry in feed.entries[:MAX_ITEMS_PER_SITE]:
            title = sanitize_text(entry.get("title", ""))
            link = to_absolute_url(base_url, entry.get("link", ""))
            if title and link:
                items.append({"title": title, "link": link})
        return items
    except Exception as exc:
        print(f"[FEED ERROR] {site['name']} parse failed: {exc}")
        return []


def extract_techcrunch_ranking(soup, ranking_url):
    items = []
    seen = set()
    top_headlines = None
    for el in soup.find_all(string=lambda t: t and "Top Headlines" in t):
        top_headlines = el.find_parent()
        break

    if top_headlines:
        container = top_headlines.find_parent("div") or top_headlines.find_parent("section")
        if container:
            for a_tag in container.find_all("a", class_="loop-card__title-link", href=True):
                append_ranking_item(items, seen, a_tag.get_text(strip=True), a_tag.get("href"), ranking_url, 10)
                if len(items) >= MAX_RANKING_ITEMS:
                    break
    return items


def extract_gizmodo_ranking(soup, ranking_url):
    items = []
    seen = set()
    ranking_heading = soup.find("h2", class_="s-Ranking_Heading")
    if ranking_heading:
        container = ranking_heading.find_parent("div") or ranking_heading.find_parent("section")
        if container:
            for a_tag in container.find_all("a", href=True):
                link = to_absolute_url(ranking_url, a_tag.get("href"))
                if "gizmodo.jp" not in link:
                    continue
                append_ranking_item(items, seen, a_tag.get_text(strip=True), link, ranking_url, 10)
                if len(items) >= MAX_RANKING_ITEMS:
                    break
    return items


def extract_theverge_ranking(soup, ranking_url):
    items = []
    seen = set()
    for heading in soup.find_all("h2"):
        if "Most Popular" not in heading.get_text(strip=True):
            continue
        container = heading.find_parent("div") or heading.find_parent("section")
        if container:
            for a_tag in container.find_all("a", href=True):
                append_ranking_item(items, seen, a_tag.get_text(strip=True), a_tag.get("href"), ranking_url, 15)
                if len(items) >= MAX_RANKING_ITEMS:
                    break
        break
    return items


def extract_itmedia_ranking(soup, ranking_url):
    items = []
    seen = set()
    for h3 in soup.find_all("h3"):
        a_tag = h3.find("a")
        if not a_tag or not a_tag.get("href"):
            continue
        title = a_tag.get_text(strip=True)
        if title.startswith("'"):  # Skip JS template strings.
            continue
        append_ranking_item(items, seen, title, a_tag.get("href"), ranking_url, 4)
        if len(items) >= MAX_RANKING_ITEMS:
            break
    return items


def extract_hackernews_ranking(soup, ranking_url):
    items = []
    seen = set()
    for span in soup.find_all("span", class_="titleline"):
        a_tag = span.find("a")
        if not a_tag or not a_tag.get("href"):
            continue
        append_ranking_item(items, seen, a_tag.get_text(strip=True), a_tag.get("href"), ranking_url, 4)
        if len(items) >= MAX_RANKING_ITEMS:
            break
    return items


def extract_fashionsnap_ranking(soup, ranking_url):
    items = []
    seen = set()
    for a_tag in soup.find_all("a", href=True):
        href = a_tag.get("href")
        if not re.match(r"/article/\d{4}-", href or ""):
            continue
        append_ranking_item(items, seen, a_tag.get_text(strip=True), href, ranking_url, 10)
        if len(items) >= MAX_RANKING_ITEMS:
            break
    return items


def extract_wwdjapan_ranking(soup, ranking_url):
    items = []
    seen = set()
    for a_tag in soup.find_all("a", href=True):
        href = a_tag.get("href")
        if "articles/" not in (href or ""):
            continue
        append_ranking_item(items, seen, a_tag.get_text(strip=True), href, ranking_url, 10)
        if len(items) >= MAX_RANKING_ITEMS:
            break
    return items


def extract_nikkei_ranking(soup, ranking_url):
    items = []
    seen = set()
    for a_tag in soup.find_all("a", href=True):
        href = a_tag.get("href")
        if "/article/" not in (href or ""):
            continue
        append_ranking_item(items, seen, a_tag.get_text(strip=True), href, ranking_url, 10)
        if len(items) >= MAX_RANKING_ITEMS:
            break
    return items


def extract_jdn_ranking(soup, ranking_url):
    items = []
    seen = set()
    ranking_heading = None
    for heading in soup.find_all(["h2", "h3", "h4"]):
        if "ランキング" in heading.get_text():
            ranking_heading = heading
            break

    if ranking_heading:
        parent = ranking_heading.find_parent("section") or ranking_heading.find_parent("div")
        if parent:
            for a_tag in parent.find_all("a", href=True):
                href = to_absolute_url(ranking_url, a_tag.get("href"))
                if "japandesign.ne.jp" not in href or "/ranking/" in href:
                    continue
                title = re.sub(r"^\d+", "", a_tag.get_text(strip=True)).strip()
                append_ranking_item(items, seen, title, href, ranking_url, 5)
                if len(items) >= MAX_RANKING_ITEMS:
                    break
    return items


def extract_bbc_ranking(soup, ranking_url):
    items = []
    seen = set()
    most_read = None
    for heading in soup.find_all("h2"):
        if "most read" in heading.get_text(strip=True).lower():
            most_read = heading
            break

    if most_read:
        section = most_read.find_parent("section") or most_read.find_parent("div")
        if section:
            for a_tag in section.find_all("a", href=True):
                h2_tag = a_tag.find("h2")
                title = h2_tag.get_text(strip=True) if h2_tag else a_tag.get_text(strip=True)
                append_ranking_item(items, seen, title, a_tag.get("href"), ranking_url, 10)
                if len(items) >= MAX_RANKING_ITEMS:
                    break
    return items


def extract_generic_ranking(soup, ranking_url):
    """Fallback parser used when a site-specific parser yields no items."""
    items = []
    seen = set()
    keyword_en = ("ranking", "most read", "most popular", "top headlines")
    keyword_ja = ("ランキング", "人気", "アクセス")

    for heading in soup.find_all(["h2", "h3", "h4"]):
        title = heading.get_text(" ", strip=True)
        lower = title.lower()
        if not any(k in lower for k in keyword_en) and not any(k in title for k in keyword_ja):
            continue

        section = heading.find_parent("section") or heading.find_parent("div") or heading.parent
        if not section:
            continue

        for a_tag in section.find_all("a", href=True):
            append_ranking_item(
                items,
                seen,
                a_tag.get_text(" ", strip=True),
                a_tag.get("href"),
                ranking_url,
                min_title_length=8,
            )
            if len(items) >= MAX_RANKING_ITEMS:
                return items
    return items


def _prtimes_ranking_wrappers(soup):
    """Return the ordered list of js-ranking-list wrappers from PR Times ranking page.

    Tab order: 旬速(0), いま話題(1), 今日のランキング(2), SNSで話題(3), 今週(4), 今月(5).
    """
    return soup.find_all("div", class_="js-ranking-list")


def _extract_prtimes_articles(wrapper, base_url, limit):
    """Extract article items from a PR Times ranking wrapper."""
    items = []
    seen = set()
    if not wrapper:
        return items
    for article in wrapper.find_all("article", class_="list-article"):
        h3 = article.find("h3", class_="list-article__title")
        a_tag = article.find("a", class_="list-article__link")
        if not h3 or not a_tag or not a_tag.get("href"):
            continue
        title = h3.get_text(strip=True)
        href = a_tag.get("href")
        append_ranking_item(items, seen, title, href, base_url, 5)
        if len(items) >= limit:
            break
    return items


def extract_prtimes_news(soup, base_url):
    """Extract '旬速' (trending) items from PR Times ranking page."""
    wrappers = _prtimes_ranking_wrappers(soup)
    if not wrappers:
        return []
    return _extract_prtimes_articles(wrappers[0], base_url, MAX_ITEMS_PER_SITE)


def extract_prtimes_ranking(soup, ranking_url):
    """Extract '今日のランキング' items from PR Times ranking page."""
    wrappers = _prtimes_ranking_wrappers(soup)
    if len(wrappers) < 3:
        return []
    return _extract_prtimes_articles(wrappers[2], ranking_url, MAX_RANKING_ITEMS)


def extract_yahoo_news(soup, base_url):
    """Extract '主要' (top/main) news items from Yahoo! News top page."""
    items = []
    seen = set()
    topics = soup.find("section", class_="topics")
    if not topics:
        return items
    for a_tag in topics.find_all("a", href=lambda h: h and "/pickup/" in h):
        title = a_tag.get_text(strip=True)
        href = a_tag.get("href")
        append_ranking_item(items, seen, title, href, base_url, 4)
        if len(items) >= MAX_ITEMS_PER_SITE:
            break
    return items


def extract_yahoo_news_ranking(soup, ranking_url):
    """Extract ranking items from Yahoo! News ranking page."""
    items = []
    seen = set()
    for a_tag in soup.find_all("a", href=lambda h: h and "/articles/" in h):
        body = a_tag.find("div", class_="newsFeed_item_body")
        if not body:
            continue
        # Title is in the first div inside the second child div of body
        divs = body.find_all("div", recursive=False)
        if len(divs) < 2:
            continue
        title_div = divs[1].find("div")
        if not title_div:
            continue
        title = title_div.get_text(strip=True)
        href = a_tag.get("href")
        append_ranking_item(items, seen, title, href, ranking_url, 5)
        if len(items) >= MAX_RANKING_ITEMS:
            break
    return items


SCRAPE_NEWS_EXTRACTORS = {
    "prtimes_news": extract_prtimes_news,
    "yahoo_news": extract_yahoo_news,
}


RANKING_EXTRACTORS = {
    "techcrunch": extract_techcrunch_ranking,
    "gizmodo": extract_gizmodo_ranking,
    "theverge": extract_theverge_ranking,
    "itmedia": extract_itmedia_ranking,
    "hackernews": extract_hackernews_ranking,
    "fashionsnap": extract_fashionsnap_ranking,
    "wwdjapan": extract_wwdjapan_ranking,
    "nikkei": extract_nikkei_ranking,
    "jdn": extract_jdn_ranking,
    "bbc": extract_bbc_ranking,
    "prtimes": extract_prtimes_ranking,
    "yahoo_news": extract_yahoo_news_ranking,
}


def fetch_scrape_news(site):
    """Fetch news items from a site via HTML scraping (non-RSS)."""
    url = site["url"]
    scrape_type = site.get("scrape_type")
    if not url or not scrape_type:
        return []

    try:
        resp = requests.get(
            url,
            headers={"User-Agent": USER_AGENT},
            timeout=REQUEST_TIMEOUT,
        )
        resp.raise_for_status()
    except requests.exceptions.RequestException as exc:
        print(f"[SCRAPE ERROR] {site['name']} request failed: {exc}")
        return []

    soup = BeautifulSoup(resp.text, "html.parser")
    extractor = SCRAPE_NEWS_EXTRACTORS.get(scrape_type)
    if not extractor:
        print(f"[SCRAPE WARN] {site['name']} unknown scrape_type='{scrape_type}'")
        return []

    try:
        items = extractor(soup, url)
    except Exception as exc:
        print(f"[SCRAPE ERROR] {site['name']} parser '{scrape_type}' failed: {exc}")
        items = []

    return items[:MAX_ITEMS_PER_SITE]


def fetch_ranking(site):
    """Fetch ranking/popular articles for a site via scraping."""
    ranking_url = site.get("ranking_url")
    ranking_type = site.get("ranking_type")
    if not ranking_url or not ranking_type:
        return []

    try:
        resp = requests.get(
            ranking_url,
            headers={"User-Agent": USER_AGENT},
            timeout=REQUEST_TIMEOUT,
        )
        resp.raise_for_status()
    except requests.exceptions.RequestException as exc:
        print(f"[RANKING ERROR] {site['name']} request failed: {exc}")
        return []

    if ranking_type == "itmedia":
        content = resp.content.decode("shift_jis", errors="replace")
    else:
        content = resp.text
    soup = BeautifulSoup(content, "html.parser")

    extractor = RANKING_EXTRACTORS.get(ranking_type)
    if not extractor:
        print(f"[RANKING WARN] {site['name']} unknown ranking_type='{ranking_type}'. Using generic parser.")
        return extract_generic_ranking(soup, ranking_url)[:MAX_RANKING_ITEMS]

    try:
        items = extractor(soup, ranking_url)
    except Exception as exc:
        print(f"[RANKING ERROR] {site['name']} parser '{ranking_type}' failed: {exc}")
        items = []

    if items:
        return items[:MAX_RANKING_ITEMS]

    fallback_items = extract_generic_ranking(soup, ranking_url)
    if fallback_items:
        print(
            f"[RANKING WARN] {site['name']} parser '{ranking_type}' returned 0 items. "
            f"Fallback found {len(fallback_items)} items."
        )
    else:
        print(
            f"[RANKING WARN] {site['name']} parser '{ranking_type}' returned 0 items. "
            "Fallback also found 0 items."
        )
    return fallback_items[:MAX_RANKING_ITEMS]


def build_site_view_model(site, items):
    """Build UI-facing site payload with defaults in one place."""
    return {
        "name": site["name"],
        "items": items,
        "icon": site.get("icon", "?"),
        "css_class": site.get("css_class", ""),
        "domain": site.get("domain", ""),
        "badge": site.get("badge", ""),
        "site_url": site.get("site_url", "#"),
        "icon_gradient": site.get("icon_gradient", "linear-gradient(135deg, #888, #aaa)"),
        "accent_color": site.get("accent_color", "#888"),
    }


def init_category_data():
    """Initialize category buckets before fetching feeds."""
    category_data = {}
    for cat_key, cat_info in CATEGORIES.items():
        category_data[cat_key] = {
            "label": cat_info["label"],
            "color": cat_info["color"],
            "sites": [],
            "total": 0,
        }
    return category_data


def build_display_categories(category_data):
    """Merge internal categories by shared display labels for the template."""
    display_by_label = {}
    display_categories = []

    for cat_key, cat_info in CATEGORIES.items():
        label = cat_info["label"]
        bucket = display_by_label.get(label)
        if bucket is None:
            bucket = {
                "label": label,
                "color": cat_info["color"],
                "sites": [],
                "total": 0,
                "source_count": 0,
            }
            display_by_label[label] = bucket
            display_categories.append(bucket)

        cat_bucket = category_data.get(cat_key, {"sites": [], "total": 0})
        bucket["sites"].extend(cat_bucket["sites"])
        bucket["total"] += cat_bucket["total"]
        bucket["source_count"] += len(cat_bucket["sites"])

    return display_categories


def main():
    category_data = init_category_data()
    ranking_data = []
    ranking_total_sources = sum(1 for site in SITES if site.get("ranking_url"))
    ranking_success_sources = 0

    for site in SITES:
        cat = site["category"]
        print(f"Fetching: {site['name']} ...")
        if site.get("type") == "scrape":
            items = fetch_scrape_news(site)
        else:
            items = fetch_feed(site)
        print(f"  -> {len(items)} items")
        if items:
            category_data[cat]["sites"].append(build_site_view_model(site, items))
            category_data[cat]["total"] += len(items)

        if site.get("ranking_url"):
            print(f"  Fetching ranking: {site['name']} ...")
            ranking_items = fetch_ranking(site)
            print(f"  -> {len(ranking_items)} ranking items")
            if ranking_items:
                ranking_data.append(build_site_view_model(site, ranking_items))
                ranking_success_sources += 1

    display_categories = build_display_categories(category_data)
    overall_total = sum(category["total"] for category in display_categories)

    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    template_dir = os.path.join(project_root, "templates")
    env = Environment(loader=FileSystemLoader(template_dir), autoescape=True)
    template = env.get_template("index.html.j2")

    now_jst = datetime.now(JST)
    ranking_status = {
        "total_sources": ranking_total_sources,
        "success_sources": ranking_success_sources,
        "failed_sources": ranking_total_sources - ranking_success_sources,
        "updated_at": now_jst.strftime("%Y-%m-%d %H:%M JST"),
    }
    html = template.render(
        display_categories=display_categories,
        overall_total=overall_total,
        all_sites=SITES,
        ranking_data=ranking_data,
        ranking_status=ranking_status,
        updated_at=now_jst.strftime("%Y-%m-%d %H:%M JST"),
    )

    docs_dir = os.path.join(project_root, "docs")
    os.makedirs(docs_dir, exist_ok=True)
    output_path = os.path.join(docs_dir, "index.html")
    with open(output_path, "w", encoding="utf-8") as file_obj:
        file_obj.write(html)

    print(f"\nGenerated: {output_path}")
    print(f"Updated at: {now_jst.strftime('%Y-%m-%d %H:%M JST')}")


if __name__ == "__main__":
    main()
