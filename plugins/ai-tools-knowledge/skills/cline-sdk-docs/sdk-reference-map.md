# Cline SDK 参照マップ

回答時はまず同階層の [sdk-reference.md](sdk-reference.md) の該当節を読み、詳細な型や仕様差異が必要な場合にこの表から公式ページを選ぶ。`cline-docs` の `output/llms.txt` を索引として使い、質問に対応するページだけを抽出する。以下の URL は公式ドキュメントの一次情報である。

| 質問・目的                                          | 最初に読むページ                                                                 | 追加で読むページ                                                                                                                     |
| --------------------------------------------------- | -------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------ |
| SDK の概要、インストール、最初の Agent              | [SDK overview](https://docs.cline.bot/sdk/overview)                              | [Examples](https://docs.cline.bot/sdk/examples)、[Building an Agent](https://docs.cline.bot/sdk/guides/building-an-agent)            |
| パッケージの選択・責務                              | [Packages](https://docs.cline.bot/sdk/architecture/overview)                     | [SDK overview](https://docs.cline.bot/sdk/overview)                                                                                  |
| `Agent` / `AgentRuntime` の実行、継続、停止、復元   | [Agent reference](https://docs.cline.bot/sdk/reference/agent)                    | [Events](https://docs.cline.bot/sdk/events)、[Types](https://docs.cline.bot/sdk/reference/types)                                     |
| セッション、永続化、組み込みツール、Hub、Automation | [ClineCore](https://docs.cline.bot/sdk/reference/cline-core)                     | [ClineCore guide](https://docs.cline.bot/sdk/clinecore)、[Hub-Spoke architecture](https://docs.cline.bot/sdk/architecture/hub-spoke) |
| カスタムツールの作成・登録・テスト                  | [Creating Custom Tools](https://docs.cline.bot/sdk/guides/creating-custom-tools) | [Tools API](https://docs.cline.bot/sdk/reference/tools-api)、[Tools](https://docs.cline.bot/sdk/tools)                               |
| ストリーミング、UI 更新、使用量、セッションイベント | [Events](https://docs.cline.bot/sdk/events)                                      | [Events reference](https://docs.cline.bot/sdk/reference/events)                                                                      |
| プロバイダー、モデル、OpenAI互換、Gateway           | [Model Providers](https://docs.cline.bot/sdk/model-providers)                    | [Gateway reference](https://docs.cline.bot/sdk/reference/gateway)、[Types](https://docs.cline.bot/sdk/reference/types)               |
| ツールの有効化・自動承認・人手承認                  | [Permission Handling](https://docs.cline.bot/sdk/guides/permission-handling)     | [Tools API](https://docs.cline.bot/sdk/reference/tools-api)                                                                          |
| プラグインでツールや Hooks を拡張                   | [Plugins overview](https://docs.cline.bot/sdk/plugins)                           | [Writing Plugins](https://docs.cline.bot/sdk/guides/writing-plugins)、[Plugin examples](https://docs.cline.bot/sdk/plugin-examples)  |
| サブエージェント、チーム                            | [Multi-Agent Teams](https://docs.cline.bot/sdk/guides/multi-agent-teams)         | [ClineCore](https://docs.cline.bot/sdk/reference/cline-core)、[Examples](https://docs.cline.bot/sdk/examples)                        |
| Cron による定期実行                                 | [Scheduled Agents](https://docs.cline.bot/sdk/guides/scheduled-agents)           | [Hub-Spoke architecture](https://docs.cline.bot/sdk/architecture/hub-spoke)                                                          |
| 本番デプロイ、失敗処理、監視、コスト、セキュリティ  | [Going to Production](https://docs.cline.bot/sdk/guides/going-to-production)     | [Permission Handling](https://docs.cline.bot/sdk/guides/permission-handling)、[Events](https://docs.cline.bot/sdk/events)            |

## 抽出時の目安

リポジトリ内の `cline-docs` スキルを使える場合は、同スキルの `scripts/extract_doc_section.py` に、表の URL の `/sdk/` 以下のパスを渡す。たとえば次のように実行する。

```bash
python scripts/extract_doc_section.py sdk/overview sdk/reference/agent sdk/guides/creating-custom-tools
```

REST API の `/api/*`、CLI の `/cli/*`、IDE の Skills / Rules の説明を SDK の挙動として流用しない。
