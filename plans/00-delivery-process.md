# 出荷プロセス v2（1 往復）— Claude 監督 × Codex 実装

作成: 2026-08-26（P3 完了後）。正本はこのファイル。指示書（`plans/YYYY-MM-DD-*.md`）はこのプロセスを前提に書く。
変えたいときはこのファイルを直し、変更点を Obsidian のセッションノートに残す。

## 0. なぜ v2 か（と、何を諦めたか）

- v1（P1 Step 2 〜 P3）は 1 フェーズ 5 ステップ・**2 往復**: ①Claude 指示書 → ②Codex 実装・PR で停止 → ③Claude が PR head を verify して reviewed SHA 付き GO → ④Codex merge・dispatch → ⑤Claude 出荷 verify
- ③の事前 GO ゲートは P2 で導入した。P1 Step 2 〜 P3 の 3 回で差し戻し 0 回。③で見つかった指摘は 2 件（P1 S6: `"active" in class_name` が `inactive` にも一致 / P2 S4: 位置結合など残存リスク 5 件）だが、**どちらも「merge して follow-up」と判定され出荷を止めていない**。一方 ③と⑤は別セッションで、毎回コンテキスト再構築とユーザーの伝達コストがかかっていた
- v2 は **③を廃止**して ②と④を Codex の 1 セッションに畳む: ①指示書 → ②Codex 実装 → PR → CI → merge → dispatch → 証拠バンドル返却 → ③Claude 出荷 verify（1 回）。**1 フェーズ 1 往復**
- **諦めるもの**: 意味的レビュー（Opus lens）による catch は本番投入後に移る。受容できる根拠は (a) 過去の該当 2 件は v1 でも出荷を止めなかった (b) squash merge 1 commit なので revert が単純、cron は `docs/` しか触らない (c) `status.json` gate が空ページを止める (d) 影響は最大 1 cron 周期（12 時間）の誤データ。**revert で戻せないもの（§3-A）だけは事前 GO を残す**
- 安全網: (1) Codex の停止条件（§4）が本番前の唯一のゲート (2) Codex 側の独立レビューを merge 前に必須化、レビュー対象 SHA を固定（§2） (3) Claude の出荷後 verify は契約・安全性・定量主張を**全件**確認（§6） (4) revert runbook（§7）

## 1. 役割と環境制約（不変）

| | Claude（Fable 監督） | Codex |
|---|---|---|
| できること | 設計・指示書、diff 全読、pytest 自走（certifi スタブ）、GitHub API / Pages を WebFetch で読む、Obsidian / memory | ライブサイト取得（本番 UA）、Python 実行、`gh`（PR / checks / merge / run / ログ）、push、workflow dispatch |
| できないこと | 外部ネットワーク、`gh`、`git fetch` / push、Actions ログ本文（403） | Obsidian vault の閲覧（ノート追記はファイルパス指定で可） |
| 所有ファイル | `.github/**`、`plans/**`、`AGENTS.md` / `CLAUDE.md`、Obsidian | `scripts/**`、`templates/**`、`requirements*.txt`、`CURRENT_STATE.md`（指示書で scope grant） |

- `docs/**` は GitHub Actions だけが書く。人も Codex も編集しない。**public repo なので `docs/` の内容は git 履歴と Pages に永久に残る**（revert しても消えない）
- Claude 所有ファイルも push は Codex（か ユーザー）が行う。指示書 §0 で「最初の commit に含めるファイル」として明示する
- main は branch protection 無し（2026-08-26 時点、cron の bot push を通すため）。**CI green は `gh pr checks` で Codex が確認する以外に強制されない**
- `update-news.yml` は `concurrency: cancel-in-progress: true` + push 失敗時に `git pull --rebase` して再 push。**cron と merge / dispatch が重なると、旧コードの生成物が新 main を親に持つ**。§2 の禁止時間帯を守る

## 2. フロー

