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

    # PR
    {
        "name": "PR TIMES", "url": "https://prtimes.jp/ranking/",
        "category": "business", "type": "scrape", "scrape_type": "prtimes_news",
        "icon": "PR", "css_class": "prtimes", "domain": "prtimes.jp", "badge": "PR",
        "site_url": "https://prtimes.jp",
        "icon_gradient": "linear-gradient(135deg, #0072bc, #00a0e9)",
        "accent_color": "#0072bc",
        "ranking_url": "https://prtimes.jp/ranking/",
        "ranking_type": "prtimes",
    },

    # Yahoo!ニュース
    {
        "name": "Yahoo!ニュース", "url": "https://news.yahoo.co.jp/",
        "category": "general", "type": "scrape", "scrape_type": "yahoo_news",
        "icon": "Y!", "css_class": "yahoonews", "domain": "news.yahoo.co.jp", "badge": "NEWS",
        "site_url": "https://news.yahoo.co.jp",
        "icon_gradient": "linear-gradient(135deg, #ff0033, #ff4466)",
        "accent_color": "#ff0033",
        "ranking_url": "https://news.yahoo.co.jp/ranking/access/news",
        "ranking_type": "yahoo_news",
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

# SNS (X/Twitter) categories fetched via xAI Grok API
SNS_CATEGORIES = [
    {
        "key": "jp_trending",
        "label": "日本で話題",
        "badge": "JP",
        "accent_color": "#ef4444",
        "icon_gradient": "linear-gradient(135deg, #ef4444, #f87171)",
        "prompt": (
            "あなたはX（旧Twitter）のトレンドアナリストです。\n"
            "日本国内で直近24時間に話題になっている注目ポストを調査してください。\n\n"
            "要件:\n"
            "- 話題性・重要度の高いポストを8〜10件選出\n"
            "- 各ポストの投稿者名、内容の要約、ポストURLを含める\n"
            "- リプライや宣伝ポストは除外し、情報価値の高いものを優先\n"
            "- 日本語のポストを対象とする\n\n"
            "以下のJSON形式のみ出力してください:\n"
            '[{"author":"表示名 (@ユーザー名)","content":"ポスト内容の要約（100字以内）","url":"ポストのURL"}]'
        ),
    },
    {
        "key": "global_trending",
        "label": "海外で話題",
        "badge": "GLOBAL",
        "accent_color": "#10b981",
        "icon_gradient": "linear-gradient(135deg, #10b981, #34d399)",
        "prompt": (
            "You are an X (Twitter) trend analyst.\n"
            "Find notable posts trending globally in the last 24 hours.\n\n"
            "Requirements:\n"
            "- Select 8-10 high-impact, newsworthy posts\n"
            "- Include author name, content summary, and post URL\n"
            "- Exclude replies and promotional posts; prioritize informational value\n"
            "- Focus on English-language posts\n\n"
            "Output ONLY the following JSON format:\n"
            '[{"author":"Display Name (@username)","content":"Post summary (under 100 chars)","url":"Post URL"}]'
        ),
    },
    {
        "key": "ai_jp",
        "label": "AI (日本語)",
        "badge": "AI-JP",
        "accent_color": "#8b5cf6",
        "icon_gradient": "linear-gradient(135deg, #8b5cf6, #a78bfa)",
        "prompt": (
            "あなたはX（旧Twitter）のAI分野トレンドアナリストです。\n"
            "AI・機械学習・LLMに関する直近24時間の注目ポストを調査してください。\n\n"
            "選定基準（厳守）:\n"
            "- いいね数やRT数が多く、広く拡散されているポストのみ選出\n"
            "- 以下のようなニュースバリューがあるものを優先:\n"
            "  - 新モデル・新サービスのリリース発表\n"
            "  - 大手企業のAI関連の重要発表\n"
            "  - 注目の研究論文・ベンチマーク結果\n"
            "  - 業界に影響を与える規制・政策の動き\n"
            "  - 著名な研究者・開発者による重要な知見\n"
            "- 8〜10件選出\n\n"
            "除外対象:\n"
            "- エンゲージメントが低い個人の感想・日常的なつぶやき\n"
            "  （ただしバズっている感想・レビュー・「試してみた」系は選出OK）\n"
            "- アフィリエイト・有料note誘導・セミナー宣伝\n"
            "- リプライ・引用RTのみのポスト\n"
            "- フォロワー数が少なくエンゲージメントも低いポスト\n\n"
            "日本語のポストを対象とする。\n\n"
            "以下のJSON形式のみ出力してください:\n"
            '[{"author":"表示名 (@ユーザー名)","content":"ポスト内容の要約（100字以内）","url":"ポストのURL"}]'
        ),
    },
    {
        "key": "ai_en",
        "label": "AI (English)",
        "badge": "AI-EN",
        "accent_color": "#8b5cf6",
        "icon_gradient": "linear-gradient(135deg, #8b5cf6, #a78bfa)",
        "prompt": (
            "You are an X (Twitter) AI trend analyst.\n"
            "Find notable posts about AI, machine learning, and LLMs from the last 24 hours.\n\n"
            "Selection criteria (strict):\n"
            "- ONLY select posts with high engagement (many likes/retweets)\n"
            "- Prioritize posts with real news value:\n"
            "  - New model/product launches and announcements\n"
            "  - Major company AI announcements\n"
            "  - Breakthrough research papers and benchmark results\n"
            "  - Significant regulatory or policy developments\n"
            "  - Key insights from prominent researchers/engineers\n"
            "- Select 8-10 posts\n\n"
            "Exclude:\n"
            "- Low-engagement personal opinions and casual commentary\n"
            "  (However, viral reviews/impressions/'just tried X' posts with high engagement ARE welcome)\n"
            "- Promotional content, course/newsletter ads, affiliate links\n"
            "- Replies and quote tweets\n"
            "- Low-follower accounts with minimal engagement\n\n"
            "Focus on English-language posts.\n\n"
            "Output ONLY the following JSON format:\n"
            '[{"author":"Display Name (@username)","content":"Post summary (under 100 chars)","url":"Post URL"}]'
        ),
    },
    {
        "key": "blockchain",
        "label": "ブロックチェーン",
        "badge": "CHAIN",
        "accent_color": "#f59e0b",
        "icon_gradient": "linear-gradient(135deg, #f59e0b, #fbbf24)",
        "prompt": (
            "あなたはX（旧Twitter）のブロックチェーン分野トレンドアナリストです。\n"
            "ブロックチェーン・DeFi・Web3に関する直近24時間の注目ポストを調査してください。\n\n"
            "選定基準（厳守）:\n"
            "- いいね数やRT数が多く、広く拡散されているポストのみ選出\n"
            "- 以下のようなニュースバリューがあるものを優先:\n"
            "  - プロトコルの大型アップデート・ローンチ\n"
            "  - 大手企業・VCの投資・提携発表\n"
            "  - 規制・法整備に関する重要な動き\n"
            "  - セキュリティインシデント・ハッキング事案\n"
            "  - 技術的に重要なブレイクスルー\n"
            "- 8〜10件選出\n\n"
            "除外対象:\n"
            "- 単純な価格予想・価格速報（「BTC○○ドル突破」など）\n"
            "- 煽り系・FOMO誘発ポスト（「まだ間に合う」「100x確定」など）\n"
            "- エアドロップ告知・ギブアウェイ・アフィリエイト\n"
            "- リプライ・引用RTのみのポスト\n"
            "- フォロワー数が少なくエンゲージメントも低いポスト\n\n"
            "日本語・英語両方のポストを対象とする。\n\n"
            "以下のJSON形式のみ出力してください:\n"
            '[{"author":"表示名 (@ユーザー名)","content":"ポスト内容の要約（100字以内）","url":"ポストのURL"}]'
        ),
    },
]
