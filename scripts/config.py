SITES = [
    # テック・AI系
    {"name": "TechCrunch", "url": "https://techcrunch.com/feed/", "category": "tech", "type": "rss"},
    {"name": "ITmedia", "url": "https://rss.itmedia.co.jp/rss/2.0/itmedia_all.xml", "category": "tech", "type": "rss"},
    {"name": "GIZMODO JAPAN", "url": "https://www.gizmodo.jp/feed/atom", "category": "tech", "type": "rss"},
    {"name": "The Verge", "url": "https://www.theverge.com/rss/index.xml", "category": "tech", "type": "rss"},
    {"name": "AI News", "url": "https://www.artificialintelligence-news.com/feed/rss/", "category": "tech", "type": "rss"},
    {"name": "CryptoSlate", "url": "https://cryptoslate.com/feed/", "category": "tech", "type": "rss"},
    {"name": "Hacker News", "url": "https://news.ycombinator.com/rss", "category": "tech", "type": "rss"},

    # ファッション・デザイン系
    {"name": "FASHIONSNAP", "url": "https://www.fashionsnap.com/rss.xml", "category": "fashion", "type": "rss"},
    {"name": "designboom", "url": "https://www.designboom.com/feed/", "category": "fashion", "type": "rss"},
    # WWDJAPAN, JDN → Phase 2で追加（RSS未確認）

    # 経済・ビジネス系
    {"name": "日経新聞", "url": "https://assets.wor.jp/rss/rdf/nikkei/news.rdf", "category": "business", "type": "rss"},
    # NADA NEWS → Phase 2で追加（RSS未確認）

    # 一般ニュース
    {"name": "BBC News", "url": "https://feeds.bbci.co.uk/news/rss.xml", "category": "general", "type": "rss"},
]

CATEGORIES = {
    "tech": {"label": "テック・AI", "color": "#8b5cf6"},       # 紫
    "fashion": {"label": "ファッション・デザイン", "color": "#ec4899"},  # ピンク
    "business": {"label": "経済・ビジネス", "color": "#10b981"},  # グリーン
    "general": {"label": "一般ニュース", "color": "#f59e0b"},    # オレンジ
}

MAX_ITEMS_PER_SITE = 8
