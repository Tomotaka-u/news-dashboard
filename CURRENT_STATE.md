# news-dashboard 現状まとめ

最終確認日: 2026-08-24

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
│   ├── requirements.txt
│   ├── requirements-dev.txt
│   └── tests/              # ネットワーク不要の pytest・抽出フィクスチャ
├── templates/
│   ├── index.html.j2       # メインテンプレート
│   └── partials/
│       ├── index.css       # スタイル
│       └── index.js        # クライアントサイドJS
├── docs/                   # GitHub Pages 公開ディレクトリ（生成物）
│   ├── index.html
│   └── status.json         # 最後に品質ゲートを通過した実行の取得状況
└── .github/
    ├── dependabot.yml      # pip / github-actions の週次更新 PR
    └── workflows/
        ├── update-news.yml # 自動更新ワークフロー（本番 cron）
        └── ci.yml          # pytest（docs/ 以外の push・PR）
```

---

## タブ構成（4タブ）

| タブ名 | 内容 |
|--------|------|
| Today's News | RSSフィード・スクレイピングによる最新記事 |
| Rankings | 各サイトの人気記事ランキング |
| SNS | xAI Grok API経由のXトレンドポスト |
| Bookmarks | `config.py` / `BOOKMARKS` の静的リンク一覧（自動取得なし、手動巡回用） |

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
| CryptoSlate | RSS | CRYPTO | #1e40af |
| Hacker News | RSS | TECH | #f97316 |
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

### 設定値
- `MAX_ITEMS_PER_SITE = 8`（RSSフィード・スクレイピングの最大件数）
- `MAX_RANKING_ITEMS = 5`（ランキングの最大件数）
- `MIN_TOTAL_ITEMS = 20`（記事総数が未満なら `docs/` を更新しない品質ゲート）
- `DEFAULT_XAI_MODEL = "grok-4-1-fast-reasoning"`（`XAI_MODEL` 未設定時）

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
| 日経新聞 | nikkei |
| BBC News | bbc |
| PR TIMES | prtimes |
| Yahoo!ニュース | yahoo_news |

汎用フォールバックは使用しない。専用パーサーが0件なら `empty` として失敗表示・記録する。未知の `ranking_type` は `parse_error`。

- TechCrunch はトップページのサーバHTMLに含まれる「Most Popular」モジュールを、そのクラス境界内だけスクレイプする。
- GIZMODO JAPAN はトップページ「Ranking」で active な Daily タブと同じ index のパネルを選び、順位 1〜5 と記事リンクが対応する場合だけ取得する。
- FASHIONSNAP は `/ranking/` の「トップ100」内で初期選択された WEEKLY を起点に、順位 1〜5 と同じ item の記事リンクが対応する場合だけ取得する。
- 日経新聞は `/access/` の最初のアクセスランキングコンテナ `.m-miM32` が「総合」かつ「今日」で、順位 1〜5 と記事リンクが対応する場合だけ取得する。

### 稼働状況（2026-08-24 時点）

本番UAのフル実行で、ランキング10ソースはすべて5件取得できた（`overall_total=136`、feed/scrape は17/17成功）。

| サイト | 結論 |
|--------|------|
| TechCrunch | 「Most Popular」から5件取得。旧「Top Headlines」は使用しない |
| GIZMODO JAPAN | active な Daily タブと同 index のパネルから、順位1〜5に対応する記事を5件取得 |
| FASHIONSNAP | 「トップ100」の初期選択 WEEKLY から、非日付 slug を含む順位1〜5を5件取得 |
| JDN | `/pickup/` は人気順ではないためランキング対象外 |
| WWDJAPAN | 本番UAと Accept ヘッダでも `/ranking` が HTTP 403 のためランキング対象外。feed は取得可能 |
| 日経新聞 | `/access/` の「総合」かつ「今日」のコンテナから、順位1〜5に対応する記事を5件取得 |

### ランキング参照先 調査メモ（2026-02-27・履歴）

| サイト | 現在の `ranking_url` | 現在の抽出基準 | 観測結果（`docs/index.html`） | 判定 |
|--------|----------------------|----------------|-------------------------------|------|
| JDN | 対象外（旧 `https://www.japandesign.ne.jp/pickup/`） | 編集ピックアップであり人気順ではない | 2026-08-21 にランキング設定を削除 | 対象外 |
| GIZMODO JAPAN | `https://www.gizmodo.jp/` | `RANKING` の active Daily タブと同 index のパネル内、順位1〜5の `/article/` | 本番UAで5件確認 | 運用中 |

