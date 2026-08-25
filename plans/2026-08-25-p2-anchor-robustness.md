# P2 指示書: ランキング抽出器のアンカー堅牢化（Codex 向け）

作成: 2026-08-25（Claude Fable 監督セッション。P1 Step 2 の Opus 敵対的レビュー follow-up と S6 backlog を指示書化）
対象リポジトリ: `~/projects/news-dashboard`（開始時点 main = `df4ec46`。cron の生成物 commit が積まれていてよい）
レーン: 実装フェーズ **M**（3 抽出器のアンカー変更とテスト拡充。`status.json` の形・workflow・成功条件の厳格さは変えない）。出荷フェーズ（§6）は **L**（本番 workflow への merge・dispatch）
背景: Obsidian `40_Sessions/2026-08/2026-08-25/2026-08-25-news-dashboard-P2アンカー堅牢化.md`（topic_id `news-dashboard-p2`）。前段: P1 Step 2 `ac09f5e`（`plans/2026-08-22-p1-detection-hygiene.md`）、その出荷 `plans/2026-08-24-p1-step2-ship.md`（未 commit。本指示書と一緒に最初の commit に同梱する）

---

## 0. 前提条件と開始前チェック

### 0-a. P1 Step 2 と同じ点・違う点（最初に読む）
- 手順は P1 Step 2 と同じ「実装 → テスト → push → PR → CI green → **停止して §5 の形式で報告**」。監督が pytest を自走し diff を読んだ後に **reviewed head SHA を明記した GO** を出す。**GO が来るまで merge・dispatch はしない**（CI green は GO ではない）
- 違う点: GO が出た後の出荷（§6）も本指示書に含める。別の出荷指示書は作らない
- P1 Step 2 で「取れていると言っているものが本当にランキングか」を構造で保証した。P2 はその成功条件を**緩めずに**、依存しているアンカーのうち「サイトの再デプロイで勝手に変わるもの」（CSS-in-JS のハッシュ class、部分一致の class 名、先頭要素の仮定）を「サイトが意図して出しているもの」（data-testid・見出し文言・順位番号・href・HTML 標準属性）に置き換える。**`ok` を増やすことが目的ではない**。ライブの結果は before/after で同一でなければならない

### 0-b. Codex が最初に行うチェック
1. `git switch main && git pull --rebase && git status --short` → untracked が `plans/2026-08-24-p1-step2-ship.md` と本指示書 `plans/2026-08-25-p2-anchor-robustness.md` の 2 本だけであること。それ以外がダーティなら止まって報告
2. 作業ブランチ: `git switch -c feat/p2-anchor-robustness`。最初の commit は指示書 2 本だけ: `git add plans/2026-08-24-p1-step2-ship.md plans/2026-08-25-p2-anchor-robustness.md && git commit -m "docs: P1 Step2 出荷指示書と P2 指示書を追加"`
3. `python --version` が 3.12 系（CI と同じ）。`pip install -r scripts/requirements-dev.txt`（pytest は #3 で **9.1.1** に上がっている）
4. `python -m pytest scripts/tests -q` → **27 passed** を baseline として記録
5. ライブサイト（gizmodo.jp トップ / fashionsnap.com/ranking/ / nikkei.com/access/）に本番 UA `NewsDashboard/1.0 (+https://github.com/Tomotaka-u/news-dashboard)` で取得できること。**できない環境なら D1〜D4 のライブ確認は推測で書かず `[検証不能]` として報告**する（fixture テストだけで実装は進めてよい。§4 の before/after は監督が代行する）
6. 着手前に現行コードで 3 サイトのライブ結果を保存する（§4 の before）: `python -c` で `build_http_session()` → 各 URL 取得 → `extract_*_ranking(soup, url)` を呼び、title / link 5 件を JSON でファイルに残す

## 1. 目的（何を達成するか）

