#!/usr/bin/env python3
"""Fetch RSS feeds and generate the news dashboard HTML."""

import os
import re
import sys
from datetime import datetime, timezone, timedelta

import feedparser
import requests
from bs4 import BeautifulSoup
from jinja2 import Environment, FileSystemLoader

# Add scripts directory to path so config can be imported
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from config import SITES, CATEGORIES, MAX_ITEMS_PER_SITE, MAX_RANKING_ITEMS

JST = timezone(timedelta(hours=9))
USER_AGENT = "NewsDashboard/1.0 (+https://github.com/Tomotaka-u/news-dashboard)"
REQUEST_TIMEOUT = 15


def fetch_feed(site):
    """Fetch and parse an RSS feed for a single site."""
    try:
        resp = requests.get(
            site["url"],
            headers={"User-Agent": USER_AGENT},
            timeout=REQUEST_TIMEOUT,
        )
        resp.raise_for_status()
        feed = feedparser.parse(resp.content)
        items = []
        for entry in feed.entries[:MAX_ITEMS_PER_SITE]:
            title = entry.get("title", "").strip()
            link = entry.get("link", "").strip()
            if title and link:
                items.append({"title": title, "link": link})
        return items
    except Exception as e:
        print(f"[ERROR] {site['name']}: {e}")
        return []


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

        # Detect encoding
        if ranking_type == "itmedia":
            content = resp.content.decode("shift_jis", errors="replace")
        else:
            content = resp.text

        soup = BeautifulSoup(content, "html.parser")
        items = []

        if ranking_type == "itmedia":
            # ITmedia: <h3> tags containing <a> links (skip first 2 which are template strings)
            for h3 in soup.find_all("h3"):
                a_tag = h3.find("a")
                if a_tag and a_tag.get("href") and a_tag.get_text(strip=True):
                    title = a_tag.get_text(strip=True)
                    link = a_tag["href"]
                    if title.startswith("'"):  # skip JS template strings
                        continue
                    items.append({"title": title, "link": link})
                    if len(items) >= MAX_RANKING_ITEMS:
                        break

        elif ranking_type == "hackernews":
            # Hacker News: class="titleline" containing <a>
            for span in soup.find_all("span", class_="titleline"):
                a_tag = span.find("a")
                if a_tag and a_tag.get("href") and a_tag.get_text(strip=True):
                    title = a_tag.get_text(strip=True)
                    link = a_tag["href"]
                    if not link.startswith("http"):
                        link = "https://news.ycombinator.com/" + link
                    items.append({"title": title, "link": link})
                    if len(items) >= MAX_RANKING_ITEMS:
                        break

        elif ranking_type == "fashionsnap":
            # FASHIONSNAP: article links matching /article/YYYY-
            seen = set()
            for a_tag in soup.find_all("a", href=True):
                href = a_tag["href"]
                if re.match(r"/article/\d{4}-", href):
                    text = a_tag.get_text(strip=True)
                    if text and len(text) > 10 and href not in seen:
                        seen.add(href)
                        link = "https://www.fashionsnap.com" + href
                        items.append({"title": text, "link": link})
                        if len(items) >= MAX_RANKING_ITEMS:
                            break

        elif ranking_type == "wwdjapan":
            # WWDJAPAN: article links
            seen = set()
            for a_tag in soup.find_all("a", href=True):
                href = a_tag["href"]
                if "articles/" in href:
                    text = a_tag.get_text(strip=True)
                    if text and len(text) > 10 and href not in seen:
                        seen.add(href)
                        if not href.startswith("http"):
                            href = "https://www.wwdjapan.com" + href
                        items.append({"title": text, "link": href})
                        if len(items) >= MAX_RANKING_ITEMS:
                            break

        return items
    except Exception as e:
        print(f"[RANKING ERROR] {site['name']}: {e}")
        return []


def main():
    # Collect articles grouped by category then by site
    category_data = {}
    for cat_key, cat_info in CATEGORIES.items():
        category_data[cat_key] = {
            "label": cat_info["label"],
            "color": cat_info["color"],
            "sites": [],
            "total": 0,
        }

    # Collect ranking data
    ranking_data = []

    for site in SITES:
        cat = site["category"]
        print(f"Fetching: {site['name']} ...")
        items = fetch_feed(site)
        print(f"  -> {len(items)} items")
        if items:
            category_data[cat]["sites"].append({
                "name": site["name"],
                "items": items,
                "icon": site.get("icon", "?"),
                "css_class": site.get("css_class", ""),
                "domain": site.get("domain", ""),
                "badge": site.get("badge", ""),
                "site_url": site.get("site_url", "#"),
                "icon_gradient": site.get("icon_gradient", "linear-gradient(135deg, #888, #aaa)"),
                "accent_color": site.get("accent_color", "#888"),
            })
            category_data[cat]["total"] += len(items)

        # Fetch ranking if configured
        if site.get("ranking_url"):
            print(f"  Fetching ranking: {site['name']} ...")
            ranking_items = fetch_ranking(site)
            print(f"  -> {len(ranking_items)} ranking items")
            if ranking_items:
                ranking_data.append({
                    "name": site["name"],
                    "items": ranking_items,
                    "icon": site.get("icon", "?"),
                    "css_class": site.get("css_class", ""),
                    "domain": site.get("domain", ""),
                    "badge": site.get("badge", ""),
                    "site_url": site.get("site_url", "#"),
                    "icon_gradient": site.get("icon_gradient", "linear-gradient(135deg, #888, #aaa)"),
                    "accent_color": site.get("accent_color", "#888"),
                })

    # Render HTML
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    template_dir = os.path.join(project_root, "templates")
    env = Environment(loader=FileSystemLoader(template_dir), autoescape=True)
    template = env.get_template("index.html.j2")

    now_jst = datetime.now(JST)
    html = template.render(
        categories=CATEGORIES,
        category_data=category_data,
        all_sites=SITES,
        ranking_data=ranking_data,
        updated_at=now_jst.strftime("%Y-%m-%d %H:%M JST"),
    )

    docs_dir = os.path.join(project_root, "docs")
    os.makedirs(docs_dir, exist_ok=True)
    output_path = os.path.join(docs_dir, "index.html")
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(html)

    print(f"\nGenerated: {output_path}")
    print(f"Updated at: {now_jst.strftime('%Y-%m-%d %H:%M JST')}")


if __name__ == "__main__":
    main()