```
S1 Claude : 指示書を書く（§8 テンプレ）。§3-A 該当の有無を §0 に明記する
S2 Codex  : §0 開始チェック → fixture 先行（実装前 FAILED を記録）→ 実装 → §4 検証
            → 独立レビュー（Sol/high。reviewed SHA を記録。指摘を直したら同 SHA でなくなるので再レビュー）
            → 停止条件（§4）を項目別に Yes/No 判定 → push → PR → `gh pr checks <n> --watch` 全 pass
            → squash merge → dispatch 1 回 → 生成物検証 → 証拠バンドル（§5）→ Obsidian ノートに S<n> 追記
S3 Claude : ユーザーが `git pull --rebase` した後に開始（`git log -1` を報告に貼る）
            → 出荷 verify（§6）→ GREEN: ノート done / RED: revert 指示（§7）
```

- **merge / dispatch / revert の禁止時間帯: JST 5:30〜6:30、17:30〜18:30**（cron の前後。§1 の競合を避ける）。`gh run list --workflow=update-news.yml --limit 1` で in-progress が無いことも確認する
- 独立レビューは **merge する head SHA と同じ SHA** に対して行う。指摘 → 修正 commit → 再レビュー、を P0 / P1 ゼロになるまで繰り返す。報告には「Sol reviewed SHA」と「merged head SHA」を並べる
- 停止条件に当たったら S2 は **merge せず**に §5 の形式で報告して止まる（v1 の②相当。P2 S2 と同じ経路）。往復には数えない例外経路で、監督が判断してから再開する
- Dependabot PR は指示書で明示された場合だけ扱う（手順は P1 出荷指示書 §4）。書かれていなければ触らない

## 3. 事前 GO ゲートの要否

**該当するかは監督が指示書 §0 に書く。Codex は自分で判定しない（迷ったら停止）。**

### 3-A. 事前 GO を残す（revert で取り消せない変更）

v1 手順（PR で停止 → Claude が head SHA を verify → GO → merge）を取る。

1. `.github/workflows/**` の変更（本番 cron の挙動そのもの。壊れると 60 日無 commit で scheduled が自動無効化）
2. **動的文字列**（HTTP 応答本文・ヘッダ・例外文・URL・パス・クエリ）を **Actions ログまたは公開面（`status.json` / `index.html`）に出す**変更全般。repo は public: ログは誰でも読め、`docs/` は履歴に永久に残る。キーやトークンが 1 行でも出たらキー失効が必要になる。「`redact_detail` を通すから」「テストがあるから」では免除しない（テストは実装者が書いた経路しか固定しない。P3 の `[SNS ERROR] ... {exc}` のように別経路から出る）
3. 秘密の読み方・送り先を変えるコード（`XAI_API_KEY` の扱い等）
4. 外部サイトへのリクエストの回数・頻度・並列度・UA・エンドポイントを変える変更（block されたら revert しても戻らない）

### 3-B. 事前 GO 不要だが、出荷直後に即時確認する（可逆だが本番停止を伴う）

v2 で出す。Codex が dispatch 後に §5「本番生成物」で確認し、Claude が §6 で再確認する。

1. `status.json` のキー / 語彙 / `sources` 行の変更（毎 run 再生成されるので revert + dispatch で数分で戻る。行の追加は特に注意不要）
2. テンプレ（`templates/**`）の変更（表示崩れは次 run で戻る）
3. 品質ゲート（`MIN_TOTAL_ITEMS` 等）の変更

## 4. Codex の停止条件（merge しない・報告して停止）

報告（§5）には **この 10 項目それぞれに Yes / No と根拠 1 行**を書く。

1. §0 開始チェックの不一致（dirty / untracked が指示書の whitelist 外、baseline テスト件数の不一致、前回出荷以降に `scripts/` が変わっている、`git stash list` に指示書が知らない stash）
2. ライブ before/after の不一致（サイト側の順位入替は取得時刻つきで再取得 1 回まで。**両回の生出力を貼る**。それでも不一致なら停止）
3. 指示書の D 判断を変える必要がある（D0 手続き: 理由を添えて報告、勝手に変えない。P2 S2 で FASHIONSNAP の DOM 不一致を止めたのがこの経路）
4. diff が指示書の「変更ファイル」一覧の外に出る
5. `.github/**` / `docs/**` に触れた（指示書で明示 grant された場合を除く）
6. 独立レビューに P0 / P1 指摘が残る、または reviewed SHA ≠ merge する head SHA
7. `gh pr checks` に pass 以外がある、または直近 3 run の `update-news.yml` に failure / in-progress がある
8. 検証項目に `[検証不能]` がある（ライブ取得不可など。監督が代行するので停止）
9. 指示書 §0 に「事前 GO 必須（§3-A）」と書かれている
10. `git add -A` / `--no-verify` / force push が必要になった、または禁止時間帯にかかった（＝何かが間違っている）

