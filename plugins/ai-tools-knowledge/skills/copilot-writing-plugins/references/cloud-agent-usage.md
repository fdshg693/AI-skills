# Copilot cloud agent で Plugin を使う

## 目次

- [適用範囲](#適用範囲)
- [リポジトリ設定](#リポジトリ設定)
- [marketplace を追加する](#marketplace-を追加する)
- [確認事項](#確認事項)

## 適用範囲

Copilot cloud agent で repository に Plugin を有効化するときに読む。CLI のような個人端末への imperative install ではなく、repository の設定を commit して agent に適用する流れを基本にする。

公式: [About GitHub Copilot plugins](https://docs.github.com/en/copilot/concepts/agents/about-plugins)、[GitHub Copilot CLI configuration directory](https://docs.github.com/en/copilot/reference/copilot-cli-reference/cli-config-dir-reference)

## リポジトリ設定

`.github/copilot/settings.json` の `enabledPlugins` に、登録済み marketplace の Plugin を指定する。

```json
{
  "enabledPlugins": {
    "security-checks@copilot-plugins": true,
    "team-tools@company-tools": true
  }
}
```

同じ設定ファイルは Copilot CLI と cloud agent の両方で読まれるため、CLI だけで利用する個人設定を repository 設定へコピーしない。レビューでは、誰にどの Plugin が有効になるか、Plugin の version / source、含まれる hooks / MCP / LSP の権限を確認する。

## marketplace を追加する

既定 marketplace 以外を使う場合は `extraKnownMarketplaces` を追加する。

```json
{
  "extraKnownMarketplaces": {
    "company-tools": {
      "source": {
        "source": "github",
        "repo": "your-org/plugin-marketplace",
        "ref": "v1.0.0"
      }
    }
  },
  "enabledPlugins": {
    "team-tools@company-tools": true
  }
}
```

source の形式、ref / SHA の指定、cloud agent で許可される marketplace は現行の GitHub Docs と組織ポリシーを優先する。未登録 marketplace を `enabledPlugins` にだけ書いても解決できない。

## 確認事項

- cloud agent が対象 repository と plan で利用可能か確認する。
- Plugin の component が cloud agent の host でサポートされるか確認する。ローカル CLI 専用の shell、path、認証情報をそのまま移植しない。
- PR や agent session で Plugin の skill / agent が期待どおり読み込まれるか確認する。
- settings の変更を共有する前に、外部 marketplace の publisher、固定 ref / SHA、hooks / MCP の実行内容をレビューする。
