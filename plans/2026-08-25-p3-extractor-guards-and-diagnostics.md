# P3 指示書: 厳格 3 抽出器のタイトルガードと fail-closed 診断ログ（Codex 向け）

作成: 2026-08-25（Claude Fable 監督セッション。P2 出荷 verify（S4 の P3 backlog / S6 のサイジング）を指示書化）
対象リポジトリ: `~/projects/news-dashboard`（開始時点 main = `37f841e` 以降。cron の生成物 commit `Update news dashboard …` が積まれていてよい）
レーン: 実装フェーズ **M**（3 抽出器の負例ガード追加・fixture 整備・STDOUT 診断。`status.json` の形・`detail` の文言・workflow・成功条件の厳格さは変えない）。出荷フェーズ（§6）は **L**（本番 workflow への merge・dispatch）
背景: Obsidian `40_Sessions/2026-08/2026-08-25/2026-08-25-news-dashboard-P3抽出器ガードと診断ログ.md`（topic_id `news-dashboard-p3`）。前段: P2 `16324d8`（PR #5、squash `64a95cd`、`plans/2026-08-25-p2-anchor-robustness.md`）。P2 ノート（topic_id `news-dashboard-p2`、done）の S4「P3 backlog」と S6「残作業のスコープ」が出所

---

## 0. 前提条件と開始前チェック

### 0-a. P2 と同じ点・違う点（最初に読む）
- 手順は P2 と同じ「fixture 先行 → 実装 → テスト → push → PR → CI green → **停止して §5 の形式で報告**」。監督が pytest を自走し diff を読んだ後に **reviewed head SHA を明記した GO** を出す。**GO が来るまで merge・dispatch はしない**（CI green は GO ではない）
- P2 で「再デプロイで勝手に変わるアンカー」を排除した。P3 は (1) P2 の D3（`min_title_length` 既定 1）で開いた「タイトルが順位番号そのもの」の穴を GIZMODO / 日経にも閉じ、(2) fixture が主張どおりの単一原因になるよう直し、(3) 抽出器が `[]` に倒れた地点を **Actions ログにだけ** 残す。**`ok` を増やす変更は一切含まない**。ライブ 3 サイトの before/after は完全一致でなければならない
- **SNS（xAI / `fetch_sns_posts` / `fetch_all_sns` / SNS タブ）には触らない**。SNS の復旧と可視化は別セッション・別指示書で扱う。P2 ノート S6 に改善案が書いてあるが、それをこの PR に「ついでに」入れない

### 0-b. Codex が最初に行うチェック
1. `git switch main && git pull --rebase && git status --short` → untracked が本指示書 `plans/2026-08-25-p3-extractor-guards-and-diagnostics.md` の 1 本だけであること。それ以外がダーティなら止まって報告
2. 作業ブランチ: `git switch -c feat/p3-extractor-guards`。最初の commit は指示書だけ: `git add plans/2026-08-25-p3-extractor-guards-and-diagnostics.md && git commit -m "docs: P3 指示書を追加"`
3. `python --version` が 3.12 系（CI と同じ）。`pip install -r scripts/requirements-dev.txt`（pytest 9.1.1）
4. `python -m pytest scripts/tests -q` → **43 passed** を baseline として記録
5. `git diff --stat 64a95cd HEAD -- scripts/` が空であること（P2 出荷後に `scripts/` が変わっていない。変わっていたら止まって報告）
6. ライブサイト（gizmodo.jp トップ / fashionsnap.com/ranking/ / nikkei.com/access/）に本番 UA `NewsDashboard/1.0 (+https://github.com/Tomotaka-u/news-dashboard)` で取得できること。できない環境なら §4-3 は `[検証不能]` として報告（fixture テストだけで実装は進めてよい。before/after は監督が代行する）
7. 着手前に現行コードで 3 サイトのライブ結果を保存する（§4-3 の before）: `build_http_session()` → 各 URL 取得 → `extract_*_ranking(soup, url)` → title / link 5 件を取得時刻つき JSON で残す。**同じ生 HTML も保存する**（実装後に同じ HTML へ新コードを当てて「同一 HTML での before/after」を出すため）