メモ:
- JDN は過去に「ピックアップ」基準へ変更したが、2026-08-21 に人気ランキングではないと再判定して対象外とした。
- GIZMODO は専用ランキングURLではなく、トップページ `RANKING` モジュールで active な Daily タブに対応するパネルを取得する方針。

#### 参照先 方針確定（2026-02-27）
- JDN: ランキングではなく「ピックアップ」を基準にする
- GIZMODO JAPAN: 「総合ランキング」のデイリー（当日ランキング）を基準にする
- 実装ルール: まず参照先URLと抽出セレクタをこの方針に合わせて見直してから、`ranking_url` / 抽出ロジックを修正する

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
モデル: `XAI_MODEL`、未設定時は `DEFAULT_XAI_MODEL`（現在 `grok-4-1-fast-reasoning`）

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
| XAI_MODEL | xAI モデルの上書き。未設定時は `DEFAULT_XAI_MODEL` |
| NEWS_MIN_TOTAL_ITEMS | テスト・診断用の品質ゲート上書き。実行時に整数として読む |

### `status.json` / 画面の `detail` 方針

URL・パス・クエリ・生の例外文は公開しない。取得例外は `summarize_error()` で要約し、全 `detail` に redaction の安全網を適用する。

---

## GitHub Actions（update-news.yml）

```
スケジュール: 毎日 21:00 UTC（JST 6:00） / 09:00 UTC（JST 18:00）
実行内容:
  1. checkout
  2. Python 3.12 セットアップ
  3. pip install -r scripts/requirements.txt
  4. python scripts/fetch_news.py（XAI_API_KEY注入）
  5. docs/ に変更があればコミット&プッシュ（push 失敗時は origin/main に rebase して最大3回リトライ。競合は exit 1 で失敗させる）
```

`docs/index.html` と `docs/status.json` は同じディレクトリの tmp へ書いてから `os.replace` で置換する。残存する `docs/*.tmp` は Git の対象外。

concurrency: `update-news-dashboard`（同時実行キャンセル）
actions: `actions/checkout@v7` / `actions/setup-python@v7`（Node 24 ランタイム。v4/v5 は Node 20 deprecation 警告が出る）

### CI（ci.yml）

`docs/` 以外への push（main）と pull_request で `scripts/tests` の pytest を Python 3.12 で実行（compileall も実行）。本番 cron と同じ Python で、ネットワーク不要のテストだけを回す。cron の `docs/` のみの commit では起動しない。

### Dependabot（.github/dependabot.yml）

毎週月曜（JST）に pip（`/scripts` の requirements）と github-actions を確認。pip は minor/patch を 1 PR にグループ化。マージ前に CI が通ることを確認する。

品質ゲート失敗時は SNS API と `docs/` 書き込みより前に終了コード1で止まり、前回の正常版を保持する。公開 `status.json` は「最新試行」ではなく「最後にゲートを通過した成功実行」の状態を表すため、ゲート失敗自体は GitHub Actions の失敗履歴で確認する。

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
  - `ranking_status` - ランキング取得状況（total/success/failed/failed_names/updated_at）
  - `source_status` - `status.json` の `sources` と同一のソース別取得結果
  - `feed_status_by_name` - feed/scrape の取得結果をサイト名で引く辞書
  - `sns_data` - SNSカテゴリ一覧（posts含む）
  - `bookmarks` - Bookmarksタブ用の静的サイト一覧（`config.py` / `BOOKMARKS`）
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
- モバイルスワイプは「スクロール中はインジケータ更新のみ」。タブ確定・高さ同期はスクロール停止後（約160ms）に実行し、最寄りスライドへ `left` を明示補正する（iPhone Safariの慣性で止まり位置がぶれる問題の対策）
- iPhone向けに「1スワイプで最大1タブ移動」を適用（news→sns の2枚飛びを禁止し、ranking に止まりやすくする）

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
  - 最終スクロール入力から約160ms後に最寄りタブを確定
  - `scrollLeft` がタブ先頭から1px超ズレていれば `behavior: auto` で補正
  - 補正時の候補タブは「スワイプ開始タブの前後1つまで」に制限（1ジェスチャーで2枚飛びしない）
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
