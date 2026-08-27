# news-dashboard

Python (feedparser + BeautifulSoup + Jinja2) で静的HTMLを生成し、GitHub Pagesで配信するニュースダッシュボード。

アーキテクチャ・ファイル構成・タブ構成・ニュースソース一覧は `CURRENT_STATE.md` を参照（正本）。

## CRITICAL

- **GitHub Actions（`update-news.yml`）が本番稼働中**。JST 6:00 / 18:00 に自動実行し `docs/` へ push している。
- このリポジトリ名・`scripts/fetch_news.py`・`docs/` 配下のパスを rename / move しない。cron ワークフローが壊れる。
- ローカル開発は休眠中。**自動化（GitHub Actions）が本体**であり、手元で動かす前提の変更は要注意。

## 開発フロー（Claude 監督 × Codex 実装）

- 出荷プロセスの正本は `plans/00-delivery-process.md`（v2・1 往復）。指示書（`plans/YYYY-MM-DD-*.md`）はこれを前提に書く。
- Codex は指示書 §0 の開始チェックと `00-delivery-process.md` §4 の停止条件に当たったら **merge せず報告して止まる**。
- `docs/**` は GitHub Actions だけが書く。人も Codex も編集しない。
