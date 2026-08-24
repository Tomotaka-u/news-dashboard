# P1 Step 2 指示書: ランキング検出力（②）と公開面の衛生（③）（Codex 向け）

作成: 2026-08-22（Claude Fable 監督セッション。Opus 独立レビュー 1 回反映済み: D1 の ITmedia decode、D2 の対応規則、D5 の redaction 形、D6 の 2 段ヘルパ、§4 の期待値、D7 の根拠を修正）
対象リポジトリ: `~/projects/news-dashboard`（開始時点 main = `4cfc87f`）
レーン: **M**（パーサ・ロジック変更と書き込み経路の変更。`status.json` の形・workflow・不変条件は変えない。L hard trigger 非該当）
背景: Obsidian `40_Sessions/2026-08/2026-08-22/2026-08-22-news-dashboard-P0ライブ検証とP1優先順位.md`（S1「P1 優先順位案」バケット②③、S4 = 本指示書の作成経緯）。前段: P0 `39742bf`（`plans/2026-08-21-p0-ranking-reliability.md`）、P1 Step 1 `0107152`（`plans/2026-08-22-p1-step1-ship.md`）

---

## 0. 前提条件と開始前チェック

### 0-a. **Step 1 と違う点（最初に読む）**
- Step 1 の指示書は「Claude が実装・検証済みのものを Codex が merge まで出荷」だった。**今回は実装が Codex なので、merge は Codex の仕事ではない**。手順は「実装 → テスト → push → PR → CI green → **停止して §5 の形式で報告**」で終わる。merge は監督が pytest を自分で回し diff を読んだ後に別途指示する。
- 分担 memory 上 `.gitignore` と `CURRENT_STATE.md` は Claude 担当だが、P0 D9 の前例に沿って**本指示書の範囲（D6 の 1 行追加、D9 の記述更新）に限って Codex に委譲**する。それ以外の Claude 担当ファイル（`.github/**`）には触らない。

### 0-b. Codex が最初に行うチェック
1. `git switch main && git pull --rebase && git status --short` → 空であること（**本指示書 `plans/2026-08-22-p1-detection-hygiene.md` の未追跡のみ許容**。次の 2. で commit する）。それ以外がダーティなら止まって報告。`git log --oneline -1` が `4cfc87f` 以降（cron commit が積まれていてよい）。
2. 作業ブランチを切る: `git switch -c feat/p1-detection-hygiene`。最初の commit は本指示書だけ: `git add plans/2026-08-22-p1-detection-hygiene.md && git commit -m "docs: P1 Step2（検出力・公開面衛生）指示書を追加"`。
3. `python --version` が 3.12 系（CI と同じ）。`pip install -r scripts/requirements-dev.txt` が通る。
4. `python -m pytest scripts/tests -q` → **12 passed** を baseline として記録。
5. ライブサイト（gizmodo.jp / fashionsnap.com / nikkei.com / itmedia.co.jp）に本番 UA `NewsDashboard/1.0 (+https://github.com/Tomotaka-u/news-dashboard)` で HTTP 取得できること。**できない環境なら D2〜D4 は推測で書かず `[検証不能]` として止まり、D1 / D5〜D9 だけ進めて報告**する。

## 1. 目的（何を達成するか）

P0 で「取れていないものを取れていないと言う」状態にはなった。P1 Step 2 はその上で (a) **取れていると言っているものが本当に人気ランキングか**を構造で保証し、(b) **公開面（`status.json` / `title=`）と書き込み経路の衛生**を整える。

