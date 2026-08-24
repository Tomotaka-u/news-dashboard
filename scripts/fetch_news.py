#!/usr/bin/env python3
"""Fetch RSS feeds and generate the news dashboard HTML."""

import json
import os
import re
import sys
import time
from datetime import datetime, timedelta, timezone
from urllib.parse import urljoin, urlparse

import feedparser
import requests
from bs4 import BeautifulSoup
from jinja2 import Environment, FileSystemLoader
from requests.adapters import HTTPAdapter
from urllib3.util import Retry

# Add scripts directory to path so config can be imported
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from config import (
    BOOKMARKS,
    CATEGORIES,
    DEFAULT_XAI_MODEL,
    DISPLAY_CATEGORIES,
    MAX_ITEMS_PER_SITE,
    MAX_RANKING_ITEMS,
    MIN_TOTAL_ITEMS,
    SITES,
    SNS_CATEGORIES,
)

JST = timezone(timedelta(hours=9))
USER_AGENT = "NewsDashboard/1.0 (+https://github.com/Tomotaka-u/news-dashboard)"
REQUEST_TIMEOUT = 15
RETRY_TOTAL = 3
RETRY_BACKOFF = 0.7
RETRY_STATUS_CODES = (429, 500, 502, 503, 504)
SNS_API_RETRY_TOTAL = 2
HTML_ACCEPT = "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8"
FEED_ACCEPT = "application/rss+xml,application/atom+xml,application/rdf+xml,application/xml;q=0.9,text/xml;q=0.9,*/*;q=0.8"


def build_fetch_result(items=None, status="ok", detail=""):
    """Build the common fetch result and keep diagnostic text bounded."""
    items = items or []
    if status == "ok" and not items:
        status = "empty"
        detail = detail or "0 items after filtering"
    elif status != "ok" and items:
        raise ValueError(f"fetch result status='{status}' cannot contain items")
    return {
        "items": items,
        "status": status,
        "detail": sanitize_text(redact_detail(str(detail)))[:200],
    }


def sanitize_text(text):
    """Normalize text spacing for consistent rendering and deduplication."""
    return re.sub(r"\s+", " ", text or "").strip()


def redact_detail(detail):
    """Remove URLs, urllib3 request paths, and query strings from diagnostics."""
    detail = re.sub(r"https?://\S+", "<url>", detail)
    detail = re.sub(r"url: /\S*", "<url>", detail)
    return re.sub(r"\?\S+", "<url>", detail)


def summarize_error(exc, url):
    """Create a safe, concise diagnostic for a fetch or parse error."""
    if isinstance(exc, requests.exceptions.HTTPError) and exc.response is not None:
        return f"HTTP {exc.response.status_code} {exc.response.reason}"
    if isinstance(exc, requests.exceptions.RequestException):
        return f"{type(exc).__name__} ({urlparse(url).hostname})"
    return f"{type(exc).__name__}: {redact_detail(str(exc))[:160]}"


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


def _parse_rank_number(text):
    """Return a normalized rank number when text uses an accepted format."""
    match = re.fullmatch(r"0?(\d{1,3})(位|\.)?", sanitize_text(text or ""))
    return int(match.group(1)) if match else None


def build_http_session():
    """Create a requests session with retry policy for transient failures."""
    retry = Retry(
        total=RETRY_TOTAL,
        connect=RETRY_TOTAL,
        read=RETRY_TOTAL,
        status=RETRY_TOTAL,
        backoff_factor=RETRY_BACKOFF,
        status_forcelist=RETRY_STATUS_CODES,
        allowed_methods=frozenset(["GET"]),
        raise_on_status=False,
    )
    adapter = HTTPAdapter(max_retries=retry)
    session = requests.Session()
    session.headers.update({
        "User-Agent": USER_AGENT,
        "Accept-Language": "ja,en;q=0.8",
    })
    session.mount("https://", adapter)
    session.mount("http://", adapter)
    return session