## 5. 証拠バンドル（返却形式）と定量主張のルール

Claude は Codex の主張を一次証拠で再確認する。そのために報告は次の規則で書く。

- **件数・行数・回数**の主張は、生成したコマンドと生出力をそのまま貼る。要約した数字だけは不可（P2 で fail-closed 分岐「12」→ 実際は 27 の過小報告があった）。行範囲を切る grep は、範囲の根拠（関数の開始行・終了行と `def` 行）も貼る
- **「いつから」**の主張は履歴を遡って onset を特定する。「直近 N run」で止めない（P2 で「直近 4 run」と報告された SNS 全滅は、履歴を遡ると 2026-03-04 から 5 か月続いていた）。手段: `git log --format='%h %ci' -- docs/index.html` を最古まで走査して該当 commit を二分探索、`gh run list --workflow=... --limit 200`
- **「一致」**の主張は両側の値を並べる（before/after は 5 件 × サイト、PR head SHA と squash SHA、Sol reviewed SHA と head SHA、報告テスト件数と実出力）
- **Actions ログ本文**の件数（Claude は sandbox から読めない）は `gh run view <id> --log | grep -c '<pattern>'` のコマンドと出力を貼る。Claude は「Codex 報告」印をつけて `status.json` と突合する
- **未確認は未確認と書く**。「問題なし」と「見ていない」を混ぜない
- 判断の変更・追加は「指示書どおり」でも 1 行ずつ明記する

```
## 開始状態（git status --short / git stash list / baseline テスト件数 / git log -1）
## 変更ファイル（git diff --stat <base> <merge SHA> -- . ':!docs'）
## 判断の変更・追加（D0 手続きを踏んだもの）
## テスト・検証出力（baseline → after、負例の実装前 FAILED、compileall、完了 grep はコマンド＋範囲根拠＋生出力）
## ライブ before/after（該当サイト × 5 件、取得時刻つき。再取得したら両回。同一 HTML での比較も）
## 独立レビュー（Sol reviewed SHA、指摘と処置、再レビュー回数、最終 P0/P1 ゼロ）
## 停止条件の判定（§4 の 10 項目それぞれ Yes/No + 根拠 1 行）
## 出荷（PR URL / head SHA / gh pr checks 出力 / squash SHA / main CI run ID / dispatch run ID と開始時刻 / update job 所要時間）
## run ログ件数（grep コマンド＋出力: FEED FAIL / RANKING FAIL / RANKING FAIL DETAIL / SNS ERROR / Node.js / deprecated）
## 本番生成物（生成 commit SHA と author date、status.json の generated_at / gate / feeds / rankings / 非 ok 行全部、キー集合）
## 最終 git 状態（git log --oneline -3 main / git branch -a / git status --short / git stash list）
## 未解決・気づいた事項（修正はしない。onset を特定した「いつから」もここ）
## 監督構成（レーン / 委譲 / 昇格 / 未確認）
## Obsidian（追記したノートのパスと見出し）
```

Obsidian: 指示書に書かれたノートの末尾に `## S<n> | 日付 | 一言` で追記する。新規ノートは作らない。

## 6. Claude の出荷 verify（全件、1 セッション）

事前 GO を廃止した分、ここで **契約・安全性・定量主張を全件**確認する。開始条件: ユーザーが `git pull --rebase` 済みで、ローカル `main` に squash commit と生成 commit がある（無ければ WebFetch で代用せず、ユーザーに pull を依頼する）。

独立 review lens 1〜2（Opus devils-advocate = diff の意味的監査: 文字列の部分一致・位置結合・属性消失時の fail-open・例外経路の状態 / Sonnet = 機械監査: pytest・grep・API）を並列に出し、親は最重要主張を 1 件以上、契約・安全性の主張は全件、自分で再実行する。advisor は委譲前と完了宣言前の 2 回。