| # | 問題 | 場所（`4cfc87f` 時点の行） |
|---|---|---|
| ② -1 | GIZMODO は `rankingContainer` 内の**先頭** `rankingList` を Daily と仮定している。タブ順が変わる・Amazon タブが先頭に来る等で「別の並び」を `ok` として出す | `scripts/fetch_news.py` L156-197（コメント L182 が仮定を明記） |
| ② -2 | FASHIONSNAP は `/ranking/` ページ**全体**の `/article/YYYY-` リンク先頭 5 件。ランキング以外のリンク（ヘッダのピックアップ等）が先に並べばそれを `ok` として出す | L245-255 |
| ② -3 | 日経は `.m-miM32` 起点（P0 で修正済み）だが順位番号を見ていない | L258-271 |
| ② -4 | `BeautifulSoup(resp.text)`（requests の推定エンコーディング）と ITmedia だけ `shift_jis` 手動 decode（cp932 固有文字 ① 等が `�` になる）。`Accept` / `Accept-Language` を送っていない | L419, L444-455, L84-100 |
| ③ -1 | `detail` に `str(exc)` を 200 字で切っただけのものを載せている。requests / urllib3 の例外文字列は**リクエスト URL のパスとクエリ**を含むので、認証付きソース（`?token=`）を足した瞬間に `status.json`（全ソース）とサイドバーの `title=` 属性（feed/scrape 行）へトークンが公開される | L53, L111, L416, L449、`index.html.j2` L54 |
| ③ -2 | `index.html` / `status.json` を `open(..., "w")` で直接上書き。片方を書いた後に落ちると **index だけ新しく status が古い** 状態が `docs/` に残る（本番 cron では step が非 0 で終わり commit されないが、ローカル実行・部分書き込みの衛生として直す） | L789, L812 |
| ③ -3 | `feeds.total_sources = len(SITES)`。`sources` 行から導出していないため、2 つの数が別々の経路で計算されている | L800 |
| ② -5 | テスト穴: `test_gate.py` が `NEWS_MIN_TOTAL_ITEMS` を `delenv` していない（環境に残っていると 20 件境界テストが嘘をつく）。`feeds{}` の値アサートがない | `scripts/tests/test_gate.py` L25-31、`test_status_json.py` L51 |

**成功の定義**: 専用パーサが `ok` を返すのは「そのサイトがランキングだと表示している並び」から取れたときだけ。`status.json` / HTML に URL・パス・クエリ・生の例外文が出ない。`docs/` に半端なファイルが残らない。**表示上の成功数は下がってよい**（§4 参照。`ok` を増やすためにアンカー条件を緩めることは禁止）。

## 2. 設計判断（確定済み。変えたい場合は理由を添えて報告し、勝手に変えない）

### D0. D2〜D4 に共通する規則（先に読む）
- **実装時に一度だけ判断し、決めた側の条件だけをコードにハードコードする**。「順位番号があれば厳格、無ければ緩い」のような**実行時の分岐は書いてはならない**（P0 D1 で廃止したサイレントフォールバックの再発になる）。順位番号を成功条件に入れると決めたら、将来それが消えたときは 0 件（`empty`）になるのが正しい挙動。
- **順位番号の判定規則**: 要素テキストを `sanitize_text` した後 `re.fullmatch(r"0?(\d{1,3})(位|\.)?", text)` に一致するものだけを順位番号とみなし、group(1) を int にする。画像だけの順位表示は順位番号なしとして扱う。成功条件は「1〜5 がこの順で現れ、各順位に記事リンクが 1 本対応する」。
- **タブ ↔ パネルの対応**は次の優先順で取る。(a) サーバ HTML に明示の関連付け（`aria-controls` / `id` / `data-*`）があればそれ。(b) なければ「目的のラベル（Daily / WEEKLY 等）を持つタブ要素の index を求め、同じ index のパネルを採る。該当ラベルのタブが無い、またはタブ数 ≠ パネル数なら 0 件」。「先頭パネルを採ってラベルを確認する」方式は**採らない**。どちらで取ったかを報告に書く。
- **初期選択タブ**（どの期間を出すか）は**サーバ HTML の証拠**（`aria-selected` / `checked` / active 系 class 等）で判定する。証拠が無ければ決め打ちせず `[ユーザー判断事項]` として報告し、その D を止める（現状コードは残す）。
- WebFetch 経由の参考観測はクラス名・属性が落ちているので、DOM 構造の確定は**必ず本番 UA で取得した HTML**から行い、fixture はその HTML から切り出す（≤50KB、該当モジュール周辺のみ）。