## 1. 目的（何を達成するか）

| # | 問題 | 場所（`37f841e` 時点の `scripts/fetch_news.py`） |
|---|---|---|
| 1 | GIZMODO / 日経に「タイトルが順位番号そのもの」を拒否するガードが無い。FASHIONSNAP には `_parse_rank_number(title) is not None → []` がある（L389-395）。P2 D3 で `min_title_length` が 1 になったため、`"1."` のようなタイトルが長さでは弾けず `ok` で出る | GIZMODO L252-254、日経 L436 |
| 2 | GIZMODO は `rankingTitle` 要素が無いとき `a_tag.get_text()` にフォールバックする。順位テキストを含んだ「`1 タイトル`」が `ok` で出る経路であり、P1 Step 2 以来の D0（実行時フォールバック禁止）と矛盾する | L252-253 |
| 3 | `fashionsnap-ranking-all-rank-gap.html` が土台 `fashionsnap-ranking-categories.html` に対して順位飛び以外の差分（他 3 系列のカテゴリリンク 15 本の消失。`href="/article/` が 60 → 45）を含む。単一原因の負例になっていない | `scripts/tests/fixtures/` |
| 4 | `fashionsnap-ranking-rehashed-categories.html` は土台に class が無いため「class を追加しても通る」テストになっており、`test_extract_fashionsnap_ignores_rehashed_classes` の主張（ハッシュ回転に耐える）を検証していない。また `s3r3r52` リテラル（L339）が回転したときに fail-closed する負例が無い | 同上、`test_extractors.py:190` |
| 5 | `fashionsnap-ranking.html` / `fashionsnap-ranking-weekly-second.html` はどのテストからも参照されない（`grep` 0 件）。P2 で「履歴 fixture として残す」としたが、参照ゼロのファイルは次の人を迷わせる | 同上 |
| 6 | 3 抽出器の fail-closed 分岐 **27 箇所**（リテラル `return []` 18 + 空の `return items` 6 + 末尾三項 3）が全て `fetch_ranking` の `parser '<type>' returned 0 items`（L631）に潰れ、本番でどのアンカーが無かったか判別できない。P1 から続く既知の制約 | L185-260 / L308-406 / L409-439 |

**成功の定義**: 上記 1〜6 を直した後も、(a) 既存の正例 fixture の順位 1〜5 と記事の対応は変わらない、(b) ライブ 3 サイトの before/after の title / link 5 件が完全一致（同一 HTML での比較も一致）、(c) `docs/status.json` のキー集合・`sources` 行の形・`status` / `detail` の文言が **バイト単位で不変**、(d) 3 抽出器の内側に裸の `return []` と空の `return items` が **0 件**。

## 2. 設計判断（確定済み。変えたい場合は理由を添えて報告し、勝手に変えない）

### D0. 共通規則（P1 Step 2 / P2 の D0 を継続）
- 成功条件は「1〜5 がこの順で現れ、各順位に記事リンクが 1 本対応し、5 件そろう」で不変。緩めない
- 実行時フォールバック・try/except で `[]` を握りつぶす書き方を追加しない
- テストは **fixture を先に書き、失敗を確認してから実装**する。現行コードで通ってしまう負例は負例になっていない。既存実装がすでに fail-closed の負例は PASS でよく、どれがそうだったかを分けて報告する
- 順位番号の判定は既存 `_parse_rank_number`（L103-106）を使う

### D1. GIZMODO / 日経の数字タイトル拒否（backlog #1）

#### D1-a. ガードの横展開
- FASHIONSNAP L389-395 と同じ条件（`not title or _parse_rank_number(title) is not None`）を GIZMODO と日経の `append_ranking_item` 呼び出し直前に入れる。`title` は `sanitize_text` 後の値で判定する。**各抽出器でガードは 1 箇所**（D3 の理由 `<site>:title` と 1 対 1）
- GIZMODO: D1-b と合わせて `title = sanitize_text(title_node.get_text(" ", strip=True)) if title_node else ""` とし、`rankingTitle` 欠落は「空タイトル」として同じ 1 つのガードに落とす（欠落用の分岐を別に作らない）
- 日経: `a_tag.get_text(strip=True)` を一度 `title` 変数に取り、ガードを通してから `append_ranking_item` に渡す（L436）