def fetch_feed(session, site):
    """Fetch and parse an RSS feed for a single site."""
    try:
        resp = session.get(
            site["url"],
            headers={"Accept": FEED_ACCEPT},
            timeout=REQUEST_TIMEOUT,
        )
        resp.raise_for_status()
    except requests.exceptions.RequestException as exc:
        return build_fetch_result(status="http_error", detail=summarize_error(exc, site["url"]))

    try:
        feed = feedparser.parse(resp.content)
        bozo_detail = ""
        if getattr(feed, "bozo", False):
            bozo_detail = f"bozo=1: {getattr(feed, 'bozo_exception', 'unknown parse warning')}"

        items = []
        base_url = site.get("site_url", site["url"])
        for entry in feed.entries[:MAX_ITEMS_PER_SITE]:
            title = sanitize_text(entry.get("title", ""))
            link = to_absolute_url(base_url, entry.get("link", ""))
            if title and link:
                items.append({"title": title, "link": link})
        if items:
            return build_fetch_result(items=items, detail=bozo_detail)
        detail = "0 entries after filtering"
        if bozo_detail:
            detail = f"{detail} ({bozo_detail})"
        return build_fetch_result(status="empty", detail=detail)
    except Exception as exc:
        return build_fetch_result(status="parse_error", detail=summarize_error(exc, site["url"]))


def extract_techcrunch_ranking(soup, ranking_url):
    items = []
    seen = set()
    container = soup.select_one(".wp-block-techcrunch-most-popular-posts")
    if not container:
        return items

    heading = container.find(["h2", "h3", "h4"])
    if not heading or "most popular" not in heading.get_text(" ", strip=True).lower():
        return items

    for a_tag in container.select("a.loop-card__title-link[href]"):
        append_ranking_item(items, seen, a_tag.get_text(strip=True), a_tag.get("href"), ranking_url, 10)
        if len(items) >= MAX_RANKING_ITEMS:
            break
    return items


def extract_gizmodo_ranking(soup, ranking_url):
    items = []
    seen = set()
    ranking_heading = None
    for heading in soup.find_all(["h2", "h3", "h4"]):
        heading_text = sanitize_text(heading.get_text(" ", strip=True)).upper()
        if heading_text == "RANKING":
            ranking_heading = heading
            break

    # Fallback to legacy class name if exact heading text is not available.
    if ranking_heading is None:
        ranking_heading = soup.find("h2", class_="s-Ranking_Heading")

    if ranking_heading is None:
        return items

    container = ranking_heading.find_parent(
        "div", class_=lambda value: value and "rankingContainer" in value
    )
    if container is None:
        return items

    tab_container = container.select_one(".gtm-rankingTab")
    tabs = tab_container.find_all("button", recursive=False) if tab_container else []
    panels = container.find_all(
        "div", class_=lambda value: value and "ranking_slidePanel" in value
    )
    daily_index = next(
        (
            index
            for index, tab in enumerate(tabs)
            if sanitize_text(
                (tab.select_one('[data-text="Daily"]') or tab).get_text(" ", strip=True)
            )
            == "Daily"
        ),
        None,
    )
    if daily_index is None or len(tabs) != len(panels) or daily_index >= len(panels):
        return items
    if not any("active" in class_name for class_name in tabs[daily_index].get("class", [])):
        return items

    daily_list = panels[daily_index].find(
        "section", class_=lambda value: value and "rankingList" in value
    )
    if daily_list is None:
        return items

    expected_rank = 1
    for a_tag in daily_list.find_all("a", href=True):
        position = a_tag.find(
            class_=lambda value: value and "rankingPosition" in value
        )
        if position is None:
            continue
        if _parse_rank_number(position.get_text(strip=True)) != expected_rank:
            return []

        link = to_absolute_url(ranking_url, a_tag.get("href"))
        if "gizmodo.jp" not in link:
            return []
        path = urlparse(link).path or ""
        if any(excluded in path for excluded in ("/tag/", "/issue/", "/author/")):
            return []
        if not re.search(r"/(article/|\d{4}/\d{2}/)", path):
            return []
        title_node = a_tag.find(class_=lambda value: value and "rankingTitle" in value)
        title = title_node.get_text(" ", strip=True) if title_node else a_tag.get_text(" ", strip=True)
        append_ranking_item(items, seen, title, link, ranking_url, 10)
        if len(items) != expected_rank:
            return []
        expected_rank += 1
        if expected_rank > MAX_RANKING_ITEMS:
            break
    return items if expected_rank == MAX_RANKING_ITEMS + 1 else []


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
    heading = next(
        (
            heading
            for heading in soup.find_all(["h1", "h2"])
            if sanitize_text(heading.get_text(" ", strip=True)) == "トップ100"
        ),
        None,
    )
    if heading is None:
        return []

    section = next(
        (
            parent
            for parent in heading.parents
            if parent.select_one('[data-testid="weekly"]')
            and parent.select_one('[data-testid="monthly"]')
            and parent.select_one(".si7p730")
        ),
        None,
    )
    if section is None:
        return []

    weekly = section.select_one('[data-testid="weekly"]')
    monthly = section.select_one('[data-testid="monthly"]')
    if (
        weekly is None
        or monthly is None
        or weekly.parent is not monthly.parent
        or "s3r3r52" not in weekly.get("class", [])
        or "s3r3r52" in monthly.get("class", [])
    ):
        return []

    tabs = weekly.parent.find_all(attrs={"data-testid": ["weekly", "monthly"]}, recursive=False)
    weekly_index = tabs.index(weekly)
    ranking_roots = section.select("._7rl1co1")
    if len(ranking_roots) == 1:
        ranking_root = ranking_roots[0]
    elif len(ranking_roots) == len(tabs):
        ranking_root = ranking_roots[weekly_index]
    else:
        return []

    items = []
    seen = set()
    for expected_rank, block in enumerate(
        ranking_root.select(".si7p730")[:MAX_RANKING_ITEMS], start=1
    ):
        rank_node = block.find("p")
        if rank_node is None or _parse_rank_number(rank_node.get_text(strip=True)) != expected_rank:
            return []

        image_link = block.find("a", href=lambda href: href and href.startswith("/article/"))
        wrapper = block.parent
        title_node = wrapper.select_one("p.si7p732") if wrapper else None
        title_link = title_node.find_parent("a", href=True) if title_node else None
        if (
            image_link is None
            or title_link is None
            or image_link.get("href") != title_link.get("href")
        ):
            return []

        append_ranking_item(
            items,
            seen,
            title_node.get_text(" ", strip=True),
            title_link.get("href"),
            ranking_url,
            10,
        )
        if len(items) != expected_rank:
            return []
    return items if len(items) == MAX_RANKING_ITEMS else []


