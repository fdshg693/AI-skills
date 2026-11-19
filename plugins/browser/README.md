# browser

`playwright-cli`（`@playwright/cli`）でブラウザを操作するための Claude Code プラグイン。
microsoft/playwright のクローンで育てたスキルを、クローンの `.claude/` に依存しない形に直して持ち込んだもの。

`tools/` の CLI のインストールは要らない。各スキルは upstream（microsoft/playwright `main`）のスナップショットを
同梱スクリプトで取り直して根拠にする。

## 4 スキルの責務分担

| スキル                                                             | 担当                                                                                                                                                                  |
| ------------------------------------------------------------------ | --------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| [using-playwright-cli](skills/using-playwright-cli/)               | **認証不要のブラウザ操作の入口。** `playwright-cli` のコマンド仕様の正（upstream 同梱スキルのミラー）と、状況別の入口（初見サイトの偵察・スクリプト化・実験用サイト） |
| [sharing-browser-with-user](skills/sharing-browser-with-user/)     | **認証が要る区間。** 可視ブラウザでユーザーにログインしてもらい、永続プロファイルで持ち越す。手順と禁止事項だけを持ち、コマンド仕様は using-playwright-cli に任せる   |
| [searching-playwright-docs](skills/searching-playwright-docs/)     | **公式情報の参照（API・ガイド）。** `docs/src/**/*.md` を sparse clone で取り、検索・セクション抽出する                                                               |
| [authoring-playwright-agents](skills/authoring-playwright-agents/) | **公式情報の参照（エージェント定義）。** planner / generator / healer の定義と `playwright-test` MCP ツールのミラー、`*.agent.md` の書き方                            |

`pwq`（出力を縮めるラッパー）・`pwdo`（一区間の委譲）を前提にした手順は、`tools/` の CLI のインストールが必須なので
my-tools プラグインの [browser-context-tools](../../../tools/_plugin/my-tools/skills/browser-context-tools/) に分けた。
using-playwright-cli からは「入っていれば」の任意の参照にしている。

一覧は生成カタログ [skills/CATALOG.md](skills/CATALOG.md)。設計意図は各スキルの `README.md`、実行時の手順は `SKILL.md`。

## 実測の根拠

スキル本文の数値・規則の根拠は、アンブレラの `docs/topics/browser-automation/`（偵察・往復・引き渡し・スクリプト化・委譲の実測メモ）にある。
スキル本文（エージェントが読む側）からは張らず、各スキルの README からだけ参照する。実測の多くはアンブレラの `tools/browser/test-sites/`（ローカルのテストサイト）に対して行った。
