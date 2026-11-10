# Plugin のトラブルシューティング

## 目次

- [Plugin 自体が表示されない](#plugin-自体が表示されない)
- [component が読み込まれない](#component-が読み込まれない)
- [変更が反映されない](#変更が反映されない)
- [marketplace や install が失敗する](#marketplace-や-install-が失敗する)
- [hooks / MCP の問題](#hooks--mcp-の問題)

## Plugin 自体が表示されない

次を順に確認する。

1. Plugin 形式に応じた場所に `plugin.json` があるか確認する。最初は Plugin ルートの `plugin.json` に寄せる。
2. manifest が valid JSON か確認する。
3. `name` が小文字・数字・ハイフンのみで、64 文字以内か確認する。slash、colon、namespace prefix は使わない。
4. CLI では `copilot plugin list`、VS Code では `@agentPlugins` と customization diagnostics を確認する。
5. VS Code では agent plugin 機能が組織設定で無効化されていないか確認する。
6. cloud agent では `.github/copilot/settings.json` の `extraKnownMarketplaces` と `enabledPlugins` の marketplace / Plugin 名が一致するか確認する。

## component が読み込まれない

- manifest の `agents` / `skills` / `hooks` / `mcpServers` / `lspServers` の path と実ファイルを比較する。
- skill directory 直下が正確に `SKILL.md` か、frontmatter の `name` が kebab-case か確認する。
- agent のファイル名、frontmatter、必要 tool が対象 host の仕様に合うか確認する。
- Plugin を disable していないか確認する。
- 同名の agent / skill が project-level または personal configuration にないか確認する。CLI の agent / skill は first-found-wins で、project-level のものが Plugin を上書きできない形で優先される。
- MCP server の重複名は last-wins になるため、どの Plugin が最後に読み込まれたかと警告を確認する。

## 変更が反映されない

Plugin install 後の component は cache から読まれる。local development では次を再実行し、新しい session を作る。

```powershell
copilot plugin install ./my-plugin
copilot plugin list
```

marketplace の一覧が古い場合は `copilot plugin marketplace update NAME` を実行する。公開済み Plugin の変更は `plugin.json` と marketplace entry の version 更新も確認する。

## marketplace や install が失敗する

- `marketplace.json` の top-level `name`、`owner`、`plugins` を確認する。
- `plugins[].source` が marketplace root から解決でき、対象 directory に `plugin.json` があるか確認する。
- entry の `name` と manifest の `name` が一致するか確認する。
- source の Git URL、repository、subdirectory、ref / SHA が存在するか確認する。
- marketplace を remove できない場合、その marketplace から install した Plugin を先に確認する。`--force` は関連 Plugin も削除するため、明示的に必要な場合だけ使う。

## hooks / MCP の問題

hooks と MCP は Plugin が読み込まれた時点で実行・起動され得る。次を確認する。

- command、runtime、実行権限、相対 path、Windows / Unix の shell 差異
- 環境変数と秘密情報が source に含まれていないこと
- 外部通信先、最小権限、入力の検証、タイムアウト
- Copilot CLI、VS Code、cloud agent の path token と設定ファイル位置の差異
- MCP server の process log と server name の衝突

問題を切り分ける間は Plugin 全体を trust して再実行するのではなく、component を一つずつ無効化して原因を絞る。公式: [About GitHub Copilot plugins](https://docs.github.com/en/copilot/concepts/agents/about-plugins)、[Agent plugins in VS Code](https://code.visualstudio.com/docs/agent-customization/agent-plugins)