#### D1-b. GIZMODO の `rankingTitle` フォールバック撤廃（**backlog の記載を超える判断。§5 で明示報告**）
- 現行 L252-253 の `title_node.get_text(...) if title_node else a_tag.get_text(...)` を、**`rankingTitle` 要素必須**に変える。無ければ `[]`
- 理由: D1-a のガードだけでは、`rankingTitle` 消失時に `a_tag.get_text()` が返す「`1 タイトル`」（順位＋タイトルの連結）は順位番号として解釈されず `ok` で通る。タイトルの取得元を 1 つに固定するのが D0（実行時フォールバック禁止）と整合し、`rankingPosition` / `rankingList` / `rankingContainer` と同じ「基底名の部分一致」アンカーなので再デプロイ耐性は他と同等
- ライブ GIZMODO には `rankingTitle` がある（正例 fixture はライブ由来）ので before/after は変わらないはず。変わったら止まって報告

#### D1 fixture（先行。全て既存 fixture のコピー＋最小改変、単一原因）
| テスト | fixture | 改変 | 期待 | 実装前 |
|---|---|---|---|---|
| GIZMODO タイトルが順位番号 | `gizmodo-ranking-title-is-rank-number.html` | `gizmodo-ranking.html` の rank 1 の `rankingTitle` テキストを `1.` に | `[]` | FAILED（現行は 5 件返す） |
| GIZMODO `rankingTitle` 要素なし | `gizmodo-ranking-title-node-missing.html` | rank 1 の `rankingTitle` div を外し、そのテキストを `a` 直下の生テキストとして残す | `[]` | FAILED（現行は fallback で 5 件返す） |
| 日経 タイトルが順位番号 | `nikkei-ranking-title-is-rank-number.html` | `nikkei-ranking.html` の rank 1 の `.m-miM32_itemTitleText a` テキストを `1` に | `[]` | FAILED |

### D2. fixture の単一原因化（backlog #2）

#### D2-a. `fashionsnap-ranking-all-rank-gap.html`
- `fashionsnap-ranking-categories.html` から作り直す。差分は **all 系列の順位アンカーのテキスト 3 箇所だけ**（`3`→`4`、`4`→`5`、`5`→`6`）。href・他 3 系列・カテゴリリンクは一切変えない
- 検証: `grep -o 'href="/article/[^"]*"' | wc -l` が土台と同じ **60**。prettify（`BeautifulSoup(...).prettify()`）した両者の `diff` が順位テキスト 3 行以外に出ない。既存 `test_extract_fashionsnap_rejects_rank_gap_in_all_series` は無変更で PASS のまま

#### D2-b. `fashionsnap-ranking-rehashed-categories.html` と回転負例
- `x-main` / `x-tab` 等の意味のある名前を、vanilla-extract 風のハッシュトークン（例: `_1q9zk30` `s7f2ab1` `he4j7q0` のような英数字 6〜8 文字。旧 `fashionsnap-ranking.html` の書式を参考にする）に置き換える。時間 tabs・カテゴリ tabs・順位リンク・タイトルリンク・wrapper 全てに付ける。weekly の `s3r3r52` は残す（そこに別のハッシュを併記してよい）。**これは fixture を実 DOM 風に整える整形であり、抽出器が読む class は `s3r3r52`（L339-340）だけなので挙動は変わらない**（テストの主張と見た目を一致させるのが目的）
- `test_extract_fashionsnap_ignores_rehashed_classes` は、期待リンク列を直書きするのではなく **`fashionsnap-ranking-categories.html` の抽出結果と等しく、かつ `len(items) == 5`** を assert する形に変える（class 非依存の主張をテストに書く。絶対値は `test_extract_fashionsnap_all_category_top_five_in_rank_order` が引き続き固定する）
- 新規負例 `fashionsnap-ranking-weekly-hash-rotated.html`: `categories.html` の weekly から `s3r3r52` を別トークン（例: `s3r3r99`）に変えるだけ（1 箇所）。期待 `[]`。現行コードでも fail-closed なので実装前 PASS でよい（その旨を報告）

