#!/usr/bin/env python3
"""Fetch RSS feeds and generate the news dashboard HTML."""

import os
import sys
from datetime import datetime, timezone, timedelta

import feedparser
import requests
from jinja2 import Environment, FileSystemLoader

# Add scripts directory to path so config can be imported
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from config import SITES, CATEGORIES, MAX_ITEMS_PER_SITE

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

    for site in SITES:
        cat = site["category"]
        print(f"Fetching: {site['name']} ...")
        items = fetch_feed(site)
        print(f"  -> {len(items)} items")
        if items:
            category_data[cat]["sites"].append({
                "name": site["name"],
                "items": items,
            })
            category_data[cat]["total"] += len(items)

    # Render HTML
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    template_dir = os.path.join(project_root, "templates")
    env = Environment(loader=FileSystemLoader(template_dir), autoescape=True)
    template = env.get_template("index.html.j2")

    now_jst = datetime.now(JST)
    html = template.render(
        categories=CATEGORIES,
        category_data=category_data,
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
