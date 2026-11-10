# Kilo CLI コマンドガイド

日常の作業では以下を優先し、全オプションは`output/help_result.yaml`または`kilo help <command>`で確認する。

## 導入と起動

```text
npm install -g @kilocode/cli
kilo --version
kilo
kilo --continue
kilo --model provider/model --agent <agent>
```

- `kilo`はカレントディレクトリをプロジェクトとしてTUIを起動する。
- `--continue`は現在のワークスペースの最後のセッションを再開する。プロンプトや`--auto`との併用はできない。

## プロバイダーとモデル

```text
kilo auth list
kilo auth login --provider <provider>
kilo auth logout <provider>
kilo models [provider]
```

- 初回の対話設定はTUIの`/connect`が簡単である。
- TUIでは`/models`でモデル、`/agents`でエージェントを切り替える。

## セッションとレビュー

```text
kilo session list --max-count 20
kilo export <session-id> --sanitize
kilo import <file-or-url>
```

- TUIでは`/sessions`で切替、`/new`で新規作成、`/compact`で要約、`/diff`で変更確認を行う。
- `/review`は変更済みファイルをローカルでレビューする。`/review branch [base]`は現在ブランチを指定または検出したベースと比較する。

## 自動化

```text
kilo run "調査して結果を要約して"
kilo run --format json "テストを実行して失敗を報告して"
kilo run --auto "限定した自律タスク"
```

- `--format json`は機械処理用の生JSONイベントを出力する。
- `--auto`は危険な自動承認を有効にする。限定的な権限設定と隔離された実行環境でのみ使う。

## MCP

```text
kilo mcp add <name> --url https://example.com/mcp
kilo mcp list
kilo mcp auth <name>
kilo mcp logout <name>
```

- ローカルMCPは設定の`mcp.<name>`に`type: "local"`と`command`配列を指定する。
- リモートMCPは`type: "remote"`と`url`を指定する。認証ヘッダーやAPIキーをリポジトリ設定に直接保存しない。

## 診断

```text
kilo config check
kilo debug config
kilo debug paths
kilo debug skill
kilo help <command>
kilo --print-logs --log-level DEBUG
```

- 設定値の優先順位や展開結果を確認するときは`kilo debug config`を使う。
- 設定ディレクトリやデータ保存先は`kilo debug paths`で確認する。
- スキルが検出されない場合は`kilo debug skill`、TUI内では`/reload`を使う。