#### D2-c. 孤児 fixture の削除（**P2 指示書 D1 末尾「履歴 fixture として残す」の撤回。§5 で明示報告**）
- `fashionsnap-ranking.html` と `fashionsnap-ranking-weekly-second.html` を `git rm` する。git 履歴に残るので参照が必要なら `git show 64a95cd:scripts/tests/fixtures/fashionsnap-ranking.html` で取り出せる
- 削除前に D2-b のハッシュ書式の参考として読む

### D3. fail-closed 地点の診断ログ（backlog #3。**STDOUT のみ、公開面は不変**）

#### 仕組み
- モジュールレベルに「直近の fail-closed 理由」の置き場を 1 つ作る（例: `_RANKING_DIAG = {"reason": None}`）。ヘルパー `_ranking_fail(reason)` は理由を記録して `[]` を返す
- **リセットは 2 か所**: (1) `fetch_ranking` が `extractor(soup, ranking_url)`（L625）を呼ぶ **直前** に理由を `None` にし、DETAIL を print した **直後** にも `None` に戻す（consume）。(2) 3 つの厳格抽出器（GIZMODO / FASHIONSNAP / 日経）の入口でも `None` にする（テストが抽出器を直接呼んでも前の呼び出しの理由が残らないように）。(1) が無いと、`run()` は `config.SITES` を逐次処理するため、日経が落ちた直後に PR TIMES / Yahoo / BBC（非厳格抽出器）が 0 件だったとき `[RANKING FAIL DETAIL] PR TIMES: anchor=nikkei:rank_seq` のような**他サイト名の偽の行**が出る（GIZMODO → The Verge も同様）
- 3 抽出器の内側の fail-closed 分岐を **全て** `return _ranking_fail("<site>:<anchor>")` に置き換える。対象は §1-6 の 27 箇所: リテラル `return []`、`items` が空のまま早期 return している `return items`、末尾の `return items if … else []`（`else _ranking_fail(...)` にする）。`continue`（GIZMODO L240 の `position is None`）は失敗ではないので対象外
- `fetch_ranking`（L631 の直前）で、`items` が空 **かつ** 理由が記録されているときだけ `print(f"[RANKING FAIL DETAIL] {site.get('name', '?')}: anchor={reason}")` を出す。理由が無ければ何も出さない（TechCrunch 等の他抽出器や、テストの `lambda soup, url: []` はこの経路。`fetch_ranking` は現状 `site["name"]` を参照していないので `.get` で読む）
- **`build_fetch_result` の `detail` には理由を入れない**。`status` / `detail` の文言・`status.json` のキー集合・`sources` 行の形は不変。理由は `run()` 側の `[RANKING FAIL]` 行にも混ぜない（`fetch_ranking` の print だけ）

#### 理由の語彙
- 形式は `<site>:<anchor>` の固定 ASCII 識別子。**動的な文字列（URL・パス・HTML テキスト・例外文）を絶対に含めない**（STDOUT は公開されないが、公開面と同じ衛生を保つ）
- 提案する 29 個（D1 で増える 2 個を含む。名前は変えてよいが、対応表を §5 に載せる）:

