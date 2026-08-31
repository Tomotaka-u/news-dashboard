# 日本教育新聞を Bookmarks に追加 — 出荷指示書

作成: 2026-08-31（Sol 監督 × Codex 実装）。`plans/00-delivery-process.md` v2 を前提とする。

## §0 開始チェック

- 開始点は `origin/main` の `675bfc1`。隔離 worktree の branch は `codex/add-kyoiku-press-bookmark`。
- 変更前の隔離 worktree は clean、stash は 0 件。
- 元の `main` worktree に残る `AGENTS.md` と `plans/00-delivery-process.md`、`plans/2026-08-27-sns-recovery-research-brief.md` は PR #7 head `a62a6ca` / squash `543e579` に同一 blob で保存・merge 済み。元 worktree は出荷完了まで変更しない。
- 元 worktree の `scripts/config.py` は古い main を基点に bookmark 7 行だけを含む。ファイル全体を移さず、最新 `origin/main` に7行だけ再適用する。
- 変更ファイル whitelist は `scripts/config.py` と本指示書のみ。最初の commit にこの2ファイルだけを含める。
- baseline は `python -m pytest scripts/tests -q` の 57 passed を期待する。件数が異なる場合は停止する。
- §3-A は該当なし。固定 bookmark URL は §3-A-2 の「動的文字列」ではなく、`BOOKMARKS` は自動取得なしなので §3-A-4 の外部自動リクエストも不変。workflow、秘密、ログも変えない。

## §1 目的

Bookmarks タブへ日本教育新聞（`https://www.kyoiku-press.com/`）を1件追加し、次の本番生成で公開する。

## §2 設計判断

- D0: サイレントフォールバックを追加せず、既存の取得・品質ゲート・SNS停止契約を変えない。
- D1: `教育新聞` の直後へ `日本教育新聞` を追加し、近い媒体を並べる。
- D2: 既存カードと同じ5キーを使う。`icon` は `日`、gradient は `#b91c1c` → `#ef4444`、accent は `#b91c1c` とする。
- D3: `SNS_FETCH_ENABLED = False` を含む最新 main の設定を保持する。

## §3 制約・禁止事項

- `.github/**`、`docs/**`、既存テンプレート、ニュース取得ロジックを編集しない。
- 出荷完了と upstream の blob / bookmark 一致を確認するまでは、元 worktree の dirty 4ファイルを上書き・削除しない。
- `git add -A`、`--no-verify`、force push を使わない。
- merge / dispatch は JST 5:30〜6:30、17:30〜18:30 を避け、直前に進行中 run がないことを確認する。

## §4 検証

1. Python 3.12 で `python -m pytest scripts/tests -q` → 57 passed。
2. `python -m compileall -q scripts` → 無出力、`git diff --check` → 無出力。
3. `BOOKMARKS` を import し、対象 URL と name が各1件、全 URL が一意、総数が 13 であることを assert する。
4. Jinja2 で `templates/index.html.j2` をレンダリングし、対象 URL の `href` と表示名が生成 HTML に各1件だけ含まれることを assert する。
5. diff が whitelist 2ファイルだけで、`SNS_FETCH_ENABLED = False` が1件だけ残り、`.github/**` / `docs/**` に差分がないことを確認する。
6. commit 後の head SHA を Sol/high が独立レビューし、P0/P1 ゼロと reviewed SHA の一致を確認する。

## §5 出荷手順

1. 明示した2ファイルだけを stage・commit・push する。
2. PR を作成し、`gh pr checks <n> --watch` が全 pass であることを確認する。
3. `update-news.yml` 直近3 run が success、進行中 run なし、禁止時間帯外、Sol reviewed SHA = PR head SHA を確認する。
4. squash merge し、`workflow_dispatch` を1回だけ実行する。
5. run success 後に生成 commitを取得し、変更が `docs/index.html` と `docs/status.json` だけ、bookmark URL / 表示名が index に各1件、`status.json` gate が passed、run log の固定文字列 `[SNS SKIP] Automated xAI SNS fetching is disabled.` が1件であることを確認する。
6. 元 worktree の対象4ファイルを `/private/tmp` へ個別バックアップして hash を記録する。3つの既存 blob と bookmark block が upstream に保存済みであることを確認した後、対象4パスだけを明示した一時 stash、fetch、`git merge --ff-only origin/main` の順で同期する。最終ファイルとの一致を確認してから既知 stash を drop する。`git reset`、`git clean`、ワイルドカード削除は使わない。

## §6 返却形式・Obsidian

- `plans/00-delivery-process.md` §5 の証拠バンドルに準じて、開始状態、変更、検証、Sol reviewed SHA、PR / merge / dispatch、生成物、最終 Git 状態、未確認事項を報告する。
- Obsidian は `/Users/uchida/Obsidian/TomoVault/40_Sessions/2026-08/2026-08-29/2026-08-29-news-dashboard-SNS復旧-残作業の引き継ぎ.md` に `## S1 | 2026-08-31 | bookmark出荷とGit整理` を append-only で追記する。

## §7 運用調査・見送り

- xAI 403 の復旧、`DEFAULT_XAI_MODEL`、SNS CTA、抽出器、ニュースソースは変更しない。
- PR #7 の merged branch は再mergeしない。head `a62a6ca` と merge `543e579` の一致を証拠に、必要なら clean な旧 worktreeだけを整理する。

## §8 参考

- Bookmarks 定義: `scripts/config.py` の `BOOKMARKS`
- 表示: `templates/index.html.j2` の Bookmarks tab
- 既存出荷プロセス: `plans/00-delivery-process.md`
