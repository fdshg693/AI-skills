# Copilot CLI で Plugin を使う

## 目次

- [Plugin を探す](#plugin-を探す)
- [インストール元](#インストール元)
- [marketplace を登録して install する](#marketplace-を登録して-install-する)
- [管理する](#管理する)
- [Plugin を検証する](#plugin-を検証する)

公式: [Finding and installing plugins for GitHub Copilot CLI](https://docs.github.com/en/copilot/how-tos/copilot-cli/customize-copilot/plugins-finding-installing)、[CLI plugin reference](https://docs.github.com/en/copilot/reference/copilot-cli-reference/cli-plugin-reference)

## Plugin を探す

登録済み marketplace を確認し、一覧から install 対象を決める。

```powershell
copilot plugin marketplace list
copilot plugin marketplace browse MARKETPLACE-NAME
```

interactive session では `/plugin marketplace list` と `/plugin marketplace browse MARKETPLACE-NAME` も使える。README だけでなく、`plugin.json`、skills、hooks、MCP、外部通信、必要権限をレビューしてから導入する。

## インストール元

`copilot plugin install SPECIFICATION` の specification は次のいずれか。

| 形式                         | 例                                  |
| ---------------------------- | ----------------------------------- |
| marketplace                  | `plugin@marketplace`                |
| GitHub repository            | `OWNER/REPO`                        |
| repository 内の subdirectory | `OWNER/REPO:path/to/plugin`         |
| Git URL                      | `https://github.com/owner/repo.git` |
| local path                   | `./my-plugin` または絶対パス        |

```powershell
copilot plugin install test-tools@my-marketplace
copilot plugin install OWNER/REPO:path/to/plugin
copilot plugin install ./my-plugin
```

直接 install は marketplace への登録を省略できる。信頼できない source の hook や MCP は、インストール前に実行内容を確認する。

## marketplace を登録して install する

GitHub repository なら `OWNER/REPO`、local directory なら path、他の Git hosting なら Git URL を指定する。

```powershell
copilot plugin marketplace add OWNER/REPO
copilot plugin marketplace browse MARKETPLACE-NAME
copilot plugin install PLUGIN-NAME@MARKETPLACE-NAME
```

登録名は repository 名と異なることがあるので、`marketplace list` の結果を使う。更新後に catalog が古い場合は `copilot plugin marketplace update MARKETPLACE-NAME` を実行する。

## 管理する

```powershell
copilot plugin list
copilot plugin update PLUGIN-NAME
copilot plugin update --all
copilot plugin enable PLUGIN-NAME
copilot plugin disable PLUGIN-NAME
copilot plugin uninstall PLUGIN-NAME
copilot plugin marketplace remove MARKETPLACE-NAME
```

`plugin` と `plugins` は subcommand によって同義として扱われる。marketplace を削除する際、そこから install した Plugin が残っていると拒否される。`--force` は関連 Plugin の削除も行うため、対象を確認してから使う。

## Plugin を検証する

新しい session を開始し、次を確認する。

```text
/plugin list
/agent
/skills list
```

ローカル開発でファイルを変更した場合、install 済み component は cache から読まれるため、`copilot plugin install ./my-plugin` を再実行する。Plugin の `name` ではなく path を uninstall 引数に渡さない。