| 抽出器 | 現行行 | 条件 | 理由 |
|---|---|---|---|
| GIZMODO | L196 | 見出し `RANKING` なし | `gizmodo:heading` |
| GIZMODO | L202 | `rankingContainer` なし | `gizmodo:container` |
| GIZMODO | L221 | Daily tab なし / tabs≠panels / index 超過 | `gizmodo:tabs_panels` |
| GIZMODO | L226 | Daily tab が `ranking_active` でない | `gizmodo:daily_inactive` |
| GIZMODO | L232 | `rankingList` なし | `gizmodo:list` |
| GIZMODO | L242 | 順位が期待値と不一致 | `gizmodo:rank_seq` |
| GIZMODO | L246 | host が gizmodo.jp でない | `gizmodo:host` |
| GIZMODO | L249 | `/tag/` `/issue/` `/author/` | `gizmodo:excluded_path` |
| GIZMODO | L251 | `/article/` / `/YYYY/MM/` に不一致 | `gizmodo:path_pattern` |
| GIZMODO | 新規（D1） | `rankingTitle` なし / 空 / 順位番号 | `gizmodo:title` |
| GIZMODO | L256 | append 後の件数不一致（重複リンク） | `gizmodo:dup_link` |
| GIZMODO | L260 | 末尾 5 件未満 | `gizmodo:count` |
| FASHIONSNAP | L318 | 見出し `トップ100` なし | `fashionsnap:heading` |
| FASHIONSNAP | L331 | weekly/monthly/記事リンクを含む section なし | `fashionsnap:section` |
| FASHIONSNAP | L342 | weekly/monthly の親不一致・初期選択の証拠なし | `fashionsnap:time_tabs_selection` |
| FASHIONSNAP | L346 | 時間 tabs が 2 でない | `fashionsnap:time_tabs_count` |
| FASHIONSNAP | L350 | `data-testid="all"` が 1 でない | `fashionsnap:all_tab` |
| FASHIONSNAP | L358 | カテゴリ tabs が 4 / 集合不一致 | `fashionsnap:category_tabs` |
| FASHIONSNAP | L373 | 系列開始数 ≠ tabs 数 | `fashionsnap:series_count` |
| FASHIONSNAP | L381 | all 系列が途中で尽きる | `fashionsnap:series_short` |
| FASHIONSNAP | L385 | タイトルアンカーが無い | `fashionsnap:title_missing` |
| FASHIONSNAP | L395 | 順位不一致 / href 不一致 / 空 / 順位番号 | `fashionsnap:rank_title_pair` |
| FASHIONSNAP | L405 | append 後の件数不一致 | `fashionsnap:dup_link` |
| FASHIONSNAP | L406 | 末尾 5 件未満 | `fashionsnap:count` |
| 日経 | L424 | 「総合」かつ「今日」のコンテナなし | `nikkei:container` |
| 日経 | L435 | 順位ノード / リンクなし / 順位不一致 | `nikkei:rank_seq` |
| 日経 | 新規（D1） | タイトル空 / 順位番号 | `nikkei:title` |
| 日経 | L438 | append 後の件数不一致 | `nikkei:dup_link` |
| 日経 | L439 | 末尾 5 件未満 | `nikkei:count` |

- 既知の制約（直さない）: `fashionsnap:rank_title_pair` は L389-395 の 4 条件（順位不一致 / href 不一致 / 空 / 順位番号）を 1 語彙に潰す。分割は 29 件固定と衝突するので、§5 の対応表にこの制約を 1 行残す

#### テスト
- `scripts/tests/test_fetch_ranking.py` に 3 本: (a) `_ranking_fail("fixture:anchor")` を返す偽抽出器で `capsys` に `[RANKING FAIL DETAIL] Fixture: anchor=fixture:anchor` が出て、`result["detail"]` は `parser 'fixture' returned 0 items` のまま、`result` のキーは `items` / `status` / `detail` だけ、print 後に理由が `None` に戻っている、(b) **事前に理由を手で残した状態で** `lambda soup, url: []` を `fetch_ranking` 経由で通しても DETAIL 行が **出ない**（呼び出し直前リセットの確認。pytest はファイル名順に収集するので `test_extractors.py` の負例が残した理由がここに流れ込む）、(c) 負例 fixture で理由が記録された直後に正例 fixture を直接呼ぶと理由が `None` に戻る（入口リセットの確認）
- `scripts/tests/test_extractors.py` に理由の spot check を **3 本だけ**（全 29 個を assert しない。壊れやすさに見合わない）: GIZMODO `rank-gap` → `gizmodo:rank_seq`、FASHIONSNAP `all-missing` → `fashionsnap:all_tab`、日経 `no-match` → `nikkei:container`
- 完了条件の grep（§4-5）: 3 抽出器の行範囲で `return \[\]` と行末の `return items` が **0 件**

