---
# 詳細なオプションは command-guide.md、現在のCLIコマンドは output/help_result.yaml を参照する。
name: kilo-cli-guide
description: Use when working with the Kilo CLI, including command options, subcommands, installation, automation, configuration, and troubleshooting.
meta:
  tag: []
  requires_repo_tools: none
  requires_env: none
  dependencies: none
  requires_install: none
  requires_hooks: none
  requires_skills: none
  status: experimental
  description: Kilo CLI usage guide
  version: 1.0.1
---

# Kilo CLI を使う

Kilo CLIを端末から安全に導入、設定、対話利用、自動実行、診断するためのガイド。

## 使う場面

- Kilo CLIを初めて導入し、プロバイダーを接続するとき
- プロジェクトで対話的にエージェントを使うとき
- CIなどで`kilo run`を非対話実行するとき
- モデル、権限、MCP、セッションを設定または調査するとき

## 基本フロー

1. CLIが無ければ`npm install -g @kilocode/cli`で導入し、`kilo --version`で確認する。
2. 作業対象のプロジェクトルートで`kilo`を起動する。初回はTUI内の`/connect`でプロバイダーを接続する。
3. 対話中は`/models`、`/agents`、`/sessions`、`/diff`を使い、変更とセッションを確認する。
4. 詳細不明なサブコマンドは推測せず、`kilo help <command>`または[command-guide.md](command-guide.md)を参照する。
5. `output/help_result.yaml`をRead/Grepして、インストール済みCLIのコマンド、位置引数、オプションを確認する。生成は24時間キャッシュされるため、直後の再読込はCLIを再実行しない。
6. 仕様の鮮度が重要なときは`kilo-code-docs`スキルで公式ドキュメントを確認する。

## CLI ヘルプカタログ

- `python "${CLAUDE_SKILL_DIR}/generate_kilo_help_yaml.py"`を実行すると、`kilo --version`と`kilo --help`を`output/help_result.yaml`へ構造化して保存する。
- 詳しいサブコマンドのフラグは`kilo <subcommand> --help`で確認する。保存が必要なら、ヘルプ出力をファイルに保存し、`--help-file <path> --output output/<subcommand>.yaml`で変換する。
- `kilo`が実行できない環境では生成は失敗するが、コミット済みの`output/help_result.yaml`を参照する。

## 対話利用

- 通常は`kilo`でTUIを起動する。最後の同一ワークスペースのセッションを続けるには`kilo --continue`を使う。
- モデルやエージェントを開始時に固定する必要がある場合は、`kilo --model provider/model --agent <agent>`を使う。
- 設定・スキル・エージェント・コマンドをディスクから読み直すには`/reload`を使う。実行中セッションがあると拒否されるため、完了または中断後に実行する。
- `/auto-approve`や`--auto`は明示的に拒否されていない権限を自動承認する。対象プロジェクトと権限設定を確認しない限り有効化しない。

## 非対話実行

- 単発タスクは`kilo run "<指示>"`で実行する。構造化されたイベントが必要な自動化では`--format json`を付ける。
- CIなど人が承認できない環境では`kilo run --auto "<指示>"`を使う。`--auto`なしの非対話実行は、承認が必要な操作を拒否して失敗する。
- `--auto`を使う前に、プロジェクトの`permission`設定を最小権限にし、実行するリポジトリとプロンプトを限定する。秘密情報をプロンプト、ログ、コミット対象の設定へ書き込まない。
- 終了コードは成功が`0`、タイムアウトが`124`、初期化・実行・要求エラーが`1`である。CIではこの値を失敗判定に使う。

## 設定と認証

- 資格情報の追加は通常`/connect`または`kilo auth login`を使う。登録状況は`kilo auth list`で確認する。
- グローバル設定は`~/.config/kilo/kilo.jsonc`、プロジェクト設定は`kilo.jsonc`または`.kilo/kilo.jsonc`を推奨する。プロジェクト設定が優先される。
- APIキーなどの環境変数参照`{env:NAME}`は、グローバル設定などの信頼済み設定でのみ解決される。リポジトリにコミットするプロジェクト設定へ秘密情報を置かない。
- 設定を編集した後はCLIを再起動し、`kilo config check`または`kilo debug config`で検証する。

## MCP と診断

- MCPサーバーは`mcp`設定または`kilo mcp add`で追加し、`kilo mcp list`で状態を確認する。TUIでは`/mcps`で有効・無効を切り替える。
- MCPツールはコンテキストを消費するため、必要なサーバーだけを有効にする。MCPツールの権限は`{server}_{tool}`形式の名前で設定する。
- パス、設定、利用可能なスキルの調査には順に`kilo debug paths`、`kilo debug config`、`kilo debug skill`を使う。
- バージョン確認、更新、問題の再現時は`kilo --version`、`kilo upgrade`、`kilo --print-logs --log-level DEBUG`を使う。

## 参照

- [command-guide.md](command-guide.md) - よく使うコマンドと用途
- [output/help_result.yaml](output/help_result.yaml) - `kilo --help`から生成したコマンドカタログ
- https://kilo.ai/docs/code-with-ai/platforms/cli
- https://kilo.ai/docs/code-with-ai/platforms/cli-reference
- https://kilo.ai/docs/automate/mcp/using-in-cli

公式ページの確認日: 2026-09-16
