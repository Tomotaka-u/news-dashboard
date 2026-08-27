# SNSタブ Grok Automations導線・xAI取得停止 — 出荷指示書

作成: 2026-08-27

実装baseline: `0098d0865e383e526e1744fbf656814ab96639a6`

PR branch base: `5ed5a9f`（2026-08-27 cron生成commit。`0098d08..5ed5a9f` は `docs/index.html` / `docs/status.json` のみ）

## §0 開始チェック

期待する開始状態:

- 開始時のdetached HEAD: `0098d0865e383e526e1744fbf656814ab96639a6`
- fetch後の `origin/main`: `5ed5a9f`。差分は `docs/index.html` / `docs/status.json` のみ。
- `git stash list`: 空
- baselineテスト: 53件
- 許可するdirty / untrackedと、最初のfeature commitへ含めるwhitelist:
  1. `AGENTS.md`
  2. `CURRENT_STATE.md`
  3. `plans/00-delivery-process.md`
  4. `plans/2026-08-27-sns-recovery-research-brief.md`
  5. `plans/2026-08-27-sns-grok-automations-handoff.md`
  6. `plans/2026-08-27-sns-grok-automations-ship.md`
  7. `scripts/config.py`
  8. `scripts/fetch_news.py`
  9. `scripts/tests/test_gate.py`
  10. `scripts/tests/test_sns_cta_template.py`
  11. `templates/index.html.j2`
  12. `templates/partials/index.css`
- `.github/**` / `docs/**` / env・secretファイルは変更0件であること。
- branchは `codex/sns-grok-automations` を最新 `origin/main@5ed5a9f` から作り、whitelistのworking-tree変更を引き継ぐ。

### §3-A判定

**事前GO必須。v1経路でPR作成後に停止する。**

- §3-A-4: 403継続時の最大10 POST試行/実行（5カテゴリ × 最大2試行）を0へ変更する。
- §3-A-3: `SNS_FETCH_ENABLED=False` の間、`XAI_API_KEY` / `XAI_MODEL` を読むタイミングを無くす。
- ユーザーはローカル実装とPR準備へGO済み。merge GOはPR head SHAの同一SHAレビュー後に別途受ける。

## §1 目的

- SNSタブを `https://grok.com/automations` への日次CTAへ一時置換する。
- 失敗中のxAI自動取得を停止し、不要な外部通信・403ログを止める。
- 既存の5カテゴリ、取得関数、`sns_data` render契約、旧カード表示を将来復帰できる形で保全する。

## §2 設計判断

- D0: サイレントフォールバック、statusの `ok` 増加、公開status schema変更、動的外部文字列の新規ログ出力を行わない。
- D1: `SNS_FETCH_ENABLED=False` を停止の正本とし、無効時は固定 `[SNS SKIP] Automated xAI SNS fetching is disabled.` を1行だけ出す。
- D2: 無効時の `sns_data` は全 `SNS_CATEGORIES` の表示属性と `posts=[]` を保持する。
- D3: `SNS_FETCH_ENABLED=True` は有料取得だけを再開する。表示はCTAのまま。旧表示の復帰は `legacy_sns_cards(sns_data)` macroの再挿入を別変更として行う。
- D4: 旧 `fetch_sns_posts()` / `fetch_all_sns()`、category prompts、secret名、endpoint、workflowは変更しない。

## §3 制約・禁止事項

- whitelist外のファイルを変更・stage・commitしない。
- `.github/**` / `docs/**` / secret値 / 環境変数ファイルを読まない・変更しない。
- `git add -A`、`--no-verify`、force pushを使わない。
- Dependabot PRに触れない。
- merge / dispatch禁止時間帯（JST 5:30〜6:30、17:30〜18:30）を守る。
- PR head SHAに対する事前GO前にmergeしない。

## §4 検証

実装・PR前:

1. `/private/tmp/news-dashboard-pytest-20260827/bin/python -m pytest scripts/tests -q` → 57 passed。
2. `/private/tmp/news-dashboard-pytest-20260827/bin/python -m compileall -q scripts` → exit 0。
3. `git diff --check` → exit 0。
4. `git diff --name-only -- .github docs` → 出力なし。
5. CTA: desktop / 390px、ARIA、横overflowなし、href / target / rel、動的SNS fixture非表示。
6. 無効経路: 偽キーありでもPOST 0、`XAI_API_KEY` / `XAI_MODEL` 読取り0、5カテゴリ空契約。
7. 有効経路: 実legacy関数で5カテゴリ・5 POST・endpoint 1種。

PR作成後:

8. `gh pr checks <PR> --watch` が全pass。
9. Sol/high独立レビューをPR head SHAに固定し、P0/P1ゼロを確認する。
10. `gh run list --workflow=update-news.yml --limit 3` のfailure / in-progress有無を記録する。
11. §4停止条件10項目をYes/Noで返す。

## §5 出荷手順

1. 最新 `origin/main@5ed5a9f` から `codex/sns-grok-automations` branchを作る。
2. whitelist 12ファイルだけを明示stageし、feature commitを作る。
3. branchをpushし、PRを作成する。
4. checksと同一head SHAレビューを完了する。
5. **§3-AのためPRでGO待ち停止。merge / dispatchしない。**
6. 次の明示GO後、禁止時間帯外かつupdate-news workflow非稼働を確認し、squash merge → workflow dispatch 1回 → 本番生成物検証を行う。
7. 本番ログは完全一致の `[SNS SKIP] Automated xAI SNS fetching is disabled.` が1件、`[SNS ERROR]` が0件であることを確認する。旧「キー未設定」の `[SNS SKIP]` と混同しない。

## §6 返却形式

`plans/00-delivery-process.md` §5の証拠バンドルに従う。最低限、開始状態、変更ファイル、テスト、レビュー対象SHA、PR/checks、停止条件10項目、未確認、監督構成、Obsidian追記先を含める。

Obsidian追記先:

`/Users/uchida/Obsidian/TomoVault/40_Sessions/2026-08/2026-08-27/2026-08-27-news-dashboard-SNS復旧.md`

## §7 運用調査・follow-up（今回直さない）

- `test_status_json.py` と既存gateテストの `fetch_all_sns` monkeypatchがフラグFalseで空振りになる箇所を整理する。
- 秘密未読テストは現状 `os.environ.get` を固定する。将来 `os.getenv` 等へ変更する場合は検査も更新する。
- macro定義後の改行によりDOCTYPE前へ空行が1行出るがHTML仕様上無害。必要なら別の表示ノイズ整理で扱う。
- xAI再開は取得と表示の二段階。取得だけ再開して課金する事故を避けるrunbookを別途用意する。

## §8 参考

- 現行状態: `CURRENT_STATE.md`
- 実装判断・検証・未確認: `plans/2026-08-27-sns-grok-automations-handoff.md`
- 調査証拠: `plans/2026-08-27-sns-recovery-research-brief.md`
- 出荷プロセス: `plans/00-delivery-process.md`
