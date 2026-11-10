# VS Code で Plugin を使う

## 目次

- [対応範囲](#対応範囲)
- [発見・インストール](#発見インストール)
- [有効化・無効化](#有効化無効化)
- [CLI との共有](#cli-との共有)
- [workspace で推奨する](#workspace-で推奨する)

## 対応範囲

VS Code の Agent Plugins は Preview 機能で、Plugin は commands、skills、agents、hooks、MCP servers をまとめられる。企業ポリシーで `chat.plugins.enabled` が管理されている場合があるため、表示されないときは組織設定も確認する。

公式: [Agent plugins in VS Code](https://code.visualstudio.com/docs/agent-customization/agent-plugins)

## 発見・インストール

1. Extensions view を開き、`@agentPlugins` で検索する。
2. marketplace の publisher と Plugin の内容を確認する。
3. Install を選択する。新しい marketplace の初回 install では trust prompt を確認する。

marketplace を経由せず、Command Palette の `Chat: Install Plugin From Source` から Git repository URL を指定することもできる。Agent Customizations editor の Plugins ページから操作できる場合もある。

## 有効化・無効化

Extensions view または Agent Customizations editor から、global または workspace 単位で enable / disable / uninstall する。無効化すると、その Plugin の skills、agents、hooks、MCP servers、slash commands が利用できなくなる。

Plugin が表示されても component が見えない場合は、Chat の customization diagnostics で読み込みエラー、manifest の場所、skill 名、対象 agent を確認する。

## CLI との共有

GitHub Copilot CLI で install した Plugin は、VS Code が `~/.copilot/installed-plugins/` から自動検出する場合がある。共有時は形式差分を確認する。

- VS Code は `.plugin/plugin.json`、ルート `plugin.json`、`.github/plugin/plugin.json`、`.claude-plugin/plugin.json` などを検出する。
- Copilot 形式の hook はルート `hooks.json`。Claude 形式は `hooks/hooks.json`。
- Copilot 形式では Claude 形式の `${CLAUDE_PLUGIN_ROOT}` を前提にしない。MCP / hook の path token は対象 client の仕様に合わせる。

VS Code の自動検出だけを根拠に cloud agent や CLI で動くと判断せず、各 host で install と component の検証を行う。

## workspace で推奨する

チームで Plugin を推奨する場合、`.github/copilot/settings.json` または対応する workspace settings に marketplace と enabled Plugin を設定する。例:

```json
{
  "extraKnownMarketplaces": {
    "company-tools": {
      "source": {
        "source": "github",
        "repo": "your-org/plugin-marketplace"
      }
    }
  },
  "enabledPlugins": {
    "code-formatter@company-tools": true
  }
}
```

設定キーの schema と対象 agent は VS Code の [AI settings reference](https://code.visualstudio.com/docs/agents/reference/ai-settings) で確認する。workspace 設定は共有されるため、外部 source、hook、MCP の trust boundary をレビューしてから commit する。
