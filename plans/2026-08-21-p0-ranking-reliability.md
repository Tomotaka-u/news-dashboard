# P0 指示書: Rankings の「信頼性の嘘」を止める（Codex 向け）

作成: 2026-08-21（Claude Fable 監督セッション。Opus 独立レビュー 1 回反映済み）
対象リポジトリ: `~/projects/news-dashboard`
レーン: **L**（本番 cron の「常に commit する」不変条件を変更し、`docs/status.json` という Python→テンプレ間の新契約を定義するため）
背景レビュー: Obsidian `40_Sessions/2026-08/2026-08-21/2026-08-21-news-dashboard-包括レビュー.md`（S1 = 棚卸し、S2 = 本指示書の作成経緯）

---

## 0. 前提条件と開始前チェック

### 0-a. ユーザーが dispatch 前に済ませること（Codex はやらない）
2026-08-21 の Claude セッションで次の未 commit 変更が残っている: `.github/workflows/update-news.yml`（timeout / pip cache / JST 日付）、`.gitignore`、`CURRENT_STATE.md`、`plans/`（本ファイル）。またローカル `main` は `cb0fad7` が未 push で、origin には 6/5 以降の cron commit（`docs/` のみ）が積まれている。
ユーザーが **先に** これらを commit → `git pull --rebase` → push して同期してから Codex を起動する。

### 0-b. Codex が最初に行うチェック
1. `git status --short` が空であること（`plans/` の未追跡のみ許容）。それ以外がダーティなら **止まってユーザーに報告**（0-a が未了）。
2. `git log --oneline -5` に `Update news dashboard 2026-08-xx`（github-actions bot）の commit があること。なければ 0-a の同期が未了なので**止まって報告**（自分で fetch/pull/push/force はしない）。
3. `python --version` が 3.12 系（CI と同じ）であること。違う場合は 3.12 互換の構文だけを使う。
4. `pip install -r scripts/requirements.txt` が通ること。
5. ライブサイト（gizmodo.jp / techcrunch.com / wwdjapan.com / nikkei.com）に本番 UA で HTTP 取得できること。**できない環境なら D5 は推測で書かず `[検証不能]` として止まり、D1〜D4 / D6〜D8 だけ進めて報告**する。

## 1. 目的（何を達成するか）

Rankings タブの「10 / 12 sources · 2 failed」は実態（本物の人気ランキングを取れているのは 7〜8 / 12）を表していない。原因は次の 3 つで、P0 はこれを止める。

| # | 問題 | 場所（cb0fad7 時点の行） |
|---|---|---|
| H1 | 専用パーサが 0 件のとき汎用フォールバック（`extract_generic_ranking`）が拾ったタグ/特集ページを **success に計上**している | `scripts/fetch_news.py` `fetch_ranking()` L496-510 → `main()` L744-746 |
| H5 | 品質ゲートがない。全ソース 0 件でも render → 書き込み → commit され、正常版を空ページで上書きしうる | `main()` L749-781、`update-news.yml` の commit step |
| H4/H6 | 観測性ゼロ。ソース単位の成否がどこにも残らず、フィード側は 0 件サイトがカードごと消えるだけ。同じ壊れ方が 2.5 か月放置された | `main()`・`templates/index.html.j2` |

**成功の定義**: 画面とログが「何が取れて何が取れていないか」を正直に示し、空ページが本番に出ない。**表示上の成功数は下がってよい**（それが真実）。

## 2. 設計判断（確定済み。変えたい場合は理由を添えて報告し、勝手に変えない）

### D1. 汎用フォールバックは廃止する
- `extract_generic_ranking`（L293-321）と `fetch_ranking` 内のフォールバック分岐（L485-487, L496-510）を**削除**。専用パーサが 0 件なら失敗として扱う。未知の `ranking_type` も汎用パーサに回さず `parse_error` 扱い。
- 理由: グローバル規約「サイレントなフォールバック禁止」。「それらしく見える嘘」より「0 件」の方が価値がある。

