# `ccusage` コマンドの `--help` 参照手順

学習データの記憶ではなく、`ccusage --help` の実際の出力を根拠にする。既定の `ccusage daily` 等は検出できた全ソースを集計する。1ソースに絞る形は `ccusage <source> <report>`（例: `ccusage claude daily`）。

## 手順

1. **`${CLAUDE_SKILL_DIR}/output/cli/help_result.yaml` を Read/Grep して回答する**

   - `usage` / `description` / `commands` / `options` を検索し、該当エントリの `description` を根拠として提示する
   - 回答には、どのオプション/サブコマンドを参照したかを明示する（例: `--sections` オプションの説明に基づく、など）
   - どの YAML があるかは `output/cli/index.yaml` の `commands` 一覧でも確認できる（`--all` 生成後に存在）

2. **サブコマンド固有の詳細は生成済み YAML、または `ccusage <サブコマンド> --help` で確認する**

   トップレベルの `ccusage --help` には `commands` の一行説明しかない（`daily` / `blocks` / `claude` など）。それぞれの詳しいオプションを聞かれたら、以下のいずれかで確認する。

   - `${CLAUDE_SKILL_DIR}/output/cli/<コマンド>.yaml` を Read する（例: `output/cli/daily.yaml`、`output/cli/claude.yaml`）。ソース系コマンドは入れ子の `subcommands:`（例: `output/cli/claude.yaml` の `subcommands.daily`）に `ccusage claude daily --help` 相当が入る
   - ファイルが無い、または中身が足りない場合は `ccusage <サブコマンド> --help` を実行し、出力をそのまま読んで回答する
   - 構造化して残したい場合は `uv run "${CLAUDE_SKILL_DIR}/generate_ccusage_help_yaml.py" --all --force` で全コマンド分を再生成する

## 補足

- スクリプトはこのスキルのディレクトリを基準に `output/cli/` を読み書きする（公式サイトの `output/llms.txt` 等と混ぜない）
- 既定実行は `ccusage --version` と `ccusage --help` だけを取り、`output/cli/help_result.yaml` に書き出す。全サブコマンド分は `--all`
- ccusage の `--help` は gunshi 製で、`USAGE:` / `COMMANDS:` / `OPTIONS:`（すべて大文字）のセクション構造。Claude Code（commander.js）や Codex（clap）とはレイアウトが異なる
- `ccusage` が無い/失敗する環境ではスクリプトの実行が失敗するが、その場合はバンドル済みの `output/cli/*.yaml`（同梱の生成済みスナップショット）をそのまま使う
- `output/cli/*.yaml` は生成物だが、`ccusage` CLI が使えない環境でも参照できるようリポジトリにコミットして同梱している
- 生成スクリプトは PyYAML に依存する。素の `python` に入っていないことがあるため、`uv run` 経由で実行する（ファイル先頭の PEP 723 インラインメタデータで依存を宣言している）