### D1. HTTP 取得の共通化（Accept ヘッダ・`resp.content`・ITmedia decode）
- `build_http_session()` で `session.headers.update({"User-Agent": USER_AGENT, "Accept-Language": "ja,en;q=0.8"})`。各 `session.get(..., headers={"User-Agent": USER_AGENT})` は `Accept` だけを渡す形に置き換える（UA は session 既定から乗る）。定数:
  ```python
  HTML_ACCEPT = "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8"
  FEED_ACCEPT = "application/rss+xml,application/atom+xml,application/rdf+xml,application/xml;q=0.9,text/xml;q=0.9,*/*;q=0.8"
  ```
  `fetch_feed` は `FEED_ACCEPT`、`fetch_scrape_news` / `fetch_ranking` は `HTML_ACCEPT`。注意: session 既定ヘッダは同じ session を使う `fetch_sns_posts`（xAI API）にも乗る（UA が `python-requests/…` から本番 UA に、`Accept-Language` が付く）。これは意図した変更で、`fetch_sns_posts` のコード自体は変更しない。
- `BeautifulSoup(resp.text, ...)` を **`BeautifulSoup(resp.content, "html.parser")`** に統一（bs4 が meta charset / BOM から判定する）。**例外は ITmedia**: 手動 decode を残し `resp.content.decode("cp932", errors="replace")` に変更する（`shift_jis` → `cp932` で NEC 特殊文字 ①② 等を救う。`from_encoding=` は使わない — bs4 の候補カスケードは不透明で、監督の再現でも `shift_jis` 指定が黙って `shift_jis_2004` に落ちた）。
- 検証: before/after のフル実行で **12 HTML ソース（ランキング 10＋scrape 2）のタイトル文字列が一致**すること（ITmedia は ① 等が含まれる場合のみ差分可。波ダッシュ `〜`→`～` の差も cp932 由来として受容）。不一致があれば一覧を報告。
- テスト（`test_http_headers.py` 新規、3 本）: ①`build_http_session().headers["User-Agent"] == USER_AGENT` かつ `Accept-Language` が設定されている ②`fetch_feed` が `FakeSession.get` に `headers={"Accept": FEED_ACCEPT}` を渡す ③`fetch_ranking` が `headers={"Accept": HTML_ACCEPT}` を渡す（`FakeSession.get` が受け取った `headers` を記録する）。

### D2. GIZMODO: 「先頭パネル = Daily」の仮定をやめ、Daily タブと順位番号で確定する
- ライブ（2026-08-22、参考観測）: 見出し「Ranking」、タブは **Daily | Weekly | Monthly | Amazon**、各 5 件、順位番号 1〜5 が表示されている。
- 成功条件（両方、D0 の規則で）: ①採るパネルが **Daily ラベルのタブに対応**している ②パネル内に順位番号 1〜5 がこの順で存在し、各順位に記事リンク（既存の `/article/` or `/YYYY/MM/` 判定、`/tag/` `/issue/` `/author/` 除外は維持）が対応する。
- 順位番号がサーバ HTML に無い（JS 描画）と**実装時に判明**した場合は、条件 ① だけをハードコードし、その旨と根拠（取得 HTML の該当箇所）を報告する（D0: 実行時分岐は書かない）。
- タブとパネルの対応がサーバ HTML から確立できないなら `[ユーザー判断事項]` として報告して D2 を止める。
- fixture: 既存 `scripts/tests/fixtures/gizmodo-ranking.html` は新アンカーを含まないので、本番 UA のライブ HTML から**作り直す**（≤50KB）。正例 1 本（weekly デコイを含む）＋負例 2 本: (i) タブが `Weekly | Daily | Monthly`（Daily が 2 番目）で **2 番目のパネル**が返る（「先頭を採る」実装を弾く）、(ii) `Daily` ラベルのタブが無く 0 件。`test_extractors.py` に 3 本。
- `CURRENT_STATE.md` の「先頭 Daily パネル」記述を新条件に合わせる（D9）。

