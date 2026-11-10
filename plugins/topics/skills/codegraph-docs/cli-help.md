# `codegraph` コマンドの `--help` 参照手順

学習データの記憶や公式 docs の CLI 節ではなく、インストール済み `codegraph --help` の実際の出力を根拠にする。公式 `output/reference/cli.md` はリリースより遅れたり、この環境の CLI に無いコマンドを残したりすることがある。

## 手順

1. **`${CLAUDE_SKILL_DIR}/output/cli/help_result.yaml` を Read/Grep して回答する**

   - トップレベルは `usage` / `description` / `commands`（一覧）/ `options`
   - 各サブコマンドのフラグは `subcommands.<名前>`（例: `subcommands.explore`、`subcommands.files`）。`invocation` / `usage` / `options` / `arguments` を根拠にする
   - 回答には、どのオプション/サブコマンドを参照したかを明示する（例: `--max-files` は `codegraph explore` の説明に基づく、など）
   - `hidden: true` のエントリ（例: `serve`）はトップレベルの `Commands:` に出ないが、実在するコマンド

2. **YAML に無い・古いと感じたら、その場の `--help` か再生成で確認する**

   - `codegraph <サブコマンド> --help` を実行し、出力をそのまま読んで回答する
   - 構造化して残したい場合は `uv run "${CLAUDE_SKILL_DIR}/generate_codegraph_help_yaml.py" --force`

## 補足

- スクリプトはこのスキルのディレクトリを基準に `output/cli/` を読み書きする（公式 docs の `output/*.md` とは混ぜない）
- 既定実行は `codegraph --version`、`codegraph --help`、各サブコマンドの `--help` を取り、1ファイルに書き出す。トップレベルだけ欲しいときは `--top-only`
- CodeGraph の `--help` は commander.js 製。各エントリは「インデント2の名前行＋同行または深いインデントの説明行」。パーサーは説明行を空白1つで連結して1つの `description` にする
- `codegraph` が無い/失敗する環境ではスクリプトの実行が失敗するが、その場合はバンドル済みの `output/cli/help_result.yaml`（同梱の生成済みスナップショット）をそのまま使う
- `output/cli/help_result.yaml` は生成物だが、`codegraph` CLI が使えない環境でも参照できるようリポジトリにコミットして同梱している
- 生成スクリプトは PyYAML に依存する。素の `python` に入っていないことがあるため、`uv run` 経由で実行する（ファイル先頭の PEP 723 インラインメタデータで依存を宣言している）
