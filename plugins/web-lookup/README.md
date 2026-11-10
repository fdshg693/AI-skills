# web-lookup

WEB 調査用のスクリプトをスキルに同梱した Claude Code プラグイン（旧 `my-tools-no-install` のうち WEB 調査の部分）。

対応する CLI を `tools/` からインストールする必要はない。プラグイン（または個別スキル）をよそへ移しても動く。`tools/` 配下のインストール済み CLI を前提にするスキルは [my-tools](../../../tools/_plugin/my-tools/) に置く。

- [skills/web-lookup/](skills/web-lookup/) — grep.app / Microsoft Learn / AWS Knowledge MCP / Tavily / Context7 を1つの同梱 CLI にまとめた WEB 調査
- [skills/tav-lit/](skills/tav-lit/) — 既知の URL 1 件の本文（または関連部分）を Tavily extract で Markdown ファイルに取る（抽出スクリプト同梱）

一覧は生成カタログ [skills/CATALOG.md](skills/CATALOG.md)。設計意図は各スキルの `README.md`、実行時の手順は `SKILL.md`。

## スキルの置き方

個別スキルは `skills/<skill-name>/` に置き、実行に必要なスクリプトもその配下へ同梱する。コピーした先でも、リポジトリルートの `tools/` やグローバルインストールを参照しないこと。

文書の変換・書き起こしのように WEB 調査ではない同梱型スキルは [doc-tools](../doc-tools/) に置く。