### D3. FASHIONSNAP: ランキングコンテナ起点に限定し、順位番号を成功条件にする
- ライブ（参考観測）: `/ranking/` は見出し「**トップ100**」、**WEEKLY / MONTHLY** タブ、順位番号 1〜100 表示。現行コードは起点なしでページ全体の `/article/YYYY-` 先頭 5 件。
- 成功条件: ランキングリストのコンテナ（見出し「トップ100」または順位番号要素の親）を起点にし、**順位番号 1〜5 を持つ項目**をその順で 5 件。WEEKLY / MONTHLY が両方サーバ HTML にある場合は、**初期選択タブを D0 の規則（サーバ HTML の証拠）で決める**。証拠が無ければ `[ユーザー判断事項]`（WEEKLY と決め打ちしない）。コンテナが見つからなければ 0 件（= `empty`）。
- 同じライブ HTML に対して**現行コードの結果と新コードの結果を並べて報告**（一致すれば「今まで偶然正しかった」、不一致なら「今まで嘘だった」の証拠になる）。
- fixture: ライブ HTML から正例 1 本（≤50KB）、負例 1 本（記事リンクはあるがランキングコンテナが無い）。

### D4. 日経: `.m-miM32` 起点は維持、順位番号がサーバ HTML にあれば成功条件に加える
- ライブ（参考観測）: 見出し「アクセスランキング」、順位 1〜10 表示、タブは「今日」＋日付。
- 本番 UA の HTML で `.m-miM32` 内に順位番号要素があれば、「順位番号 1〜5 を持つ項目をその順で」を成功条件に**ハードコード**する（fixture 1 本）。無ければ現状維持で**その旨を報告**（D0: 実行時分岐は書かない）。「今日」タブがサーバ HTML で初期選択かを D0 の規則で確認して報告（違えば `[ユーザー判断事項]`）。

### D5. `detail` の衛生: URL・パス・クエリ・生の例外文を公開面に出さない
- 新ヘルパ `summarize_error(exc, url)`（英語 docstring）を `fetch_feed` / `fetch_scrape_news` / `fetch_ranking` の `http_error` / `parse_error` の `detail` に使う。規則:
  - `requests.exceptions.HTTPError` で `exc.response is not None` → `f"HTTP {status_code} {reason}"`（例 `HTTP 403 Forbidden`）
  - その他の `RequestException` → `f"{type(exc).__name__} ({host})"`。`host` は `urlparse(url).hostname`（**`netloc` ではなく `hostname`**: userinfo を落とす）。**`str(exc)` を使わない**（urllib3 の文言はパスとクエリを含む）
  - それ以外の例外（parse_error）→ `f"{type(exc).__name__}: {message}"`。`message` は `str(exc)` に下記 redaction を適用し 160 字で切る
- `build_fetch_result()` の `detail` 正規化に**安全網として redaction を常に適用**（bozo detail など全経路をカバー）。redaction は 3 パターンを `<url>` に置換: ①`https?://\S+` ②`url: /\S*`（urllib3 形式 `Max retries exceeded with url: /feed?token=…`）③`\?\S+`（残存クエリ）。既存の 200 字上限・`sanitize_text` は維持。
- テスト（`scripts/tests/test_detail_sanitization.py` 新規）: ①`summarize_error(ConnectionError("…with url: /feed?token=SECRET123"), "https://user:pw@example.com/feed?token=SECRET123")` → `detail` に `SECRET123` / `token` / `/feed` / `user` / `pw` が**含まれない**、`example.com` と `ConnectionError` は含まれる ②`HTTPError` + status 403 → `HTTP 403 Forbidden` ③parse_error のメッセージ内 `https://…` が `<url>` になる ④**実物の形**で安全網を直接: `build_fetch_result(status="http_error", detail="HTTPSConnectionPool(host='example.com', port=443): Max retries exceeded with url: /feed?token=SECRET123 (Caused by X)")` → `SECRET123` と `token` が消え `example.com` が残る。
- 既存テスト `test_status_json.py` の `'title="feed is empty"'` は影響を受けない（URL を含まない）。