| # | 問題 | 場所（`df4ec46` 時点の `scripts/fetch_news.py`） |
|---|---|---|
| 1 | FASHIONSNAP が vanilla-extract のハッシュ class `s3r3r52` / `si7p730` / `si7p732` / `_7rl1co1` に依存。サイトの再デプロイで class 名が回ると `empty` に倒れる。`_7rl1co1` の本数で 2 分岐している | L326, L339-340, L346, L357, L365 |
| 2 | GIZMODO の active 判定が `"active" in class_name` の部分一致。`inactive` にも一致する | L225 |
| 3 | 厳格 3 抽出器が `min_title_length=10`。順位対応が構造保証を担っているので長さ閾値は不要で、短いタイトル 1 本で 5 件全滅する爆風半径だけが残っている | L253, L380, L409 |
| 4 | 日経が `select_one(".m-miM32")` = 先頭コンテナ固定。「総合」「今日」のブロックが 2 番目に来ると `empty` | L390 |
| 5 | GIZMODO の旧 `s-Ranking_Heading` フォールバック（`db888ed1` 2026-02-27 由来の死にコード） | L195-196 |
| 6 | 負例テストが薄い（順位が飛ぶ / Daily 非 active / tabs≠panels / MONTHLY active / 系列数不一致 が未検証） | `scripts/tests/test_extractors.py` |
| 7 | `summarize_error` で `hostname` が None のとき `(None)` と出る | L76 |

**成功の定義**: 上記 1〜7 を直した後も、(a) fixture テストの順位 1〜5 と記事の対応は変わらない（FASHIONSNAP は承認済み D1 改訂により、旧時間パネル fixture からカテゴリ系列 fixture へ契約を置き換える）、(b) ライブ 3 サイトの before/after の title / link 5 件が完全一致、(c) `status.json` のキー・語彙・並びが不変。**成功条件を緩めて `ok` を増やす変更は禁止**。

## 2. 設計判断（確定済み。変えたい場合は理由を添えて報告し、勝手に変えない）

### D0. 共通規則（P1 Step 2 の D0 を継続）
- 実装時に一度だけ判断し、決めた側の条件だけをハードコードする。「新アンカーがあれば新方式、無ければ旧 class」のような実行時分岐・旧方式へのフォールバックは書かない。旧 class 名（`s3r3r52` 以外）はコードから消す
- 順位番号の判定は既存 `_parse_rank_number` を使う。成功条件は「1〜5 がこの順で現れ、各順位に記事リンクが 1 本対応し、5 件そろう」で不変
- テストは **fixture を先に書き、失敗を確認してから実装**する（負例は特に。現行コードで通ってしまう負例は負例になっていない）

### D1. FASHIONSNAP: class 名非依存の走査に書き直す
- **2026-08-25 実装時改訂（ユーザー承認済み）**: ライブ DOM では順位系列が時間 tabs（weekly / monthly）ではなくカテゴリ tabs（all / fashion / beauty / other）と対応していたため、`data-testid="all"` を意味的アンカーへ追加し、カテゴリ系列の対応に修正する。DOM 深度で系列を選ぶ案は wrapper 変更で誤採用し得るため不採用
- 残してよいアンカー: 見出し `トップ100`（h1/h2 の文言）、時間 tabs の `data-testid="weekly"` / `"monthly"`、カテゴリ tabs の `data-testid="all"` / `"fashion"` / `"beauty"` / `"other"`、記事リンク `href^="/article/"`、順位番号、**初期選択の証拠 `s3r3r52`**（これだけは代替が無い。ライブ HTML に `aria-selected` / `aria-current` / `data-state` 等が存在するかを D1 のライブ確認で見て、あれば報告する。**あっても今回は切り替えない**。監督判断）
- 消すアンカー: `si7p730` / `si7p732` / `_7rl1co1` と `block.parent` 経由の wrapper 依存
- 手順:
  1. section の決め方は現行どおり（見出しの親をたどり weekly と monthly を両方含む要素）。ただし第 3 条件 `.si7p730` を「`a[href^="/article/"]` を含む」に置き換える
  2. 時間 tabs は `weekly.parent` 直下の weekly / monthly 2 要素だけを認め、`s3r3r52` が weekly にあり monthly にないことを初期選択の証拠とする
  3. `data-testid="all"` は section 内にちょうど 1 個を要求する。`all.parent` 直下のカテゴリ tabs は all / fashion / beauty / other の重複なし 4 要素だけを認め、文書順の `all_index` を求める。欠落・重複・未知カテゴリは `[]`
  4. section 内の `a[href^="/article/"]` を**文書順**に走査し、`_parse_rank_number(a.get_text())` が None でないものだけを「順位アンカー」とする。値 1 の順位アンカーを各カテゴリ系列の開始とし、生の系列開始数がカテゴリ tabs 数と完全一致する場合だけ `all_index` 番目を選ぶ
  5. 選んだ all 系列の順位アンカーが 1〜5 と連続することを確認する。all 系列が壊れていても別カテゴリ系列へ乗り換えない
  6. 各順位アンカーに対応する「タイトルアンカー」は、全 article link 列で**その順位アンカーの直後**に現れる 1 本だけとする。`href` が順位アンカーと等しく、sanitize 後のテキストが空でなく順位番号でもないことを要求する。タイトル後から次の順位アンカーまでにあるカテゴリリンクは無視する
  7. `append_ranking_item` の `min_title_length` は既定値（D3）
