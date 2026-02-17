SITES = [
    # テック・AI系
    {
        "name": "TechCrunch", "url": "https://techcrunch.com/feed/",
        "category": "tech", "type": "rss",
        "icon": "TC", "css_class": "techcrunch", "domain": "techcrunch.com", "badge": "TECH",
        "site_url": "https://techcrunch.com",
        "icon_gradient": "linear-gradient(135deg, #0a9e01, #23bf1f)",
        "accent_color": "#0a9e01",
        "ranking_url": "https://techcrunch.com/",
        "ranking_type": "techcrunch",
    },
    {
        "name": "ITmedia", "url": "https://rss.itmedia.co.jp/rss/2.0/itmedia_all.xml",
        "category": "tech", "type": "rss",
        "icon": "IT", "css_class": "itmedia", "domain": "itmedia.co.jp", "badge": "TECH",
        "site_url": "https://www.itmedia.co.jp",
        "icon_gradient": "linear-gradient(135deg, #e60012, #ff3333)",
        "accent_color": "#e60012",
        "ranking_url": "https://www.itmedia.co.jp/ranking/",
        "ranking_type": "itmedia",
    },
    {
        "name": "GIZMODO JAPAN", "url": "https://www.gizmodo.jp/index.xml",
        "category": "tech", "type": "rss",
        "icon": "GZ", "css_class": "gizmodo", "domain": "gizmodo.jp", "badge": "TECH",
        "site_url": "https://www.gizmodo.jp",
        "icon_gradient": "linear-gradient(135deg, #2b2b2b, #555)",
        "accent_color": "#2b2b2b",
        "ranking_url": "https://www.gizmodo.jp/",
        "ranking_type": "gizmodo",
    },
    {
        "name": "The Verge", "url": "https://www.theverge.com/rss/index.xml",
        "category": "tech", "type": "rss",
        "icon": "TV", "css_class": "theverge", "domain": "theverge.com", "badge": "TECH",
        "site_url": "https://www.theverge.com",
        "icon_gradient": "linear-gradient(135deg, #6366f1, #818cf8)",
        "accent_color": "#6366f1",
        "ranking_url": "https://www.theverge.com/",
        "ranking_type": "theverge",
    },
    {
        "name": "AI News", "url": "https://www.artificialintelligence-news.com/feed/rss/",
        "category": "tech", "type": "rss",
        "icon": "AI", "css_class": "ainews", "domain": "artificialintelligence-news.com", "badge": "AI",
        "site_url": "https://www.artificialintelligence-news.com",
        "icon_gradient": "linear-gradient(135deg, #0ea5e9, #38bdf8)",
        "accent_color": "#0ea5e9",
    },
    {
        "name": "CryptoSlate", "url": "https://cryptoslate.com/feed/",
        "category": "tech", "type": "rss",
        "icon": "CS", "css_class": "cryptoslate", "domain": "cryptoslate.com", "badge": "CRYPTO",
        "site_url": "https://cryptoslate.com",
        "icon_gradient": "linear-gradient(135deg, #1e40af, #3b82f6)",
        "accent_color": "#1e40af",
    },
    {
        "name": "Hacker News", "url": "https://news.ycombinator.com/rss",
        "category": "tech", "type": "rss",
        "icon": "HN", "css_class": "hackernews", "domain": "news.ycombinator.com", "badge": "TECH",
        "site_url": "https://news.ycombinator.com",
        "icon_gradient": "linear-gradient(135deg, #f97316, #fb923c)",
        "accent_color": "#f97316",
        "ranking_url": "https://news.ycombinator.com/best",
        "ranking_type": "hackernews",
    },

    # ファッション・デザイン系
    {
        "name": "FASHIONSNAP", "url": "https://www.fashionsnap.com/rss.xml",
        "category": "fashion", "type": "rss",
        "icon": "FS", "css_class": "fashionsnap", "domain": "fashionsnap.com", "badge": "FASHION",
        "site_url": "https://www.fashionsnap.com",
        "icon_gradient": "linear-gradient(135deg, #be185d, #ec4899)",
        "accent_color": "#be185d",
        "ranking_url": "https://www.fashionsnap.com/ranking/",
        "ranking_type": "fashionsnap",
    },
    {
        "name": "designboom", "url": "https://www.designboom.com/feed/",
        "category": "fashion", "type": "rss",
        "icon": "db", "css_class": "designboom", "domain": "designboom.com", "badge": "DESIGN",
        "site_url": "https://www.designboom.com",
        "icon_gradient": "linear-gradient(135deg, #d97706, #f59e0b)",
        "accent_color": "#d97706",
    },
    {
        "name": "WWDJAPAN", "url": "https://www.wwdjapan.com/feed",
        "category": "fashion", "type": "rss",
        "icon": "WD", "css_class": "wwdjapan", "domain": "wwdjapan.com", "badge": "FASHION",
        "site_url": "https://www.wwdjapan.com",
        "icon_gradient": "linear-gradient(135deg, #1a1a1a, #444)",
        "accent_color": "#1a1a1a",
        "ranking_url": "https://www.wwdjapan.com/ranking",
        "ranking_type": "wwdjapan",
    },
    {
        "name": "JDN", "url": "https://www.japandesign.ne.jp/feed/",
        "category": "fashion", "type": "rss",
        "icon": "JD", "css_class": "jdn", "domain": "japandesign.ne.jp", "badge": "DESIGN",
        "site_url": "https://www.japandesign.ne.jp",
        "icon_gradient": "linear-gradient(135deg, #2563eb, #60a5fa)",
        "accent_color": "#2563eb",
        "ranking_url": "https://www.japandesign.ne.jp/ranking/",
        "ranking_type": "jdn",
    },

    # 経済・ビジネス系
    {
        "name": "日経新聞", "url": "https://assets.wor.jp/rss/rdf/nikkei/news.rdf",
        "category": "business", "type": "rss",
        "icon": "NK", "css_class": "nikkei", "domain": "nikkei.com", "badge": "BIZ",
        "site_url": "https://www.nikkei.com",
        "icon_gradient": "linear-gradient(135deg, #0369a1, #0ea5e9)",
        "accent_color": "#0369a1",
        "ranking_url": "https://www.nikkei.com/access/",
        "ranking_type": "nikkei",
    },

    {
        "name": "NADA NEWS", "url": "https://www.nadanews.com/feed/",
        "category": "business", "type": "rss",
        "icon": "ND", "css_class": "nadanews", "domain": "nadanews.com", "badge": "BIZ",
        "site_url": "https://www.nadanews.com",
        "icon_gradient": "linear-gradient(135deg, #059669, #34d399)",
        "accent_color": "#059669",
    },

    # テック・AI系（追加）
    {
        "name": "WIRED JAPAN", "url": "https://wired.jp/feed/rss",
        "category": "tech", "type": "rss",
        "icon": "WI", "css_class": "wiredjp", "domain": "wired.jp", "badge": "TECH",
        "site_url": "https://wired.jp",
        "icon_gradient": "linear-gradient(135deg, #111, #333)",
        "accent_color": "#111111",
    },

    # 一般ニュース
    {
        "name": "BBC News", "url": "https://feeds.bbci.co.uk/news/rss.xml",
        "category": "general", "type": "rss",
        "icon": "BBC", "css_class": "bbc", "domain": "bbc.co.uk", "badge": "NEWS",
        "site_url": "https://www.bbc.co.uk/news",
        "icon_gradient": "linear-gradient(135deg, #991b1b, #dc2626)",
        "accent_color": "#991b1b",
        "ranking_url": "https://www.bbc.com/news",
        "ranking_type": "bbc",
    },
]

CATEGORIES = {
    "tech": {"label": "テック・AI", "color": "#6366f1"},
    "fashion": {"label": "ファッション・デザイン", "color": "#ec4899"},
    "business": {"label": "ニュース・ビジネス", "color": "#0ea5e9"},
    "general": {"label": "ニュース・ビジネス", "color": "#0ea5e9"},
}

MAX_ITEMS_PER_SITE = 8
MAX_RANKING_ITEMS = 5
