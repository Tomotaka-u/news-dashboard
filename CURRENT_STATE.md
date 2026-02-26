# news-dashboard 現状まとめ

最終確認日: 2026-02-26

---

## 概要

Python (feedparser + BeautifulSoup + Jinja2) で静的HTMLを生成し、GitHub Pages で配信するニュースダッシュボード。
GitHub Actions で1日2回（6:00 / 18:00 JST）自動更新。

---

## ファイル構成

```
news-dashboard/
├── scripts/
│   ├── config.py           # サイト設定・カテゴリ定義・SNSカテゴリ定義
│   ├── fetch_news.py       # メイン処理（RSS取得・スクレイピング・SNS取得・HTML生成）
│   └── requirements.txt
├── templates/
│   ├── index.html.j2       # メインテンプレート
│   └── partials/
│       ├── index.css       # スタイル
│       └── index.js        # クライアントサイドJS
├── docs/                   # GitHub Pages 公開ディレクトリ（生成物）
│   └── index.html
└── .github/workflows/
    └── update-news.yml     # 自動更新ワークフロー
```

---

## タブ構成（3タブ）

| タブ名 | 内容 |
|--------|------|
| Today's News | RSSフィード・スクレイピングによる最新記事 |
| Rankings | 各サイトの人気記事ランキング |
| SNS | xAI Grok API経由のXトレンドポスト |

---

## ニュースソース（config.py / SITES）

### テック・AI系
| サイト | 取得方法 | バッジ | アクセントカラー |
|--------|----------|--------|------------------|
| TechCrunch | RSS | TECH | #0a9e01 |
| ITmedia | RSS | TECH | #e60012 |
| GIZMODO JAPAN | RSS | TECH | #2b2b2b |
| The Verge | RSS | TECH | #6366f1 |
| AI News | RSS | AI | #0ea5e9 |
| WIRED JAPAN | RSS | TECH | #111111 |

### ファッション・デザイン系
| サイト | 取得方法 | バッジ | アクセントカラー |
|--------|----------|--------|------------------|
| FASHIONSNAP | RSS | FASHION | #be185d |
| designboom | RSS | DESIGN | #d97706 |
| WWDJAPAN | RSS | FASHION | #1a1a1a |
| JDN | RSS | DESIGN | #2563eb |

### 経済・ビジネス系
| サイト | 取得方法 | バッジ | アクセントカラー |
|--------|----------|--------|------------------|
| 日経新聞 | RSS | BIZ | #0369a1 |
| NADA NEWS | RSS | BIZ | #059669 |
| PR TIMES | scrape (prtimes_news) | PR | #0072bc |
| Yahoo!ニュース | scrape (yahoo_news) | NEWS | #ff0033 |
| BBC News | RSS | NEWS | #991b1b |
| CryptoSlate | RSS | CRYPTO | #1e40af |

### 設定値
- `MAX_ITEMS_PER_SITE = 8`（RSSフィード・スクレイピングの最大件数）
- `MAX_RANKING_ITEMS = 5`（ランキングの最大件数）

---

## ランキング対応サイト

ranking_url + ranking_type を持つサイトはランキング取得あり:

| サイト | ranking_type |
|--------|--------------|
| TechCrunch | techcrunch |
| ITmedia | itmedia |
| GIZMODO JAPAN | gizmodo |
| The Verge | theverge |
| Hacker News | hackernews |
| FASHIONSNAP | fashionsnap |
| WWDJAPAN | wwdjapan |
| 日経新聞 | nikkei |
| JDN | jdn |
| BBC News | bbc |
| PR TIMES | prtimes |
| Yahoo!ニュース | yahoo_news |

サイト固有パーサーが0件だった場合は `extract_generic_ranking` にフォールバック。

---

## 表示カテゴリ（config.py / DISPLAY_CATEGORIES）

| key | label | color | ソースカテゴリ |
|-----|-------|-------|----------------|
| tech | テック・AI | #6366f1 | tech |
| fashion | ファッション・デザイン | #ec4899 | fashion |
| news-business | ニュース・ビジネス | #0ea5e9 | business, general |

---

## SNSタブ（config.py / SNS_CATEGORIES）

xAI Grok API (`POST https://api.x.ai/v1/responses`) + `x_search` ビルトインツールで取得。
モデル: `grok-4-1-fast-reasoning`

| key | label | badge | アクセントカラー | 言語 |
|-----|-------|-------|------------------|------|
| jp_trending | 日本で話題 | JP | #ef4444 | 日本語 |
| global_trending | 海外で話題 | GLOBAL | #10b981 | 英語 |
| ai_jp | AI (日本語) | AI-JP | #8b5cf6 | 日本語 |
| ai_en | AI (English) | AI-EN | #8b5cf6 | 英語 |
| blockchain | ブロックチェーン | CHAIN | #f59e0b | 日英混合 |