### D6. `docs/` への書き込みを原子的にする（2 段ヘルパ）
- 動機（正直に）: 本番 cron では途中で落ちれば step が非 0 で commit されないので「壊れたファイルが commit される」経路は無い。直すのは (a) ローカル実行で半端なファイルが `docs/` に残ること (b) index を書いた後に status の構築・書き込みで落ちると **index だけ新しい**不整合が残ること。最小の代替（status 文字列を index 書き込みより前に確定するだけ）でも (b) の大半は閉じるが、tmp + `os.replace` は追加 15 行程度で (a) も閉じ標準的なので採る。
- ヘルパ 2 本（英語 docstring）:
  - `_write_tmp(path, text) -> tmp_path`: `path + ".tmp"` を同じディレクトリに `encoding="utf-8"` で書き、`file_obj.flush()` → `os.fsync(file_obj.fileno())`。戻り値は tmp パス
  - `_replace_all(pairs)`: `[(tmp_path, final_path), …]` を順に `os.replace`
- `run()` の手順: ①`html` 文字列と `status_text` を**両方先に確定**（`status_text = json.dumps(status_payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n"` — **P0 D4 の出力契約。引数を 1 つも落とさない**）→ ②`_write_tmp` を index → status の順に 2 回（どちらかが失敗したら**両方の tmp を unlink して再送出**、既存ファイルには触れない）→ ③`_replace_all([(index_tmp, index_path), (status_tmp, status_path)])`。2 本目の `os.replace` だけが失敗して index だけ新しくなる窓は受容するリスク。
- `.gitignore` に 1 行 `docs/*.tmp` を追加（ローカルで tmp が残っても `git add docs/` が拾わない保険。`git add docs/` との組み合わせで ignore が効くことは確認済み）。
- テスト（`test_atomic_write.py` 新規）: ①正常系: `tmp_path` に `index.html` と `status.json` **だけ**が残る（`*.tmp` なし）、`status.json` の生テキストが `"\n"` で終わり、`json.loads` 後のキー順が `sorted()` と一致する ②異常系: **2 本目（status）の `_write_tmp` 呼び出し**で例外を注入（`monkeypatch` で `fetch_news._write_tmp` を「1 回目は素通し、2 回目で raise」のラッパに差し替える。`json.dumps` の monkeypatch は禁止 — テスト自身の json 使用も壊れる）→ 事前に置いた `index.html` / `status.json` の内容が**変わらない**、`*.tmp` が残らない、例外が伝播する。

### D7. `feeds.total_sources` を `sources` 行から導出する
- `len(SITES)` → `sum(1 for row in source_status if row["kind"] != "ranking")`。**現行では常に同値**（`run()` は全 `SITES` に feed/scrape 行を積む）で挙動は変わらない。目的は「分母と `ok_sources` を同じ `source_status` から導出し、構造上ずれないようにする」だけ。ranking-only サイトは現状サポート外（`site["url"]` で KeyError）で、今回はサポートしない。
- テスト: `test_status_json.py` の既存 `test_status_schema_order_and_feed_status_not_overwritten` に `written["feeds"] == {"total_sources": 2, "ok_sources": 1}` と `written["rankings"] == {"total_sources": 1, "ok_sources": 1}` を追加。

### D8. テスト穴を塞ぐ
- `test_gate.py` の `configure()` に `monkeypatch.delenv("NEWS_MIN_TOTAL_ITEMS", raising=False)` を追加（既存 4 本すべてに効く）。
- 失敗バッジのテンプレテストは **`test_status_json.py` に既存**（`取得失敗` と `title="feed is empty"` のアサート）。重複実装しない。追加は負例 1 行だけ: 同テストで `html.count("取得失敗") == 1`（healthy 側にバッジが出ない。テンプレ内の `取得失敗` は `index.html.j2` L54 の 1 箇所のみ）。
- D1 / D5 / D6 / D7 / D2〜D4 のテストは各項を参照。全体で **12 → 25 本前後**になる想定（数は目安、質優先）。

