# SNS 復旧 — Codex 調査ブリーフ（読み取り専用）

作成: 2026-08-27（Claude 監督）。**コードは変更しない。commit / push / PR / dispatch もしない。**
目的は、SNS タブが 2026-03-04（`ede81d6`）以降 xAI API 403 で全滅している件の一次証拠を、Claude が sandbox から読めない経路（`gh`）で集めること。

## 禁止事項

- `scripts/**` `templates/**` `.github/**` `docs/**` を編集しない
- 環境変数ファイルや secrets の値を読まない・貼らない。`gh secret list` の **名前と更新日だけ** 使う
- `git stash` / `git checkout` で作業ツリーを変えない（`M AGENTS.md` / `?? plans/*` はそのまま）

## 調査項目（各項目、コマンドと生出力をそのまま貼る）

1. **Secret の更新日**
   `gh secret list`
   → `XAI_API_KEY` の UPDATED が onset（2026-03-04）より前か後か。

2. **直近 run の SNS エラー行（全文）**
   `gh run list --workflow=update-news.yml --limit 3`
   `gh run view <直近 success の run id> --log | grep -E '\[SNS'`
   → 5 カテゴリ分の `[SNS ERROR]` / `[SNS WARN]` 行を **省略せず** 貼る（例外文に含まれるのは status line と URL のみのはず。応答本文は含まれない）。
   `gh run view <同 id> --log | grep -c '\[SNS ERROR\]'`

3. **403 が最初に現れた run**（Actions ログの保持期間内で最古のもの）
   `gh run list --workflow=update-news.yml --limit 200 --json databaseId,createdAt,conclusion --jq '.[-1]'`
   → 最古 run の id と日付。その run にも `[SNS ERROR]` があるか `grep -c`。
   （onset `ede81d6` = 2026-03-04 は Claude が `docs/index.html` 履歴で確定済み。再導出は不要。ここで見たいのは「ログ保持期間内は一貫して 403 か」だけ）

4. **例外文のパターン**
   2. の行から、`403 Client Error: Forbidden for url: https://api.x.ai/v1/responses` 以外の文言（`401` / `404` / `429` / timeout / JSON parse）が混ざっていないか。

## 返却形式

```
## 1 secret list（コマンド＋生出力）
## 2 直近 run の SNS 行（run id / 開始時刻 / grep 生出力 / grep -c）
## 3 最古 run（id / 日付 / grep -c）
## 4 パターン所見（1〜3 行）
## 未確認（実行できなかった項目と理由）
```

結果は Codex から Claude へ返す（Obsidian 追記は不要。Claude 側で行う）。