| # | 確認 | 一次証拠 |
|---|---|---|
| 1 | squash commit の diff 全読（`git show <squash> -- . ':!docs'`）。D0: `ok` が増える変更なし・条件不変・サイレントフォールバックなし・scope 内・動的文字列がログ / 公開面に出ていない | ローカル git |
| 2 | PR は merged、`merge_commit_sha` と `head.sha` が報告と一致、**Sol reviewed SHA = head.sha** | API `pulls/<n>` |
| 3 | main CI が squash SHA で success | API `actions/runs?event=push` |
| 4 | dispatch run が success、`head_sha` の祖先に squash SHA を含む、開始時刻が禁止時間帯外 | API `actions/runs?event=workflow_dispatch` |
| 5 | 生成 commit の親 = squash SHA、変更は `docs/index.html` + `docs/status.json` のみ、**author date が dispatch run の開始〜終了の間**（cron の生成物と取り違えない） | `git show --stat --format='%ci'` |
| 6 | `git show <生成>:docs/status.json` を parse: gate passed・総数・feeds/rankings 比・`sources` 全行・キー集合・非 ok 行・`detail` に URL / パス / `?` / 例外文なし | ローカル git（WebFetch は要約モデル経由なので契約判定には使わない） |
| 7 | pytest を自走して件数が報告と一致、compileall。完了 grep は **Codex の行範囲を使わず、merged ファイルから関数境界を自分で導出して**再実行 | ローカル（certifi スタブ） |
| 8 | 報告中の**定量主張**をすべて再計算（分岐数・fixture 件数・リンク数など） | grep / wc |
| 9 | 報告中の**「いつから」主張**を履歴で再確認 | `git log` 走査 |
| 10 | run ログ件数は「Codex 報告」印。`status.json` の非 ok 0 と整合するか（SNS / Node.js / deprecated は対応物が無いので Codex 単独証拠と明記） | 間接 |
| 11 | open PR（Dependabot）、branch は main のみ、worktree clean、`main` = `origin/main`、`git stash list` の各 stash を `git stash show -p` で中身確認 | API + ローカル |
| 12 | Obsidian: 指示書指定パスに `## S<n>` が 1 件だけ増え、同ディレクトリに新規ノートが増えていない | vault |
| 13 | 可能なら次の cron 1 回後の `status.json` も同値 | Pages |

結果表は Obsidian ノートに残す（主張 / 結果 / 一次証拠 / 確認者）。1 項目でも RED なら §7。意味的レビューの指摘で「誤データが出ていない・潜在型」のものは follow-up として次フェーズの backlog に載せる（v1 の P1 S6 / P2 S4 と同じ扱い）。

## 7. Revert runbook

- Codex: `git revert <squash SHA>`（squash なので 1 commit）→ PR → `gh pr checks` → squash merge → dispatch 1 回 → §5 形式で報告。禁止時間帯を避ける。cron は `docs/` しか触らないので衝突しない。生成 commit は revert しない（次 run が上書き。ただし **public 履歴には残る**）
- 生成物が壊れて gate が落ちている場合、`status.json` は最後の成功実行のまま残る（仕様）。Actions が赤のまま放置しない
- 秘密がログ / `docs/` に出た疑いがあれば revert より先にキー失効（ユーザー作業、L）。履歴からの除去は別途判断

## 8. 指示書テンプレ

```
§0 開始チェック（期待する開始状態を whitelist で書く: untracked / dirty / stash に何が残っていてよいか、最初の commit に含めるファイル。§3-A 該当の有無）
§1 目的
§2 設計判断 D0..Dn（D0 = 共通規則: フォールバック禁止・ok を増やさない・変えたい時は報告）
§3 制約・禁止事項
§4 検証（報告に貼る出力を列挙。完了 grep はコマンドと範囲根拠まで指定）
§5 出荷手順（禁止時間帯 → gh pr checks → merge → dispatch → 生成物検証。§3-A 該当ならここに「GO 待ちで停止」と書く）
§6 返却形式（本ファイル §5 のバンドル）＋ Obsidian ノートのパス
§7 運用調査・見送り（触らないこと）
§8 参考: 現行コードの該当箇所（SHA 付き）
```