### D2. `fetch_feed` / `fetch_scrape_news` / `fetch_ranking` は結果オブジェクトを返す
呼び出し元は `main()` のみ（L732 / L734 / L742）。他に呼び出しは無い。
```python
# plain dict で可（dataclass でもよい）
{"items": [...], "status": "ok" | "empty" | "http_error" | "parse_error" | "skipped", "detail": "<短い人間向け説明。例外メッセージは 200 字で切る>"}
```
- `ok`: HTTP 成功かつ **フィルタ後の** items ≥ 1
- `empty`: HTTP 成功だがフィルタ後の items が 0（feed なら entries 0 or 全件 title/link 欠落。`bozo=1` は `detail` に書くが status は変えない）
- `http_error`: リクエスト失敗（タイムアウト / 4xx / 5xx / 接続不可）
- `parse_error`: パーサ内で例外、または未知の `ranking_type` / `scrape_type`
- `skipped`: 設定不足で取得を試みなかった（現行 L432-433 / L465-466 の無言 `return []` に相当。現 `SITES` では到達しないが契約として定義）
- `main()` は `status == "ok"` のときだけ success に数える。ログは `[FEED FAIL] {name}: {status} {detail}` / `[RANKING FAIL] {name}: {status} {detail}` に統一（grep しやすく）。

### D3. 品質ゲートは「空ページを出すか」だけで判定する
- `scripts/config.py` に定数を追加:
  ```python
  MIN_TOTAL_ITEMS = 20  # quality gate: refuse to publish when fewer feed/scrape items than this were collected
  ```
- 数値の根拠: `SITES` は 17 件、`MAX_ITEMS_PER_SITE = 8` なので上限 136 件、直近の正常時実測は `overall_total = 120`（6/5 スナップショット `All · 120`、15/17 サイトに記事あり）。20 は健全時の約 17% で「ほぼ全滅」だけを弾く。**75% 崩壊しても publish される**のは受容するリスク（ソース単位の劣化は D4 で可視化）。フル実行の `overall_total` を報告に書き、不適切なら提案する（勝手に変えない）。
- `main()` でフィード＋ランキング収集の直後、`overall_total` 確定後（現 L749）かつ **`fetch_all_sns` の前（現 L752）** に判定（失敗時に xAI API を叩かない）:
  `overall_total < MIN_TOTAL_ITEMS` → `[GATE FAIL] overall_total=N < MIN_TOTAL_ITEMS=20; not writing docs/` を出して **何も書かずに `sys.exit(1)`**（`try/finally` で session は閉じる）。
- ランキング成功率はゲートに**入れない**（D5 でソースを外すと分母が動いて flap する）。ただし `rankings.ok_sources == 0` のときは `[RANKING ALL FAIL] all N ranking sources failed` を 1 行ログに出す。「記事は健全・ランキング全滅」で green publish になるのは**受容するリスク**として明記しておく。
- Actions 側は変更不要: step が非 0 で終われば commit step は実行されず（`if: always()` 無し）、前回の正常版が残る。scheduled workflow の失敗は GitHub が owner に通知する。
- テスト用の環境変数 `NEWS_MIN_TOTAL_ITEMS`: **ゲート実行時に `os.environ` を読む**（import 時ではない）。`int()` に失敗したら握りつぶさず例外で落とす。未設定なら config の値。

### D4. `docs/status.json` を出力し、画面にも成否を出す
- 書き出し先: `docs/status.json`（`git add docs/` の対象に自動で入る）。`json.dump(..., ensure_ascii=False, indent=2, sort_keys=True)` + 末尾改行。**ゲート失敗時は書かない**。
- 形（数値は例。`*_sources` は**ソース数**、`overall_total` / `count` は**記事件数**）:
  ```json
  {
    "generated_at": "2026-08-21T18:05:12+09:00",
    "gate": {"passed": true, "overall_total": 118, "min_total_items": 20},
    "feeds":    {"total_sources": 17, "ok_sources": 15},
    "rankings": {"total_sources": 11, "ok_sources": 9},
    "sources": [
      {"name": "TechCrunch", "kind": "feed",    "status": "ok",    "count": 8, "detail": ""},
      {"name": "TechCrunch", "kind": "ranking", "status": "ok",    "count": 5, "detail": ""},
      {"name": "AI News",    "kind": "feed",    "status": "empty", "count": 0, "detail": "0 entries after filtering (bozo=1: ...)"}
    ]
  }
  ```
  `kind` は `feed` | `scrape`（`type: scrape` の PR TIMES / Yahoo!ニュース）| `ranking`。`sources` は `SITES` の順、同一サイトは feed/scrape 行 → ranking 行の順（`main()` の既存ループ順と同じ）。`feeds.total_sources` は feed+scrape の合計（=17）。`SITES` の `name` に重複は無い（サイト識別子として使ってよい）。
- テンプレに渡す変数:
  - `source_status`: status.json の `sources` と同一 list
  - `feed_status_by_name`: `{name: {"status", "detail"}}`。**feed/scrape 行だけ**から作る（ranking 行で上書きしない。`kind != "ranking"` で絞る）。サイドバーはこれを引く
  - `ranking_status` の拡張: `failed_names: ["GIZMODO JAPAN (empty)", "WWDJAPAN (http_error)"]`（**整形済み文字列の list**。テンプレは `", ".join`するだけ）
  - その他の既存変数・HTML 構造は変えない