- fixture: ライブ由来のカテゴリ4系列正例、all が2番目の正例、all 破損時の乗り換え禁止、カテゴリ tabs / 系列数不一致、all 欠落・重複、class 総入替を D6 で固定する。旧 `fashionsnap-ranking.html` / `-weekly-second.html` は改訂前 DOM の履歴 fixture として残すが、改訂後の抽出契約テストには使わない

### D2. GIZMODO: active 判定を CSS Modules の基底名でアンカーする
- `"active" in class_name` を、class トークンが `re.fullmatch(r"ranking_active(__\w+)?", token)` に一致するものが tabs[daily_index] にあるか、に変える（基底名 `ranking_active` はソース由来で安定、`__Idnm1` 部分はビルドハッシュ）
- `inert` 属性はライブでは非 active パネルに付いているが、**判定には使わない**（サイトが `inert` をやめた場合に両パネルとも「active」に見えて緩む方向に倒れるため。D0 のとおり fail-closed を選ぶ）。fixture の負例には使ってよい
- 旧 `s-Ranking_Heading` フォールバック（L195-196）を削除（D5）

### D3. `min_title_length=10` を既定値に戻す
- GIZMODO / FASHIONSNAP / 日経の 3 呼び出しから引数 `10` を外す。`append_ranking_item` のシグネチャと他の抽出器（TechCrunch 等）は触らない
- テスト: 3 サイトのいずれかの fixture で 1 件だけタイトルを 3 文字にした負例… は**作らない**（短いタイトルは今後 ok になるのが正しい）。代わりに既存の正例 fixture がそのまま通ることで足りる

### D4. 日経: 探索範囲を「先頭 `.m-miM32`」から「条件を満たす `.m-miM32`」に広げる
- `select_one(".m-miM32")` → `select(".m-miM32")` を順に見て、`.m-miM32_title` が「総合」かつ `.m-miM32_pulldownCurrentText` が「今日」の**最初の**コンテナを採る。該当なしなら `[]`。順位 1〜5 の条件は不変
- fixture: `nikkei-ranking-second-container.html`（先頭に「ビジネス」/「今日」のコンテナ、2 番目に「総合」/「今日」）→ 2 番目から 5 件。`nikkei-ranking-no-match.html`（「総合」/「昨日」のみ）→ `[]`

### D5. 死にコードの削除
- GIZMODO の `s-Ranking_Heading` フォールバックを削除。他は触らない

