# モデル指定を使って実行する方法

出典: `docs/cli/reference/parameters.md`, `docs/cli/reference/slash-commands.md`, `docs/cli/reference/configuration.md`, `docs/subagents.md#model-configuration`, `help/models-and-usage/available-models.md`

## CLI 起動時にモデルを指定する

```bash
# グローバルオプション --model <model>
agent --model gpt-5 "fix the tests"
agent --model sonnet-4-thinking

# 利用可能なモデル一覧を見て終了する
agent --list-models

# アカウントで使えるモデル一覧を確認するサブコマンド
agent models
```

- `--model <model>` はグローバルオプション（`agent` 全体で共通）。値はモデル ID 文字列（例: `gpt-5`, `sonnet-4`, `sonnet-4-thinking`）。
- `--list-models` はモデル一覧を表示して終了するフラグ。`agent models` サブコマンドは「このアカウントで使えるモデル一覧」を表示するコマンドとして別に存在する（ヘルプ出力上は両方存在するが、実機での出力差分は未確認）。

## 対話モード中にモデルを切り替える

```text
/model auto
/model gpt-5
/model sonnet-4-thinking
/model [filter]   # Tab キーで編集可能
```

`/model` はスラッシュコマンド一覧（`docs/cli/reference/slash-commands.md`）にも記載があり、`[filter]` を付けて絞り込み検索もできる。

## 設定ファイルでの永続化

`~/.cursor/cli-config.json`（Windows: `$env:USERPROFILE\.cursor\cli-config.json`）に以下のオプションフィールドがある（`docs/cli/reference/configuration.md`）:

| フィールド               | 型      | 説明                                               |
| ------------------------ | ------- | -------------------------------------------------- |
| `model`                  | object  | 選択中のモデル設定                                 |
| `maxMode`                | boolean | モデルピッカーでの Max Mode 設定を永続化するフラグ |
| `hasChangedDefaultModel` | boolean | CLI が内部管理するデフォルトモデル変更フラグ       |

これらは基本的に CLI が `/model` 実行時などに書き込む管理フィールドで、手動編集は非推奨（`permissions` 以外の全設定はグローバルのみで、プロジェクト側 `.cursor/cli.json` では権限しか設定できない点に注意）。

## Auto / Premium / 個別モデルの使い分け（エディタと共通の考え方）

`help/models-and-usage/available-models.md` より:

- **Auto**: 知性・コスト・信頼性のバランスを Cursor 側が選択。日常タスク向き。
- **Premium**: Cursor が内部ベンチマークで選んだ「今もっとも高性能」なモデル群。複雑なタスク向き。
- **Composer**: Cursor 自社モデル。速くて対話的コーディングに強い。
- **Claude Opus / GPT Codex**: 複雑な多段階タスクに強い。
- モデルがリージョン制限で「not available」になる場合は Auto を使うか、BYOK（自分の API キー登録）で回避可能。

## Subagent（`.cursor/agents/*.md`）のモデル指定（参考・詳細は別スキルへ）

Subagent の YAML frontmatter にある `model` フィールドは `inherit`（親と同じ、デフォルト）か具体的なモデル ID。ブラケット構文でモデルごとのパラメータを追加指定できる:

```yaml
model: claude-opus-4-8[effort=high,context=300k]
model: composer-2.5[] # fast ではなく標準バリアントを明示選択
model: composer-2.5[fast=false]
```

- `effort=<low|...|high>`: reasoning effort
- `context=<size>`: コンテキストウィンドウサイズ（例 `300k`）
- 利用可能なオプションはモデル依存。SDK の model parameters と同じ `id=value` 形式。

この bracket 構文が `agent --model` のようなトップレベル CLI フラグでも使えるかは未確認（ドキュメント上は subagent frontmatter の説明としてのみ記載）。実装時に `agent --model 'claude-opus-4-8[effort=high]' -p "..."` を実機で試して検証すること。

チームアドミンによるモデルブロック / Max Mode 未有効 / プラン制限のいずれかに該当すると、指定した `model` は無視され Cursor 側の互換モデルにフォールバックする（`docs/subagents.md` FAQ）。
