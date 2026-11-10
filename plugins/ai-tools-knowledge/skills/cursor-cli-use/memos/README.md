# cursor-cli-use 事前調査メモ

`cursor-cli-use`（Cursor CLI 利用特化スキル）を作成するための事前調査メモ。このメモをもとに [../SKILL.md](../SKILL.md) と [../README.md](../README.md)（モデル選択の理由など）を作成済み。
`cursor-cli-docs`（`agent --help` の実出力）と `cursor-docs`（`cursor.com/docs` の `.md` エンドポイント）を情報源として、2026-07-09 時点の内容を調査した。

各メモの根拠となった生の `.md` 本文は `C:\Users\xingw\AppData\Local\Temp\claude\...\scratchpad\cursor_docs\*.txt`（セッション一時ディレクトリ、リポジトリには含まれない）に保存済み。再取得する場合は `cursor-docs` スキルの `download_cursor_reference.py` の要領で該当 URL を直接 `requests.get()` すればよい（`WebFetch` ツールは cursor.com に対して原因不明の 404 を返したため、今回は Python `requests` で直接取得した）。

## メモ一覧

1. [01-model-selection.md](01-model-selection.md) — モデル指定を使って実行する方法
2. [02-pricing-billing.md](02-pricing-billing.md) — モデルごとの料金・課金体系
3. [03-debugging-logs.md](03-debugging-logs.md) — ログなどを使ったデバッグ方法
4. [04-tools-permissions.md](04-tools-permissions.md) — ツール・権限の操作方法
5. [05-reusable-agents-pointer.md](05-reusable-agents-pointer.md) — 繰り返し指示を避けるための「Cursorエージェント（subagent）作成方法」— 別スキル切り出しのための調査メモ（このスキル自体には実装しない）

## 未解決・要検証事項（実装時に確認する）

- `--model` フラグの値に、subagents で使えるブラケット構文（`claude-opus-4-8[effort=high]` 等）がトップレベルの `agent --model` でも使えるか未確認（ドキュメント上は subagent 向けの記載のみ）。
- `agent models` / `--list-models` の実際の出力フォーマットは 2026-07-09 に実機確認済み（バージョン `2026.07.08-0c04a8a`）。結果は [../README.md](../README.md) のモデルID確度表に反映済み。旧バージョン（`2026.03.30-a5d3e17`）では同じアカウントで「No models available for this account」となり取得できなかった経緯があるため、CLI/アカウント状態次第で再び取得できなくなる可能性は残る。
- モデル価格表（`models-and-pricing.md`）は変動が激しいページ。スキル本体に価格を書き写さず、都度 `cursor-docs` スキル経由で最新を取得する方針にする（`cursor-docs` の補足にある通り 24 時間キャッシュ）。