def extract_nikkei_ranking(soup, ranking_url):
    items = []
    seen = set()
    container = soup.select_one(".m-miM32")
    if container is None:
        return items
    title_node = container.select_one(".m-miM32_title")
    current_node = container.select_one(".m-miM32_pulldownCurrentText")
    if title_node is None or current_node is None or title_node.get_text(strip=True) != "総合" or current_node.get_text(strip=True) != "今日":
        return []
    for expected_rank, item in enumerate(
        container.select(".m-miM32_item")[:MAX_RANKING_ITEMS], start=1
    ):
        rank_node = item.select_one(".m-miM32_itemNum")
        a_tag = item.select_one('.m-miM32_itemTitleText a[href*="/article/"]')
        if (
            rank_node is None
            or a_tag is None
            or _parse_rank_number(rank_node.get_text(strip=True)) != expected_rank
        ):
            return []
        append_ranking_item(items, seen, a_tag.get_text(strip=True), a_tag.get("href"), ranking_url, 10)
        if len(items) != expected_rank:
            return []
    return items if len(items) == MAX_RANKING_ITEMS else []


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
    "nikkei": extract_nikkei_ranking,
    "bbc": extract_bbc_ranking,
    "prtimes": extract_prtimes_ranking,
    "yahoo_news": extract_yahoo_news_ranking,
}


def fetch_scrape_news(session, site):
    """Fetch news items from a site via HTML scraping (non-RSS)."""
    url = site.get("url")
    scrape_type = site.get("scrape_type")
    if not url or not scrape_type:
        return build_fetch_result(status="skipped", detail="missing url or scrape_type")

    extractor = SCRAPE_NEWS_EXTRACTORS.get(scrape_type)
    if not extractor:
        return build_fetch_result(status="parse_error", detail=f"unknown scrape_type='{scrape_type}'")

    try:
        resp = session.get(
            url,
            headers={"Accept": HTML_ACCEPT},
            timeout=REQUEST_TIMEOUT,
        )
        resp.raise_for_status()
    except requests.exceptions.RequestException as exc:
        return build_fetch_result(status="http_error", detail=summarize_error(exc, url))

    try:
        soup = BeautifulSoup(resp.content, "html.parser")
        items = extractor(soup, url)
    except Exception as exc:
        return build_fetch_result(status="parse_error", detail=summarize_error(exc, url))

    items = items[:MAX_ITEMS_PER_SITE]
    if not items:
        return build_fetch_result(status="empty", detail="0 items after filtering")
    return build_fetch_result(items=items)