#### 実装順（commit を分ける。PR は 1 本）
1. `docs:` 指示書
2. `test:` D1 / D2 の fixture とテストを追加（この時点で D1 の 3 本が FAILED、D2-b 回転負例は PASS）
3. `feat:` D1-a / D1-b の実装（43 → 43 + D1 3 + D2 1 = 47 passed）
4. `test:` D2-a / D2-b の fixture 修正、D2-c の削除
5. `feat:` D3 のヘルパーと FASHIONSNAP の 12 箇所（最多。ここでパターンを確定）
6. `feat:` D3 の GIZMODO / 日経への横展開と `fetch_ranking` の print、テスト 6 本（47 + 6 = 53 passed）
7. `docs:` D5

### D4. 見送り（記録のため。今回は触らない）
- `redact_detail` の `\?\S+`（L68）が日本語文中の ASCII `?` に誤爆する件: `detail` は英数字主体で実例なし、安全側（消しすぎ）の誤爆。直すなら `\?[\w=&%.-]+` 程度の 1 行だが、`detail` に触る変更が無い今回は入れない
- `_replace_all`（L852-855）のディレクトリ fsync なし: 使い捨て runner + 冪等な全件再生成 + 同一ジョブ内 commit なので守るべき障害シナリオが無い

### D5. ドキュメント（`CURRENT_STATE.md`、Codex に scope grant）
- L111 の GIZMODO 記述に「タイトルは `rankingTitle` 要素から取り、順位番号だけのタイトルは拒否する」を加える。L113 の日経にも「順位番号だけのタイトルは拒否」を加える
- L190-192「`status.json` / 画面の `detail` 方針」の直後に 1 段落: `[RANKING FAIL DETAIL] <site>: anchor=<site>:<anchor>` は Actions の STDOUT にだけ出る診断で、`status.json` / 画面には出さない。理由は固定識別子のみ
- 稼働状況の日付を更新。`.github/**` / `docs/**` には触らない

## 3. 制約・禁止事項
- 成功条件を緩めない。`ok` が増える変更は含まない
- `status.json` のキー集合（`generated_at` / `gate` / `feeds` / `rankings` / `sources`）、`sources` 行のキー（`name` / `kind` / `status` / `count` / `detail`）、`status` の語彙、`detail` の文言を変えない。`build_fetch_result` の戻り値にキーを足さない（`test_status_json.py:51` `:105`、`test_fetch_ranking.py` の `test_result_builder_does_not_allow_empty_success` が固定している）
- 抽出器のシグネチャ `extractor(soup, ranking_url) -> list` を変えない。例外で失敗を伝えない（`test_extractors.py` の負例 15 本が `[]` を期待している）
- **SNS 関連コード・設定・workflow に触らない**（§0-a）
- 他サイトの抽出器（TechCrunch / Verge / ITmedia / HN / BBC / PR TIMES / Yahoo）に触らない
- `.github/**` / `docs/**` を編集しない。`git add -A` / `--no-verify` / force push 禁止。fixture は **ファイル名を指定して** add する
- 各 fixture は 50KB 以下、トラッキング・PII を含めない
- コードコメントは英語、commit メッセージは日本語 Conventional Commits

## 4. 検証（報告に出力を貼る）
1. `python -m pytest scripts/tests -q` → baseline 43 → after **53 passed**（D1 3 + D2 1 + D3 6。数が違うなら内訳を説明）。`python -m compileall -q scripts`、`git diff --check`
2. 負例の **実装前 FAILED** 出力（D1 の 3 本）。既存で fail-closed だった負例（D2-b 回転）は PASS として分けて報告
3. ライブ before/after: 0-b-7 の before と、実装後の同手順の after を 3 サイト分並べる。**title / link が 5 件とも一致**。加えて 0-b-7 で保存した生 HTML に新コードを当てた結果も一致（同一 HTML での before/after）。不一致があれば止まって報告（サイト側の更新で順位が入れ替わった場合は取得時刻を添えて再取得 1 回まで）
4. D2-a の検証: `href="/article/` 件数 60 / 60、prettify diff が順位テキスト 3 行のみ
5. D3 の完了 grep: **3 関数それぞれの行範囲で個別に** `sed -n '<開始>,<終了>p' scripts/fetch_news.py | grep -nE 'return \[\]|return items$'` を実行し、3 つとも 0 件（行範囲は実装後の行番号で示す。間に挟まる The Verge / ITmedia / HN の `return items` は対象外で、触らない）。`grep -o '_ranking_fail(' scripts/fetch_news.py | wc -l` が **30**（定義行 1 + 呼び出し 29）
6. `[RANKING FAIL DETAIL]` の実出力例を 1 行（負例 fixture を `fetch_ranking` 経由で通した `capsys` 出力）
7. `git diff --stat main` に `.github/` / `docs/` が無いこと。`docs/status.json` を生成するテスト（`test_status_json.py`）が無変更で PASS していること。fixture の最大サイズ