### D9. ドキュメント（`CURRENT_STATE.md`、Codex に委譲）
- 「ランキング対応サイト」節の GIZMODO / FASHIONSNAP / 日経 の抽出条件を D2〜D4 の結果に合わせて更新。「稼働状況」表を今回のフル実行日付で更新。
- 「環境変数」の下あたりに短い節「`status.json` / 画面の `detail` 方針」: URL・パス・クエリ・生の例外文は載せない（`summarize_error` ＋ redaction）。「GitHub Actions」節の直後に「`docs/` は tmp + `os.replace` で原子的に書く、`docs/*.tmp` は ignore」を 1〜2 行。
- `.github/**` と `plans/2026-08-21-*.md` / `plans/2026-08-22-p1-step1-ship.md` は触らない。

## 3. 制約・禁止事項

- **監督の指示前に merge しない**（0-a）。PR は CI green まで見届けて停止。
- **`ok` 件数を増やすためにアンカー条件（D0〜D4）を緩めない**。条件を満たさなければ `empty` が正しい結果。
- `AGENTS.md` CRITICAL: リポジトリ名・`scripts/fetch_news.py`・`docs/` 配下のパスを rename / move しない。`.github/workflows/*` を触らない。
- `git add -A` 禁止（明示 add）。`--no-verify` 禁止。force push 禁止。main への直接 commit は hook で拒否される（ブランチで作業）。
- 環境変数ファイル・secrets 系ファイルを Read しない。`XAI_API_KEY` 未設定のフル実行は `[SNS SKIP]` になるだけで問題ない。
- ライブサイトへのアクセス: 診断目的の個別取得は 1 サイト 5 リクエスト程度まで、フル実行は 2 回まで（before / after）。
- `docs/index.html` / `docs/status.json` を手で編集しない。**検証で再生成した `docs/` は commit しない**（`XAI_API_KEY` 未設定の生成物は SNS タブが空）。commit 前に `git checkout docs/` で戻し、`git status --short docs/` が空であることを報告に貼る。
- fixture は 1 ファイル 50KB 以下、該当モジュール周辺だけ切り出す。個人情報・トラッキングパラメータが載っていたら削る。
- `status.json` の**キー構造・`status` の語彙（ok / empty / http_error / parse_error / skipped）・`sources` の並び・シリアライズ形式（D6）**は変えない（P0 D2/D4 の契約）。
- コードコメント・docstring は英語。commit メッセージは日本語 Conventional Commits。
- スコープ外（気づいた点は報告に書くが、やらない）: 並列化、UI コントラスト・フォーカス管理、WWDJAPAN / JDN の再挑戦、TechCrunch の再診断、Dependabot PR の操作、`ci.yml` への変更、ranking-only サイトのサポート。

## 4. 検証（報告に出力を貼る）

1. `python -m pytest scripts/tests -q` → all pass（ネットワーク不要で通ること。本数を書く）。`python -m compileall -q scripts` → 無出力。
2. **before**: 変更前コード（`git stash` または `main` を別 worktree に checkout）で `XAI_API_KEY` 未設定のフル実行 1 回 → `docs/index.html` と `docs/status.json` を **repo 外**（`$TMPDIR` 等）に `index.before.html` / `status.before.json` として退避。
3. **after**: 変更後コードでフル実行 1 回 → `exit=0`、`python -m json.tool docs/status.json > /dev/null` が通る。`overall_total` を記録。
4. `status.before.json` と `docs/status.json` の `sources` から **ランキング 10 ソース＋scrape 2 ソースの before/after 表**（status / count / 1 位 URL）。**期待値は置かない**。GIZMODO / FASHIONSNAP / 日経 が `empty` になった場合も**それ自体は失敗ではない** — どのアンカー（タブ関連付け / 順位番号 / コンテナ）が無かったかを根拠付きで報告する。1 位 URL が before と after で不一致なら両方の URL を書く（D2/D3 が「嘘」を直した証拠）。
5. `index.before.html` と `docs/index.html` の diff から、12 HTML ソースのランキング／scrape タイトル文字列が一致すること（D1。ITmedia の cp932 由来差分は列挙して受容）。`detail` の露出が変わる箇所（失敗ソースが無ければ差分なしでよい）。
6. `ls docs/` に `*.tmp` が無いこと。`git checkout docs/ && git status --short` が空。
7. `git diff --stat main...feat/p1-detection-hygiene`。
8. push → `gh pr create --base main --head feat/p1-detection-hygiene --title "feat: ランキング検出条件の厳格化と status.json/書き込みの衛生（P1 Step2）"`（本文は §5 の要約）→ `gh pr checks --watch` で CI green を確認 → **停止**。