def fetch_ranking(session, site):
    """Fetch ranking/popular articles for a site via scraping."""
    ranking_url = site.get("ranking_url")
    ranking_type = site.get("ranking_type")
    if not ranking_url or not ranking_type:
        return build_fetch_result(status="skipped", detail="missing ranking_url or ranking_type")

    extractor = RANKING_EXTRACTORS.get(ranking_type)
    if not extractor:
        return build_fetch_result(status="parse_error", detail=f"unknown ranking_type='{ranking_type}'")

    try:
        resp = session.get(
            ranking_url,
            headers={"Accept": HTML_ACCEPT},
            timeout=REQUEST_TIMEOUT,
        )
        resp.raise_for_status()
    except requests.exceptions.RequestException as exc:
        return build_fetch_result(status="http_error", detail=summarize_error(exc, ranking_url))

    try:
        if ranking_type == "itmedia":
            content = resp.content.decode("cp932", errors="replace")
        else:
            content = resp.content
        soup = BeautifulSoup(content, "html.parser")
        items = extractor(soup, ranking_url)
    except Exception as exc:
        return build_fetch_result(status="parse_error", detail=summarize_error(exc, ranking_url))

    items = items[:MAX_RANKING_ITEMS]
    if not items:
        return build_fetch_result(status="empty", detail=f"parser '{ranking_type}' returned 0 items")
    return build_fetch_result(items=items)


def _extract_json_array_from_text(text):
    """Extract the first JSON array from model output text."""
    decoder = json.JSONDecoder()
    text = (text or "").strip()
    if not text:
        return None

    candidates = [text]

    fenced_match = re.search(r"```(?:json)?\s*([\s\S]*?)\s*```", text, flags=re.IGNORECASE)
    if fenced_match:
        candidates.append(fenced_match.group(1).strip())

    for candidate in candidates:
        try:
            loaded = json.loads(candidate)
            if isinstance(loaded, list):
                return loaded
        except json.JSONDecodeError:
            pass

    for idx, char in enumerate(text):
        if char != "[":
            continue
        try:
            loaded, _ = decoder.raw_decode(text[idx:])
            if isinstance(loaded, list):
                return loaded
        except json.JSONDecodeError:
            continue
    return None


def _normalize_sns_post(post):
    """Normalize SNS post shape and discard invalid entries."""
    if not isinstance(post, dict):
        return None

    author = post.get("author", "")
    content = post.get("content", "")
    url = post.get("url", "")

    if not isinstance(author, str):
        author = ""
    if not isinstance(content, str):
        return None
    if not isinstance(url, str):
        url = ""

    author = sanitize_text(author)
    content = sanitize_text(content)
    url = url.strip()

    if not content:
        return None
    if url and not url.lower().startswith(("http://", "https://")):
        url = ""

    return {"author": author, "content": content, "url": url}


def _extract_sns_output_texts(data):
    """Collect output text blocks from xAI response payload."""
    texts = []
    for item in data.get("output", []):
        if item.get("type") != "message" or item.get("role") != "assistant":
            continue
        for block in item.get("content", []):
            if block.get("type") == "output_text" and isinstance(block.get("text"), str):
                texts.append(block["text"])
    return texts