## 5. 返却形式（監督が一次証拠で verify するため）

```
## 変更ファイル
## 判断の変更・追加（D0 の手続きを踏んだもの。D1-b と D2-c は「指示書どおり実施」でも必ず 1 行ずつ明記）
## D3 理由の対応表（29 行: 行番号 / 条件 / 理由）
## ランキング before/after（3 サイト × 5 件、取得時刻つき。同一 HTML での比較も）
## テスト・検証出力（baseline 43 → after 53、負例の実装前 FAILED、compileall、完了 grep、DETAIL 実出力）
## PR URL / head SHA / CI run ID / 結論
## 未解決・気づいた事項（修正はしない。SNS に関する気づきもここに書くだけ）
## 監督構成（レーン / 委譲 / 昇格 / 未確認）
```

ここで**停止**する。Obsidian: `40_Sessions/2026-08/2026-08-25/2026-08-25-news-dashboard-P3抽出器ガードと診断ログ.md` の末尾に `## S2 | 日付 | 一言` で追記（新規ノートは作らない。P2 ノートには書かない）。

## 6. 出荷（監督の GO 後のみ。GO メッセージには reviewed head SHA が書かれている）
1. `gh pr view <n> --json headRefOid` が **GO に書かれた SHA と一致**することを確認。違えば止まって報告
2. `gh run list --workflow=update-news.yml --limit 3` が全て success
3. `gh pr merge <n> --squash --delete-branch` → merge SHA → main push CI（`ci.yml`）success を `gh run watch`
4. `gh workflow run update-news.yml` を 1 回 → run ID / 結論 / update job 所要時間 / `[FEED FAIL]` `[RANKING FAIL]` `[RANKING FAIL DETAIL]` `Node.js 20` `deprecated` の件数と本文（DETAIL 行は 0 件が期待値。出ていれば anchor 名を報告し**パーサは直さない**）
5. `git pull --rebase` → `docs/status.json` の `generated_at` / `gate` / `feeds` / `rankings` / 非 ok 行の name・kind・status・detail 全部。キー集合が不変であること
6. `detail` に URL・パス・`?` クエリ・`Max retries exceeded with url:` が無いこと
7. open な Dependabot PR があれば P1 出荷指示書 §4 と同じ手順（1 本ずつ、`requirements*.txt` 以外を触っていたら停止、CI green のみ merge、ランタイム依存を merge したら dispatch もう 1 回）
8. `git log --oneline -3 main` / `git branch -a` / `git status --short` → 報告し、同ノートに `## S<n>` で追記

## 7. 運用調査
- 今回は無し。SNS（xAI 403）の調査・復旧は別セッションで扱う。run ログに `[SNS ERROR]` が出ていても §5「未解決」に件数を書くだけで、何もしない

## 8. 参考: 現行コードの該当箇所（`37f841e` 時点）
- `redact_detail` L64-68、`summarize_error` L71-78、`append_ranking_item` L89-100、`_parse_rank_number` L103-106
- `extract_gizmodo_ranking` L185-260（title fallback L252-253、append L254）
- `extract_fashionsnap_ranking` L308-406（`s3r3r52` L339-340、ガード L389-395）
- `extract_nikkei_ranking` L409-439（append L436）
- `fetch_ranking` L598-632（`empty` の detail L631）、`run()` の `[RANKING FAIL]` L910-913
- テスト: `test_extractors.py`（GIZMODO 6 / FASHIONSNAP 12 / 日経 4 / TechCrunch 1）、`test_fetch_ranking.py` 3、`test_status_json.py` 3、`test_detail_sanitization.py` 5、他（`test_atomic_write` / `test_gate` / `test_http_headers`）。fixture 25 本、最大 4,198 bytes