### D6. 負例テストの拡充（fixture 先行）
| テスト | fixture | 期待 |
|---|---|---|
| GIZMODO 順位が飛ぶ（1,2,4,5,6） | `gizmodo-ranking-rank-gap.html` | `[]` |
| GIZMODO Daily タブが非 active（class に `ranking_inactive__x` のみ。部分一致なら誤って通る） | `gizmodo-ranking-daily-inactive.html` | `[]` |
| GIZMODO tabs 3 / panels 2 | `gizmodo-ranking-tab-panel-mismatch.html` | `[]` |
| FASHIONSNAP MONTHLY が初期選択 | `fashionsnap-ranking-monthly-active.html` | `[]` |
| FASHIONSNAP カテゴリ4 tabs / 4系列、タイトル後にカテゴリリンクがあるライブ由来正例 | `fashionsnap-ranking-categories.html` | all 系列の5件 |
| FASHIONSNAP all がカテゴリ tabs の2番目 | `fashionsnap-ranking-all-second.html` | 2番目の all 系列5件 |
| FASHIONSNAP カテゴリ4 tabs / 系列3本 | `fashionsnap-ranking-series-mismatch.html` | `[]` |
| FASHIONSNAP カテゴリ4 tabs / 系列5本 | `fashionsnap-ranking-series-excess.html` | `[]` |
| FASHIONSNAP all 系列だけ順位が飛ぶ（1,2,4,5,6） | `fashionsnap-ranking-all-rank-gap.html` | `[]`（他系列へ乗り換えない） |
| FASHIONSNAP all 系列の順位アンカー直後リンクが別 href（他3系列は正常） | `fashionsnap-ranking-href-mismatch.html` | `[]`（他系列へ乗り換えない） |
| FASHIONSNAP all 欠落 / 重複 | `fashionsnap-ranking-all-missing.html` / `-all-duplicate.html` | `[]` / `[]` |
| FASHIONSNAP all を含むが未知カテゴリがある | `fashionsnap-ranking-unknown-category.html` | `[]` |
| FASHIONSNAP class 名を全て差し替えたカテゴリ正例（`s3r3r52` 以外を `x-*` に置換） | `fashionsnap-ranking-rehashed-categories.html` | all 系列の5件 |
| 日経 順位が飛ぶ | `nikkei-ranking-rank-gap.html` | `[]` |
| 日経 D4 の 2 本 | 上記 | 5 件 / `[]` |
- 各 fixture は 50KB 以下、トラッキング・PII を含めない。既存 fixture のコピー＋最小改変で作る

### D7. `summarize_error` の hostname None
- `urlparse(url).hostname or "unknown-host"` にする。テスト: `test_detail_sanitization.py` に url が `"not a url"` のケースを 1 本

### D8. 見送り（記録のため。今回は触らない）
- `redact_detail` の `\?\S+` が日本語文中の ASCII `?` に誤爆する件: 公開面の安全側（消しすぎ）に倒れる誤爆なので放置。直すなら URL 文脈に限定する正規表現が必要で、今回の爆風半径に見合わない
- `_replace_all` のディレクトリ fsync なし: GitHub Actions 上では commit 前に step が落ちれば push されないため実害なし。ローカル運用が復活したときに再検討

### D9. ドキュメント（`CURRENT_STATE.md`、Codex に scope grant）
- L111-113 / L122-126 / L133-137 付近の 3 サイトの記述を D1 / D2 / D4 の条件に合わせて更新（FASHIONSNAP「class 名非依存、初期選択の証拠のみ class」、GIZMODO「`ranking_active` 基底名」、日経「『総合』かつ『今日』のコンテナ（先頭固定ではない）」）。稼働状況の日付を更新
- `.github/**` / `docs/**` には触らない

## 3. 制約・禁止事項
- 成功条件を緩めない（順位 1〜5 の連続・href 一致・5 件そろい・初期選択の証拠）
- 実行時フォールバック・try/except で `[]` を握りつぶす書き方を追加しない
- `status.json` のキー・語彙・並び・`total_sources` の導出を変えない
- `.github/**` / `docs/**` を編集しない。`git add -A` / `--no-verify` / force push 禁止
- 他サイトの抽出器（TechCrunch / Verge / ITmedia / HN / BBC / PR TIMES / Yahoo）に触らない
- コードコメントは英語、commit メッセージは日本語 Conventional Commits

