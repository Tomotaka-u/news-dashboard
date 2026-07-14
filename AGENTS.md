# news-dashboard

Python (feedparser + BeautifulSoup + Jinja2) で静的HTMLを生成し、GitHub Pagesで配信するニュースダッシュボード。

アーキテクチャ・ファイル構成・タブ構成・ニュースソース一覧は `CURRENT_STATE.md` を参照（正本）。

## CRITICAL

- **GitHub Actions（`update-news.yml`）が本番稼働中**。JST 6:00 / 18:00 に自動実行し `docs/` へ push している。
- このリポジトリ名・`scripts/fetch_news.py`・`docs/` 配下のパスを rename / move しない。cron ワークフローが壊れる。
- ローカル開発は休眠中。**自動化（GitHub Actions）が本体**であり、手元で動かす前提の変更は要注意。
