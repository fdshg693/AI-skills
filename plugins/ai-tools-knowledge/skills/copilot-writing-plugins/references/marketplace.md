# marketplace を作成・配布する

## 目次

- [marketplace の配置](#marketplace-の配置)
- [marketplace.json](#marketplacejson)
- [Plugin を登録する](#plugin-を登録する)
- [利用者向け手順](#利用者向け手順)
- [再現可能な配布](#再現可能な配布)

## marketplace の配置

marketplace は Plugin の registry で、GitHub repository、他の Git hosting、local / shared filesystem に置ける。GitHub Copilot CLI では repository の `.github/plugin/marketplace.json` が標準的で、`.claude-plugin/marketplace.json` も検出対象になる。

公式: [Creating a plugin marketplace for GitHub Copilot CLI](https://docs.github.com/en/copilot/how-tos/copilot-cli/customize-copilot/plugins-marketplace)、[CLI plugin reference](https://docs.github.com/en/copilot/reference/copilot-cli-reference/cli-plugin-reference#marketplacejson)

## marketplace.json

トップレベルに `name`、`owner`、`plugins` を置く。`name` は小文字・数字・ハイフンのみ、最大 64 文字にする。

```text
plugin-marketplace/
├── .github/
│   └── plugin/
│       └── marketplace.json
└── plugins/
    └── team-tools/
        ├── plugin.json
        ├── agents/
        └── skills/
```

```json
{
  "name": "company-tools",
  "owner": { "name": "Example Team" },
  "metadata": {
    "description": "Plugins for the development team",
    "version": "1.0.0"
  },
  "plugins": [
    {
      "name": "team-tools",
      "description": "Shared development agents and skills",
      "version": "1.0.0",
      "source": "./plugins/team-tools"
    }
  ]
}
```

`plugins[].source` は repository root からの相対 path、GitHub source、Git URL などを指定する。entry の `name` は Plugin の `plugin.json` と一致させ、`version` を更新したら manifest と marketplace entry の両方を確認する。

## Plugin を登録する

1. Plugin を作成し、CLI の local path install で各 component を検証する。
2. `marketplace.json` を作成し、各 entry の source が実在する Plugin directory を指すことを確認する。
3. marketplace repository を共有する。
4. 利用者に marketplace の登録、browse、install の手順を伝える。

```powershell
copilot plugin marketplace add OWNER/REPO
copilot plugin marketplace list
copilot plugin marketplace browse company-tools
copilot plugin install team-tools@company-tools
```

Marketplace は GitHub Copilot の marketplace であり、Claude Code の marketplace と同じファイルを再利用できる場合でも、Plugin の manifest、hooks、MCP、host compatibility を別途検証する。

## 利用者向け手順

利用者には少なくとも次を明示する。

- marketplace の source と trust boundary
- `copilot plugin marketplace add ...`
- `copilot plugin install NAME@MARKETPLACE`
- `copilot plugin list` と component の確認方法
- update / uninstall 方法
- 必要な環境変数、runtime、権限、対象 host

外部 marketplace では、README の説明だけでなく source の hook、MCP server、script を確認してから install するよう案内する。

## 再現可能な配布

marketplace entry の source object で `ref` または full 40-character `sha` を指定できる。強制 push や tag の移動に影響されない再現性が必要なら SHA pin を使い、更新時は意図した commit に変更する。

```json
{
  "source": {
    "source": "github",
    "repo": "your-org/plugin-marketplace",
    "path": "plugins/team-tools",
    "sha": "0123456789abcdef0123456789abcdef01234567"
  }
}
```

厳密な source schema と marketplace entry の全フィールドは [CLI plugin reference](https://docs.github.com/en/copilot/reference/copilot-cli-reference/cli-plugin-reference) を確認する。