## 4. 検証（報告に出力を貼る）
1. `python -m pytest scripts/tests -q` → 27 + 新規本数 passed。`python -m compileall -q scripts`
2. 現行バグを露出する新規テストは **fixture 追加直後・実装前に失敗すること** を 1 度確認し、その出力（`FAILED` 行）を貼る。既存実装がすでに fail-closed の負例は PASS でよく、どの負例が既存で守られていたかを分けて報告する
3. ライブ before/after: 0-b-6 で保存した before と、実装後の同手順の after を 3 サイト分並べる。**title / link が 5 件とも一致**。不一致があれば止まって報告（サイト側の更新で順位が入れ替わった場合は、取得時刻を添えて再取得 1 回まで）
4. D1 のライブ確認: FASHIONSNAP `/ranking/` の weekly タブ要素に `aria-*` / `data-state` 等の初期選択を示す標準属性があるか（あれば属性名と値を報告。切り替えはしない）
5. `git diff --stat main` に `.github/` / `docs/` が無いこと。fixture の最大サイズ

## 5. 返却形式（監督が一次証拠で verify するため）

```
## 変更ファイル
## 判断の変更・追加（D0 の手続きを踏んだもの）
## D1 ライブ確認メモ（初期選択を示す標準属性の有無、系列数、tabs 数）
## ランキング before/after（3 サイト × 5 件、取得時刻つき）
## テスト・検証出力（baseline 27 → after N、負例の実装前 FAILED、compileall）
## PR URL / head SHA / CI run ID / 結論
## 未解決・気づいた事項（修正はしない）
## 運用調査（§7、read-only）
## 監督構成（レーン / 委譲 / 昇格 / 未確認）
```

ここで**停止**する。Obsidian: `40_Sessions/2026-08/2026-08-25/2026-08-25-news-dashboard-P2アンカー堅牢化.md` の末尾に `## S2 | 日付 | 一言` で追記（新規ノートは作らない）。

## 6. 出荷（監督の GO 後のみ。GO メッセージには reviewed head SHA が書かれている）
1. `gh pr view <n> --json headRefOid` が **GO に書かれた SHA と一致**することを確認。違えば止まって報告
2. `gh run list --workflow=update-news.yml --limit 3` が全て success
3. `gh pr merge <n> --squash --delete-branch` → merge SHA → main push CI（`ci.yml`）success を `gh run watch`
4. `gh workflow run update-news.yml` を 1 回 → run ID / 結論 / update job 所要時間 / `[FEED FAIL]` `[RANKING FAIL]` `Node.js 20` `deprecated` の件数と本文
5. `git pull --rebase` → `docs/status.json` の `generated_at` / `gate` / `feeds` / `rankings` / 非 ok 行の name・kind・status・detail 全部。GIZMODO / FASHIONSNAP / 日経が `empty` なら**パーサを直さず**、どのアンカーが無かったかをログの証拠だけで報告
6. `detail` に URL・パス・`?` クエリ・`Max retries exceeded with url:` が無いこと
7. open な Dependabot PR があれば P1 出荷指示書 §4 と同じ手順（1 本ずつ、`requirements*.txt` 以外を触っていたら停止、CI green のみ merge、ランタイム依存を merge したら dispatch もう 1 回）
8. `git log --oneline -3 main` / `git branch -a` / `git status --short` → 報告し、同ノートに `## S<n>` で追記

## 7. 運用調査（read-only、実装と独立。Codex の gh 権限で行う）
- Update News の scheduled run で **#377 1m34s / #378 1m45s / #383 1m36s** が通常 31〜40s の 2 倍以上かかっている。各 run のログで **どの step が長いか**（`pip install` / `fetch_news.py` / `git push` のリトライ）と、遅い場合に `[FEED FAIL]` `[RANKING FAIL]` が出ていたかを報告する。修正・workflow 編集はしない

## 8. 参考: 現行コードの該当箇所（`df4ec46` 時点）
- `_parse_rank_number` L102-105、`append_ranking_item` L88-99、`summarize_error` L71-77、`redact_detail` L64-68
- `extract_gizmodo_ranking` L184-261（フォールバック L195-196、active 判定 L225、`min_title_length` L253）
- `extract_fashionsnap_ranking` L308-385（section 条件 L326、初期選択 L339-340、`_7rl1co1` L346、`si7p730` L357、`si7p732` L365、`min_title_length` L380）
- `extract_nikkei_ranking` L387-411（`select_one` L390、`min_title_length` L409）
- 既存テスト: `scripts/tests/test_extractors.py`（GIZMODO 3 / FASHIONSNAP 3 / 日経 1 / TechCrunch 1）、fixture 8 本