def fetch_sns_posts(session, category):
    """Fetch trending X posts for a single SNS category via xAI Grok API."""
    api_key = os.environ.get("XAI_API_KEY", "")
    if not api_key:
        print(f"[SNS SKIP] XAI_API_KEY not set, skipping {category['label']}")
        return []

    resp = None
    for attempt in range(1, SNS_API_RETRY_TOTAL + 1):
        try:
            resp = session.post(
                "https://api.x.ai/v1/responses",
                headers={
                    "Content-Type": "application/json",
                    "Authorization": f"Bearer {api_key}",
                },
                json={
                    "model": os.environ.get("XAI_MODEL") or DEFAULT_XAI_MODEL,
                    "input": [{"role": "user", "content": category["prompt"]}],
                    "tools": [{"type": "x_search"}],
                    "temperature": 0.7,
                },
                timeout=120,
            )
            resp.raise_for_status()
            break
        except requests.exceptions.RequestException as exc:
            if attempt == SNS_API_RETRY_TOTAL:
                print(f"[SNS ERROR] {category['label']} API request failed: {exc}")
                return []
            wait_seconds = RETRY_BACKOFF * (2 ** (attempt - 1))
            print(
                f"[SNS WARN] {category['label']} API request failed on attempt {attempt}. "
                f"Retrying in {wait_seconds:.1f}s..."
            )
            time.sleep(wait_seconds)

    try:
        data = resp.json()
        output_texts = _extract_sns_output_texts(data)
        if not output_texts:
            print(f"[SNS WARN] {category['label']} no output_text found in response")
            return []

        for output_text in output_texts:
            posts = _extract_json_array_from_text(output_text)
            if posts is None:
                continue

            normalized_posts = []
            for post in posts:
                normalized = _normalize_sns_post(post)
                if normalized:
                    normalized_posts.append(normalized)
            return normalized_posts

        print(f"[SNS WARN] {category['label']} JSON array not found in model output")
        return []
    except (ValueError, KeyError, json.JSONDecodeError) as exc:
        print(f"[SNS ERROR] {category['label']} response parse failed: {exc}")
        return []


def fetch_all_sns(session):
    """Fetch SNS posts for all categories. Returns list of category dicts."""
    results = []
    for cat in SNS_CATEGORIES:
        print(f"Fetching SNS: {cat['label']} ...")
        posts = fetch_sns_posts(session, cat)
        print(f"  -> {len(posts)} posts")
        results.append({
            "key": cat["key"],
            "label": cat["label"],
            "badge": cat["badge"],
            "accent_color": cat["accent_color"],
            "icon_gradient": cat["icon_gradient"],
            "posts": posts,
        })
    return results


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
    """Build display categories from explicit merge definitions."""
    display_categories = []

    for display in DISPLAY_CATEGORIES:
        bucket = {
            "label": display["label"],
            "color": display["color"],
            "sites": [],
            "total": 0,
            "source_count": 0,
        }
        for source_cat in display["source_categories"]:
            cat_bucket = category_data.get(source_cat)
            if cat_bucket is None:
                print(f"[CONFIG WARN] source category '{source_cat}' not found for display '{display['key']}'")
                continue
            bucket["sites"].extend(cat_bucket["sites"])
            bucket["total"] += cat_bucket["total"]
            bucket["source_count"] += len(cat_bucket["sites"])
        display_categories.append(bucket)

    return display_categories


def _write_tmp(path, text):
    """Write text to a synced temporary file beside its final destination."""
    tmp_path = f"{path}.tmp"
    with open(tmp_path, "w", encoding="utf-8") as file_obj:
        file_obj.write(text)
        file_obj.flush()
        os.fsync(file_obj.fileno())
    return tmp_path


def _replace_all(pairs):
    """Replace final files with prepared temporary files in order."""
    for tmp_path, final_path in pairs:
        os.replace(tmp_path, final_path)


