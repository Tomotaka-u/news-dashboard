# SNSタブ Grok Automations導線・xAI取得一時停止 — Claude Code引き継ぎ

作成: 2026-08-27（Codex Sol/high監督）

状態: **ローカル実装・検証済み / 未commit・未push・未PR・未merge・未dispatch**

## 1. ユーザー決定

- SNSタブの主表示を、一時的に `https://grok.com/automations` への明確なCTAへ置き換える。
- ユーザーはGrok側でAutomationsを設定済み。ニュースダッシュボードを毎日の入口として使う。
- 403を出し続けている自動xAI API取得は停止してよい（2026-08-27にユーザーが明示GO）。
- 将来xAI API方式へ戻せるよう、既存取得ロジック・5カテゴリ・`sns_data` render契約は削除しない。
- `.github/**`、`docs/**`、secret値、環境変数ファイルには触れない。

## 2. 実装判断

### 表示

- `#tab-sns` は静的なGrok Automations CTAを表示する。
- リンクは `target="_blank"` / `rel="noopener"`。
- 旧SNSカードは `templates/index.html.j2` 冒頭の `legacy_sns_cards(sns_data)` macroへ移し、未呼び出しで保全する。
- 復帰時はCTA sectionを `{{ legacy_sns_cards(sns_data) }}` に差し替える。

### xAI取得停止

- `scripts/config.py` の `SNS_FETCH_ENABLED = False` が停止の正本。
- `False` のとき `run()` は `fetch_all_sns()` を呼ばず、固定ログを1行出して `build_empty_sns_data()` を使用する。
- `build_empty_sns_data()` は全 `SNS_CATEGORIES` の `key` / `label` / `badge` / `accent_color` / `icon_gradient` を維持し、`posts=[]` を渡す。
- `fetch_sns_posts()`、`fetch_all_sns()`、`XAI_API_KEY` / `XAI_MODEL` の既存経路は変更していない。`SNS_FETCH_ENABLED = True` で**有料取得だけ**が再開する。SNSタブはCTAのままで取得結果を表示しないため、表示復帰にはmacroの再挿入が別途必要。
- 再開前に、退役済みの可能性がある `DEFAULT_XAI_MODEL`、APIキー状態、Billing、`x_search` 権限を確認する。

## 3. 変更ファイル

Codex実装:

- `templates/index.html.j2`
- `templates/partials/index.css`
- `scripts/tests/test_sns_cta_template.py`（新規）
- `scripts/config.py`
- `scripts/fetch_news.py`
- `scripts/tests/test_gate.py`
- `CURRENT_STATE.md`
- 本引き継ぎファイル

ユーザー/Claude所有として既に存在し、Codexが戻していないもの:

- `M AGENTS.md`
- `?? plans/00-delivery-process.md`
- `?? plans/2026-08-27-sns-recovery-research-brief.md`

## 4. 検証証拠

- 変更前baseline: `53 passed`
- CTAテスト先行: HEAD相当テンプレートで `2 failed`
- xAI停止テスト先行: `1 failed, 5 passed`（`SNS_FETCH_ENABLED` 未実装を検出）
- 実装後: `57 passed`
- `python -m compileall -q scripts`: 成功
- `git diff --check`: 成功
- CTAブラウザ確認:
  - デスクトップ正常
  - 390px幅で横あふれなし
  - SNSタブのARIA関連付け維持
  - CTAのhref / target / relを確認
  - fixtureの動的SNS投稿が公開本文へ出ない
- CTA独立レビュー: Sol/high、最終P0/P1/P2ゼロ。
- xAI停止独立レビュー: Sol/high。初回P0/P1ゼロ・P2 2件（直接POST/秘密未読テスト、二段階復旧の明記不足）を修正し、再レビューでP0/P1/P2ゼロ。

## 5. 出荷プロセス上の扱い

- xAI取得停止は外部リクエスト回数を、403継続時の最大10 POST試行/実行（5カテゴリ × 最大2試行）から0へ変えるため、`plans/00-delivery-process.md` §3-A-4。
- ユーザーは2026-08-27に明示GO済み。ただしリポジトリの正式な§0出荷指示書、commit / pushの明示指示、PR/checks/merge/dispatch検証はまだない。
- よってCodexはローカル実装で停止し、commit / push / PR / merge / dispatchを行っていない。

## 6. Claude Codeの次アクション

1. 本ファイル、`AGENTS.md`、`CURRENT_STATE.md`、`plans/00-delivery-process.md`、全diffを読む。
2. `git status --short` で上記dirty/untrackedと一致するか確認する。差異があれば停止。
3. Sol/high独立レビュー最終結果とObsidian S4を確認する。
4. 出荷する場合は、§8形式の正式指示書へ以下を明記する:
   - §3-A-4該当、ユーザーGO済み
   - 最初のcommitに含めるファイルのwhitelist
   - baseline / afterテスト件数
   - `docs/**` / `.github/**` 無変更
   - merge / dispatch禁止時間帯と直近Actions確認
5. ユーザーのcommit / push指示を得てから、PR → checks → 独立レビュー対象SHA固定 → merge → dispatch → 本番CTA・Actionsログの `[SNS ERROR]` 0件と固定 `[SNS SKIP]` 1件を確認する。
6. 次の定期cronでもCTA表示とxAIリクエスト停止が継続することを確認する。

## 7. 未確認

- 本番GitHub ActionsでのゼロxAI通信（dispatch未実施）。
- 本番生成物 `docs/index.html` のCTA（`docs/**` は未編集）。
- Grok Automations側のログイン後画面・ユーザー設定内容。
- xAI再開時に使う現行モデルIDと権限・課金状態。