各カテゴリで個別にAPIを呼ぶ（5回/実行）。
各カテゴリ 8〜10件取得。
リトライ: `SNS_API_RETRY_TOTAL = 2`、タイムアウト: 120秒。

### SNSポスト形式（JSON）
```json
{"author": "表示名 (@ユーザー名)", "content": "要約（100字以内）", "url": "ポストURL"}
```

URLなしのポストは `sns-no-link` クラスでグレーアウト表示。

---

## 環境変数

| 変数名 | 用途 |
|--------|------|
| XAI_API_KEY | xAI Grok API認証（GitHub Secretsに設定済み） |

---

## GitHub Actions（update-news.yml）

```
スケジュール: 毎日 21:00 UTC（JST 6:00） / 09:00 UTC（JST 18:00）
実行内容:
  1. checkout
  2. Python 3.12 セットアップ
  3. pip install -r scripts/requirements.txt
  4. python scripts/fetch_news.py（XAI_API_KEY注入）
  5. docs/ に変更があればコミット&プッシュ
```

concurrency: `update-news-dashboard`（同時実行キャンセル）

---

## テンプレート（templates/）

### index.html.j2
- `{% include "partials/index.css" %}` でCSS埋め込み
- `{% include "partials/index.js" %}` でJS埋め込み
- Jinja2変数:
  - `display_categories` - ニュースタブのカテゴリ一覧
  - `overall_total` - 全記事総数
  - `all_sites` - サイドバー用サイト一覧
  - `ranking_data` - ランキングデータ
  - `ranking_status` - ランキング取得状況（total/success/failed/updated_at）
  - `sns_data` - SNSカテゴリ一覧（posts含む）
  - `updated_at` - 更新日時（JST）

### index.css（主要スタイル）
- CSS Variables: `--bg-base: #f5f3f0`（ライトベージュ系）
- Glass morphism: `backdrop-filter: blur(20px)` + 白半透明背景
- Ambient blob: `body::before` / `body::after` / `.ambient-blob`（3つのぼかし円）
- サイドバー幅: `--sidebar-width: 260px`（デスクトップ固定）
- ブレークポイント: `768px`（モバイル）
- グリッド: `repeat(auto-fill, minmax(340px, 1fr))`

### index.js（主要機能）
- タブ切り替え（news / ranking / sns）
- カテゴリフィルター（Today's Newsタブのみ）
- モバイルスワイプ（scroll-snap + スワイプ検知）
- タブインジケータードット（スワイプ進捗でアニメーション）
- モバイルソースドロワー（ハンバーガーメニュー）
- localStorage状態保存（`newsflow-ui-state-v1`）
- スワイプヒント（初回のみ表示、`newsflow-swipe-hint-seen-v1`）
- タブ切り替え時に `window.scrollTo({ top: 0 })` でページトップへ戻す（タブごとのコンテンツ長の差でスクロール位置が残る問題の対策）
- `.swipe-container` に `align-items: flex-start`（モバイルのみ）。デフォルトの stretch では全スライドが最長スライド高さに引き伸ばされ、短いタブでも余分なスクロール領域が生じるため
- モバイルスワイプは「スクロール中はインジケータ更新のみ」。タブ確定・高さ同期はスクロール停止後（約120ms）に実行し、最寄りスライドへ `left` を明示補正する（iPhone Safariの慣性で止まり位置がぶれる問題の対策）

### モバイルSNSタブの空白スクロール防止仕様（2026-02-26）
- 対象: `@media (max-width: 768px)` の `.swipe-container`
- 必須指定: `align-items: flex-start`
- 理由: `display:flex` のデフォルト（`stretch`）だと、短いタブでも最長タブ高に引き伸ばされるため
- 症状: SNSタブで下方向に不要な空白領域までスクロールできる
- 運用メモ: 生成元 `templates/partials/index.css` と生成物 `docs/index.html` の両方でこの指定が欠けないこと

### モバイル横スワイプ停止安定化仕様（2026-02-27）
- 対象: iPhone Safari を含むモバイル環境の `.swipe-container`
- 挙動:
  - `scroll` イベント中はタブUIを確定しない（途中でカテゴリUIを切り替えない）
  - 最終スクロール入力から約120ms後に最寄りタブを確定
  - `scrollLeft` がタブ先頭から1px超ズレていれば `behavior: auto` で補正
  - 高さ同期（`swipe-container.style.height`）はこの確定タイミングで実行
- 禁止事項:
  - スクロール中に連続で高さ同期を走らせること
  - スワイプ中の確定処理で `window.scrollTo({ top: 0 })` を発火すること

---

## デザイン
- ライトテーマ（ベージュ系背景 `#f5f3f0`）
- フォント: Inter + Noto Sans JP
- カードスタイル: glass-morphism
- 左アクセントストライプ（各カードのサイト/カテゴリカラー）
- ランキング番号: 1位=金 / 2位=銀 / 3位=銅 / 4位以降=グレー
- ロゴ: News**Flow**（Flowが`--accent-tech: #6366f1`）