def run(session=None, output_dir=None):
    """Fetch all sources, enforce the quality gate, and write dashboard files."""
    owns_session = session is None
    if session is None:
        session = build_http_session()

    category_data = init_category_data()
    ranking_data = []
    ranking_total_sources = sum(
        1 for site in SITES if site.get("ranking_url") or site.get("ranking_type")
    )
    ranking_success_sources = 0
    source_status = []

    try:
        for site in SITES:
            cat = site["category"]
            print(f"Fetching: {site['name']} ...")
            if site.get("type") == "scrape":
                kind = "scrape"
                result = fetch_scrape_news(session, site)
            else:
                kind = "feed"
                result = fetch_feed(session, site)
            items = result["items"]
            print(f"  -> {len(items)} items")
            source_status.append({
                "name": site["name"],
                "kind": kind,
                "status": result["status"],
                "count": len(items),
                "detail": result["detail"],
            })
            if result["status"] != "ok":
                print(f"[FEED FAIL] {site['name']}: {result['status']} {result['detail']}")
            else:
                category_data[cat]["sites"].append(build_site_view_model(site, items))
                category_data[cat]["total"] += len(items)

            if site.get("ranking_url") or site.get("ranking_type"):
                print(f"  Fetching ranking: {site['name']} ...")
                ranking_result = fetch_ranking(session, site)
                ranking_items = ranking_result["items"]
                print(f"  -> {len(ranking_items)} ranking items")
                source_status.append({
                    "name": site["name"],
                    "kind": "ranking",
                    "status": ranking_result["status"],
                    "count": len(ranking_items),
                    "detail": ranking_result["detail"],
                })
                if ranking_result["status"] != "ok":
                    print(
                        f"[RANKING FAIL] {site['name']}: "
                        f"{ranking_result['status']} {ranking_result['detail']}"
                    )
                else:
                    ranking_data.append(build_site_view_model(site, ranking_items))
                    ranking_success_sources += 1

        display_categories = build_display_categories(category_data)
        overall_total = sum(category["total"] for category in display_categories)
        min_total_items = int(os.environ.get("NEWS_MIN_TOTAL_ITEMS", MIN_TOTAL_ITEMS))
        if overall_total < min_total_items:
            print(
                f"[GATE FAIL] overall_total={overall_total} < "
                f"MIN_TOTAL_ITEMS={min_total_items}; not writing docs/"
            )
            raise SystemExit(1)

        if ranking_total_sources and ranking_success_sources == 0:
            print(f"[RANKING ALL FAIL] all {ranking_total_sources} ranking sources failed")

        # Fetch SNS data
        sns_data = fetch_all_sns(session)

        project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        template_dir = os.path.join(project_root, "templates")
        env = Environment(loader=FileSystemLoader(template_dir), autoescape=True)
        template = env.get_template("index.html.j2")

        now_jst = datetime.now(JST)
        ranking_failed_names = [
            f"{row['name']} ({row['status']})"
            for row in source_status
            if row["kind"] == "ranking" and row["status"] != "ok"
        ]
        ranking_status = {
            "total_sources": ranking_total_sources,
            "success_sources": ranking_success_sources,
            "failed_sources": ranking_total_sources - ranking_success_sources,
            "failed_names": ranking_failed_names,
            "updated_at": now_jst.strftime("%Y-%m-%d %H:%M JST"),
        }
        feed_status_by_name = {
            row["name"]: {"status": row["status"], "detail": row["detail"]}
            for row in source_status
            if row["kind"] != "ranking"
        }
        html = template.render(
            display_categories=display_categories,
            overall_total=overall_total,
            all_sites=SITES,
            ranking_data=ranking_data,
            ranking_status=ranking_status,
            source_status=source_status,
            feed_status_by_name=feed_status_by_name,
            sns_data=sns_data,
            bookmarks=BOOKMARKS,
            updated_at=now_jst.strftime("%Y-%m-%d %H:%M JST"),
        )

        docs_dir = output_dir or os.path.join(project_root, "docs")
        os.makedirs(docs_dir, exist_ok=True)
        status_payload = {
            "generated_at": now_jst.isoformat(timespec="seconds"),
            "gate": {
                "passed": True,
                "overall_total": overall_total,
                "min_total_items": min_total_items,
            },
            "feeds": {
                "total_sources": sum(1 for row in source_status if row["kind"] != "ranking"),
                "ok_sources": sum(
                    1 for row in source_status if row["kind"] != "ranking" and row["status"] == "ok"
                ),
            },
            "rankings": {
                "total_sources": ranking_total_sources,
                "ok_sources": ranking_success_sources,
            },
            "sources": source_status,
        }
        output_path = os.path.join(docs_dir, "index.html")
        status_path = os.path.join(docs_dir, "status.json")
        status_text = json.dumps(status_payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
        index_tmp = f"{output_path}.tmp"
        status_tmp = f"{status_path}.tmp"
        try:
            index_tmp = _write_tmp(output_path, html)
            status_tmp = _write_tmp(status_path, status_text)
        except Exception:
            for tmp_path in (index_tmp, status_tmp):
                if os.path.exists(tmp_path):
                    os.unlink(tmp_path)
            raise
        _replace_all([(index_tmp, output_path), (status_tmp, status_path)])

        print(f"\nGenerated: {output_path}")
        print(f"Status: {status_path}")
        print(f"Updated at: {now_jst.strftime('%Y-%m-%d %H:%M JST')}")
        return status_payload
    finally:
        if owns_session:
            session.close()


def main():
    run()


if __name__ == "__main__":
    main()