- 画面（`templates/index.html.j2` ＋ `templates/partials/index.css`）:
  1. サイドバー「ソース一覧」（L47-53）で `feed_status_by_name[site.name].status != "ok"` のサイトに `<span class="source-status-failed" title="{{ detail }}">取得失敗</span>` を付ける（テキスト必須。色だけで伝えない）。色は**実効背景**（`.sidebar` は `rgba(255,255,255,0.7)` + blur を `#f5f3f0` に重ねたほぼ白）に対して **コントラスト 4.5:1 以上**（例: `#b42318`。実測値を報告に書く）。
  2. `templates/partials/index.js` L40-46 がサイドバーのリンクを `cloneNode(true)` してモバイルドロワーに複製するので、バッジも複製される。`.mobile-source-link` 側で崩れないことを目視確認（JS 変更は不要なはず。必要なら最小限）。
  3. Rankings ヘッダ（L163-171）の `X / Y sources · Z failed` の直下に `失敗: {{ failed_names | join(", ") }}` を表示。空表示（L196-200）側にも同じ列挙。
  4. サイドバーフッター（L55-58）に `<a href="status.json">status.json</a>` リンクを追加。

### D5. パーサ修正と対象整理（ライブ検証必須・本番 UA で）
本番 UA は `NewsDashboard/1.0 (+https://github.com/Tomotaka-u/news-dashboard)`（`fetch_news.py` L24 `USER_AGENT`）。ブラウザ UA で見えてもボットには見えないことがあるので、**必ずこの UA で** `requests` か `curl -A` で取得して確認する。取得できない環境なら 0-b-5 に従う。

| サイト | 現状（2026-08-21 ライブ、S1 で確認済み） | やること |
|---|---|---|
| GIZMODO JAPAN | トップに h3「Ranking」はあるが、記事 URL が `/article/<slug>/` 形式で、L149 の正規表現 `r"/\d{4}/\d{2}/"` に不一致 → 構造的に常に 0 件 → フォールバックが `/issue/…` `/tag/…` を拾っていた。`/ranking/` 専用 URL は 404 | 正規表現を `r"/(article/|\d{4}/\d{2}/)"` 相当に修正。`/tag/` `/issue/` `/author/` 等は明示除外。本番 UA で 5 件すべてが記事 URL・タイトル 10 字以上になることを確認 |
| TechCrunch | 「Top Headlines」（L113 の文字列）= 編集部最新枠（8/21 は 5 件全部 08/20 の記事、Disrupt 宣伝含む）。トップに別途「Most Popular」モジュールあり | 「Most Popular」モジュール起点に変更。**サーバ HTML に含まれるか確認**（JS で後から描画される場合、本番 UA の取得結果に無い）。含まれなければ `config.py` の `ranking_url` / `ranking_type` を外して**ユーザー判断事項として報告**（Top Headlines を残さない。人気順でないものを Rankings に出さない） |
| JDN | `/pickup/` は編集部ピックアップで人気順ではない。かつ 0 件 | **3 箇所を同時に削除**: `config.py` L106-107 の `ranking_url` / `ranking_type`、`fetch_news.py` の `extract_jdn_ranking`（L241-269）、`RANKING_EXTRACTORS` の `"jdn"` エントリ（L421）。関数だけ消すと import 時 NameError で本番即死。**ユーザーが覆せる判断として報告に明記** |
| WWDJAPAN | `/ranking` が本番で 0 件。ブラウザ経由では `articles/` リンクが存在。feed 側は生きている | 本番 UA で取得し、status code / body 長 / `articles/` リンクの有無を**診断して証拠を残す**。UA/Accept 起因なら `build_http_session()` に既定ヘッダ `Accept: text/html,application/xhtml+xml,*/*;q=0.8` と `Accept-Language: ja,en;q=0.8` を追加して再確認（P1 項目だが原因なら今やってよい）。それでも 0 件なら `ranking_url` / `ranking_type` を外してユーザー判断として報告 |
| 日経新聞 | `/access/` からページ全体の `/article/` 先頭 5 件。ランキング表か上部の主要ニュース枠か未判別 | 本番 UA で取得し、先頭 5 件がアクセスランキングの並びかを**確認して報告**。違えばランキングコンテナ起点に直す（確認だけで直さなくてもよいが結果は必ず書く） |
| その他 7 サイト（HN / Verge / BBC / ITmedia / FASHIONSNAP / Yahoo / PR TIMES） | 取れている | 触らない。フォールバック廃止後も `ok` であることをフル実行で確認 |

