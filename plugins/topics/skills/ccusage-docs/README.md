# ccusage-docs

ccusage の根拠を2系統まとめたスキル。`SKILL.md` はルーター。旧 `ccusage-cli-docs` はここに統合した。

| 根拠                                                 | 手順                                 | 成果物                                    |
| ---------------------------------------------------- | ------------------------------------ | ----------------------------------------- |
| 公式サイト（ccusage.com）の llms.txt / llms-full.txt | [official-docs.md](official-docs.md) | `output/llms.txt`, `output/llms-full.txt` |
| 実 CLI の `--help` キャプチャ                        | [cli-help.md](cli-help.md)           | `output/cli/*.yaml`                       |

CLI 側の抽出方式は `claude-cli-docs` と同じ「実 CLI の `--help` キャプチャ」であり、[ona-cli-docs](../ona-cli-docs/SKILL.md) のような llms.txt 抜粋とは異なる。

## 公式サイト側

- `ccusage.com` の `llms-full.txt` は `# タイトル` / `Source: URL` ではなく、VitePress のページ連結（`---\nurl: /path.md\n---` のあと ATX h1）である。`extract_doc_section.py` と `grep_doc_sections.py` はこの形式向けに正規表現・境界判定を差し替えてある。テンプレート既定の `Source:` パターンのままではページを切れない
- `inspect-markers` は本文中のシェルコメント（`# Clone the repository` 等）を h1 と誤認して Inconsistent と出すことがある。抽出のアンカーは `url:` 行なので、試し抽出（`guide` / `guide/daily-reports` / `guide/cost-modes`）で本文が切れることを確認すればよい
- 索引 `llms.txt` は約75行で全エントリが ccusage 本体の対象。200行閾値にも「ごく一部だけが関連」条件にも当たらないため excerpt は作っていない
- ダウンロードは UTF-8 を明示している。サーバーが charset を付けない場合に requests が Latin-1 と誤認し、引用符や絵文字が文字化けするため

```
python webref_cli.py download
python webref_cli.py download --force
```

## CLI 側

- リポジトリルートの `package.json` に `ccusage` がある。`pnpm install` 後、`pnpm exec ccusage` で呼べること
- 生成スクリプトは PyYAML に依存する。必ず `uv run generate_ccusage_help_yaml.py` で実行する（PEP 723）
- ヘルパーは gunshi の `USAGE:` / `COMMANDS:` / `OPTIONS:` 向け。`For more info, run any command with the --help flag:` 以下の例示行はコマンド一覧に入れない
- 実行バイナリはリポジトリの `node_modules/.bin/ccusage`（または `pnpm exec ccusage`）を優先し、グローバル PATH の古い版を拾わない
- YAML は `output/cli/` に置く。公式サイトの `output/llms.txt` 等とファイル名が衝突しないようにしている

```
uv run generate_ccusage_help_yaml.py
uv run generate_ccusage_help_yaml.py --all
uv run generate_ccusage_help_yaml.py --all --force
```

- 既定: トップレベルだけ `output/cli/help_result.yaml`（24時間以内の取得ならスキップ、`--force` で上書き）
- `--all`: 第一階層コマンドごとに `output/cli/<name>.yaml`。そのコマンドがさらにサブコマンドを持つ場合は `subcommands:` に入れ子で格納し、`output/cli/index.yaml` に一覧を書く