## 9. 過去の catch と v2 での受け皿

| いつ | 何が見つかったか | 誰が・どうやって | v2 での受け皿 |
|---|---|---|---|
| P0 S4 | 指示書からの逸脱 3 件（許容）と nit | Claude の diff 全読 + Opus/Sonnet lens | §6-1 diff 全読（出荷後）。`ok` を増やす逸脱は D0 で Codex が停止（§4-3） |
| P1 S2 | main への直接 commit が hook で禁止（手順の暗黙前提が崩れていた） | Claude の実装中 | §8 §0 に期待する開始状態と commit 経路を明記 |
| P1 S5 | 下位モデルの初稿が fixture 未完了のまま提出、Terra が panel 取り違えを検出 | Codex 側の親 QA・独立レビュー | §2 独立レビューを merge 前に必須化、reviewed SHA 固定 |
| P1 S6 | `"active" in class_name` が `inactive` にも一致（潜在バグ） | Opus lens（事前 GO 時）→ follow-up として P2 へ | **出荷後に移る**（§6 Opus lens）。v1 でも出荷は止めていない |
| P1 S8 | Claude 自身の verify 漏れ 2 点（status.json 2 スナップショットの実体、main CI 3 本の conclusion） | advisor | §6 で advisor 2 回、表の項目を固定 |
| P2 S2 | 指示書 D1 がライブ DOM と不一致 | Codex のライブ before/after → 停止 | §4-2 / §4-3 停止条件 |
| P2 S4 | 位置結合・数字タイトルガード欠如など残存リスク 5 件 | Opus lens（事前 GO 時）→ backlog | **出荷後に移る**（§6 Opus lens） |
| P2 S6 | fail-closed 分岐「12」→ 実際は 27 | Sonnet サイジング + 親 grep | §5 定量主張はコマンド＋範囲根拠＋生出力、§6-7/8 親が範囲を再導出して再計算 |
| P2 S6 | SNS 全滅は「直近 4 run」ではなく 2026-03-04 から | Claude の `docs/index.html` 履歴走査 | §5「いつから」は onset 特定、§6-9 |
| P3 S2 | 理由記録後に例外が出た場合だけ診断状態が残るバグ | Codex 側 Terra/high レビュー（PR 前） | §2 独立レビュー必須（Codex 側で本番前に捕まえる経路は残る） |
| P3 S3 | 完了 grep を自走していない、stash の中身未確認 | advisor | §6-7 自走、§6-11 stash の中身 |
| P3 S5 | run ログ本文が sandbox から読めない（P1 S1 から 8 セッション連続で「未確認」） | — | §5 Codex が grep コマンド＋出力、§6-10 status.json と突合。GREEN と言い切らず「Codex 報告」印 |
| P3 S5 | 8/9 なのに「全 GREEN」と書きかけた | advisor | §5 / §6「未確認は未確認と書く」 |

## 10. 次フェーズ（SNS 復旧）の v2 マッピング

1. **先にユーザーが xAI コンソール**（API Keys / Billing / Usage）で 403 の原因候補 ①キー失効 ②課金・クレジット ③`x_search` の権限 を確認する。コードは触らない（L: 秘密。キー文字列は貼らない）。ここで原因が分かれば 3. の「理由をログに出す」変更は不要になる
2. 観測性: `sources` に `kind: "sns"` 行を追加（既存 `status` 語彙、`summarize_error` 経由の `detail`、`gate` には混ぜない）→ **§3-B、v2 1 往復**。`test_status_json.py` の `sources[1]` 完全一致 assert とキー集合 assert の更新を指示書 §2 で明記。`DEFAULT_XAI_MODEL` の現行 ID への更新も同じ PR
3. xAI 応答の `error.message` をログに出す → **§3-A-2、事前 GO 必須**。1. で原因が特定できない場合だけ実施
4. キーのローテーション → ユーザー作業（GitHub Secrets）。その後 dispatch 1 回で復旧確認（Codex）