### D6. モデル名のハードコード解消（小）
- `fetch_news.py` L603 の `"grok-4-1-fast-reasoning"` を `config.py` の `DEFAULT_XAI_MODEL` に移し、`os.environ.get("XAI_MODEL") or DEFAULT_XAI_MODEL` で参照。workflow は触らない。

### D7. 依存
- `scripts/requirements.txt`: `jinja2==3.1.4` → `3.1.6`（CVE-2024-56201 / 56326 / 2025-27516 修正版）。`urllib3` を直接 import しているので**明示ピン**（`pip show urllib3` の版。`requests==2.32.3` の制約 `urllib3>=1.21.1,<3` 内であること）。クリーンな venv で `pip install -r` が解決し、フル実行が通ることを確認。

### D8. テスト（新規 `scripts/tests/`）
- `pytest` は `scripts/requirements-dev.txt` に追加（CI には載せない。P1 で `ci.yml` を別途）。`scripts/` はパッケージではないので `scripts/tests/conftest.py` で `sys.path` に `scripts/` を通す。
- `main()` の分割は次の形に限定: `run(session=None, output_dir=None)` を切り出し、`output_dir=None` のときは**従来どおり `__file__` 起点の `docs/`**（現 L754, L777）に解決する。`python scripts/fetch_news.py` の挙動・出力先は不変。**環境変数で出力先を切り替える実装はしない**。
- テストは fetcher（`fetch_feed` / `fetch_scrape_news` / `fetch_ranking` / `fetch_all_sns`）を monkeypatch し、**実ネットワークアクセスを一切行わない**。
- 最低限:
  - `test_gate.py`: `overall_total` がしきい値未満で `SystemExit(1)` かつ `tmp_path` に何も書かれない／以上で `index.html` と `status.json` が書かれる。`NEWS_MIN_TOTAL_ITEMS` の上書きと不正値での例外も 1 本ずつ。
  - `test_status_json.py`: status.json のキー・`sources` の並び・行の形、`feed_status_by_name` が ranking 行で上書きされないこと。
  - `test_fetch_ranking.py`: 専用パーサ 0 件 → `status == "empty"` かつ items 空（フォールバックが復活していないことの回帰テスト）。未知 `ranking_type` → `parse_error`。
  - `test_extractors.py`: GIZMODO / TechCrunch の**保存 HTML フィクスチャ**（該当モジュール周辺だけ切り出し、1 ファイル 50KB 以下、`scripts/tests/fixtures/`）で 5 件取れること。
- 既存の他パーサにテストを**後付けしなくてよい**（スコープ外）。

### D9. ドキュメント
- `CURRENT_STATE.md`（AGENTS.md が宣言する正本）の該当節を同時に更新: フォールバック記述（「0件だった場合は `extract_generic_ranking` にフォールバック」→廃止）、「稼働状況（2026-08-21 時点）」表、Jinja2 変数一覧（`source_status` / `feed_status_by_name` / `ranking_status.failed_names`）、JDN 行、`docs/status.json` の存在とファイル構成図、`MIN_TOTAL_ITEMS` / `DEFAULT_XAI_MODEL`。

## 3. 制約・禁止事項

- `AGENTS.md` CRITICAL: リポジトリ名・`scripts/fetch_news.py`・`docs/` 配下のパスを rename / move しない。`update-news.yml` は触らない。
- `git add -A` 禁止（明示 add）。**commit / push はユーザーの明示承認まで行わない**。`--no-verify` 禁止。
- 環境変数ファイル・secrets 系ファイルを Read しない。`XAI_API_KEY` 未設定でのフル実行は `[SNS SKIP]` になるだけで問題ない。
- ライブサイトへのアクセス: 診断目的の個別取得は 1 サイト数回まで、フル実行は 2 回まで（合計でも 1 サイト 5 リクエスト程度）。
- `docs/index.html` を**手で編集しない**（生成物）。フル実行で再生成する。
- **検証で再生成した `docs/`（`index.html` / `status.json`）は commit 対象にしない**。`XAI_API_KEY` 未設定のローカル生成物は SNS タブが空で、commit すると次の cron まで本番が劣化する。commit 前に `git checkout docs/` で戻す（`status.json` は merge 後の cron が初回生成する）。
- コードコメントは英語。
- スコープ外（P1/P2。やらない・ただし気づいた点は報告に書く）:
  - `BeautifulSoup(resp.content)` 統一・ITmedia charset（WWDJAPAN 診断で必要になった Accept ヘッダ追加は可）
  - WWDJAPAN / FASHIONSNAP / 日経 の抽出器をランキングコンテナ起点に作り直す
  - 並列化、push リトライ、CI への pytest 追加、Dependabot
  - UI コントラスト全般・フォーカス管理・reduced-motion（D4 の新規要素だけは 4.5:1 を守る）