## 5. 返却形式（監督が一次証拠で verify するため）

```
## 変更ファイル
- path — 変更の一言
## 判断の変更・追加
- D0〜D9 から逸脱した点とその理由（なければ「なし」）
## D2〜D4 の構造確定メモ
- GIZMODO: タブ↔パネルの対応の取り方（(a)/(b)）/ 順位番号要素の有無とクラス・判定式 / 初期選択の証拠 / fixture の出所と日時
- FASHIONSNAP: コンテナの起点 / 初期選択タブの証拠 / 現行コード vs 新コードの 5 件比較
- 日経: 順位番号要素の有無 / 「今日」タブ初期選択の証拠 / 変更有無
## ランキング before/after（4.）
| サイト | before status/count | after status/count | 1 位 URL before | 1 位 URL after |
## ユーザー判断が必要な事項
- D2/D3/D4 で [ユーザー判断事項] になったもの、あれば
## テスト・検証出力
（4. の 1〜7 をそのまま。pytest 本数、compileall、overall_total、json.tool、タイトル一致確認、ls docs/、git status、diff --stat）
## PR URL / CI run ID / 結論
## 未解決・気づいた事項（修正はしない）
```

## 6. 参考: 現行コードの該当箇所（`4cfc87f` 時点）

- `build_http_session()` L84-100、`fetch_feed()` L103-135（`headers=` L108）、`fetch_scrape_news()` L397-427（`headers=` L411、`resp.text` L419）、`fetch_ranking()` L430-464（`headers=` L444、shift_jis L453、`resp.text` L455）、`fetch_all_sns()` L603（同一 session を共有）
- `build_fetch_result()` L42-54（`detail` 正規化 L53）、`sanitize_text()` L57-59
- `extract_gizmodo_ranking()` L156-197（先頭パネル仮定のコメント L182）、`extract_fashionsnap_ranking()` L245-255、`extract_nikkei_ranking()` L258-271、`RANKING_EXTRACTORS` L383-394
- `run()` L674-822: `index.html` 書き込み L786-790、`feeds.total_sources` L800、`status.json` 書き込み L811-814（`json.dump(..., ensure_ascii=False, indent=2, sort_keys=True)` ＋ `"\n"`）
- テスト: `test_gate.py` `configure()` L25-31、`test_status_json.py` L50（`written == returned`）・L51（キー集合）・L57-59（バッジ）、`test_fetch_ranking.py` L6-18（`FakeResponse` / `FakeSession`）、fixtures `scripts/tests/fixtures/`（gizmodo-ranking.html 1.7KB、techcrunch-most-popular.html 1.3KB）
- `config.py`: GIZMODO L24-31、FASHIONSNAP L72-79、日経 L108-115
- テンプレ: バッジ `index.html.j2` L52-55（`title="{{ feed_status.detail }}"`、feed/scrape 行のみ。ランキング行の `detail` はレンダリングされない）、`.source-status-failed` `index.css` L200-206

## 7. 運用メモ（Codex の作業対象外）

- merge 後の初回 cron で GIZMODO / FASHIONSNAP が `empty` になった場合、それは「今まで偶然取れていた」可能性を含む。`status.json` の `detail` と Actions ログの `[RANKING FAIL]` を見て、パーサの条件が厳しすぎるのか構造が変わったのかを切り分ける。
- D5 の後も `detail` はホスト名と HTTP ステータスを出す。認証付きソースを足すときは `detail` にホスト名が出てよいかを改めて判断する。