## 4. 検証（報告に出力を貼る）

1. `python -m pytest scripts/tests -q` → all pass（ネットワーク不要で通ること）。
2. **構造 diff の取り方**（committed の `docs/index.html` は 6/5 生成物なので本文が全面入れ替わり、直接 diff は使えない）: `XAI_API_KEY` 未設定で ① `git stash` 等で変更前コードに戻して 1 回生成し `index.before.html` として **repo 外（`$TMPDIR` 等）に退避**（`docs/` に置くと workflow の `git add docs/` が拾う） → ② 変更後コードで 1 回生成 → ①② を diff し、差分が D4 の追加要素＋本文更新だけであることを確認。（これがフル実行 2 回分。ゲート失敗検証は次の 3 で、ネットワークはフル実行 1 回相当）
3. `NEWS_MIN_TOTAL_ITEMS=99999 python scripts/fetch_news.py; echo exit=$?` → `[GATE FAIL]` が出て `exit=1`、`docs/` が書き換わっていない（`git status --short docs/` が②の生成分以外に変化しない／`stat` の mtime 不変）。
4. フル実行（上記②）→ `exit=0`、`docs/status.json` が生成され `python -m json.tool docs/status.json > /dev/null` が通る。`overall_total` の実測値を記録。
5. `docs/status.json` の `sources` から **ランキング 12 ソース（整理後は 10〜11）の before/after 表**を作る（S1 の表と突き合わせ）。期待: HN / Verge / BBC / ITmedia / FASHIONSNAP / Yahoo / PR TIMES / 日経 / GIZMODO が `ok`、TechCrunch は Most Popular が取れれば `ok`、WWDJAPAN は診断次第。
6. `git diff --stat`。
7. ブラウザで `docs/index.html` を開き、(a) 失敗ソースのバッジ表示（デスクトップのサイドバーとモバイルドロワー両方）(b) Rankings ヘッダの失敗ソース名 (c) status.json リンク、を目視。スクリーンショットは任意。

## 5. 返却形式（監督セッションが一次証拠で verify するため）

```
## 変更ファイル
- path — 変更の一言
## 判断の変更・追加
- D1〜D9 から逸脱した点とその理由（なければ「なし」）
## ランキング before/after
| サイト | before (S1) | after status | after count | 1 位の URL（本番 UA で取得した時刻） |
## 診断記録
- WWDJAPAN: status code / body bytes / articles リンク有無 / 結論
- TechCrunch: Most Popular がサーバ HTML にあるか / 結論
- 日経: /access/ 先頭 5 件の正体
## ユーザー判断が必要な事項
- JDN のランキング除外、WWDJAPAN / TechCrunch の扱い、MIN_TOTAL_ITEMS=20 の妥当性 等
## テスト・検証出力
（4. の 1〜6 をそのまま）
## 未解決・気づいた P1/P2 事項
```

## 6. 参考: 現行コードの該当箇所（cb0fad7 時点。0-a の rebase で `docs/` 以外は動かない想定）

- `fetch_ranking()` L461-510、`extract_generic_ranking()` L293-321、`main()` L720-786、`RANKING_EXTRACTORS` L412-425、`build_http_session()` L59-76
- `extract_gizmodo_ranking()` L127-154（正規表現 L149）、`extract_techcrunch_ranking()` L109-124（"Top Headlines" L113）、`extract_jdn_ranking()` L241-269、`extract_wwdjapan_ranking()` L215-225、`extract_nikkei_ranking()` L228-238
- テンプレ: サイドバー ソース一覧 `index.html.j2` L47-53、フッター L55-58、Rankings ヘッダ L163-171、空表示 L196-200。`index.js` L40-46（モバイル複製）。`index.css` L89-93（`.sidebar` 背景）
- `config.py`: `SITES` L1-176（17 件、ranking 12 件、scrape 2 件）、`MAX_ITEMS_PER_SITE` L206、`MAX_RANKING_ITEMS` L207、JDN L100-108

## 7. 運用メモ（Codex の作業対象外）
- ゲート失敗が長期間続くと commit が発生せず、GitHub の「60 日間活動なしで scheduled workflow 自動無効化」に将来抵触しうる。失敗通知を見たら放置しないこと。
- 本変更後、Rankings の表示成功数は一時的に下がる（JDN 除外・WWDJAPAN 次第）。それは劣化ではなく実態の可視化。
