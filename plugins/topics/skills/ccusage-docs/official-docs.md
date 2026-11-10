# 公式サイト（ccusage.com）の参照手順

学習データの記憶ではなく、`ccusage.com` の最新ドキュメントを根拠にする。

## 取得ファイル

- `output/llms.txt`（取得元: `https://ccusage.com/llms.txt`）: 全ページの索引。約75行、`## Table of Contents` 配下にカテゴリ見出しつき。各エントリは `- [Title](/path.md)` の相対リンク（説明文なし）。索引は小さく全件がこのスキルの対象なので抜粋(excerpt)は作っていない
- `output/llms-full.txt`（取得元: `https://ccusage.com/llms-full.txt`）: 全文ダンプ。ページ境界は `# タイトル`/`Source: URL` ではなく VitePress の YAML フロントマター（`url: /path.md`）。`extract-section` / `grep-sections` はこの形式向けに適応済み

索引のカテゴリ目安: `Introduction`（導入・インストール）、`Usage Views`（daily/weekly/monthly/session と all-sources）、`Data Sources`（各 CLI のデータ場所・ソース固有の注意）、`Configuration`（CLIオプション・環境変数・設定ファイル・cost modes）、`Integration`（JSON出力）、`Community`、`Other`（blocks、statusline、削除済み live monitoring 等）

## 手順

1. **関連ページを探す**

   - `output/llms.txt` を Grep/Read し、質問に関連する `- [Title](/path.md)` を特定する
   - ページが分からずキーワードだけある場合は、全文ダンプを URL 付きで検索する:

     ```sh
     python "${CLAUDE_SKILL_DIR}/webref_cli.py" grep-sections "検索パターン" --ignore-case
     ```

     ヒットは `== /guide/....md (Title) ==` の下に行番号つきで出る。そのパスを次の抽出に使う

2. **該当ページの本文を抽出する**

   ```sh
   python "${CLAUDE_SKILL_DIR}/webref_cli.py" extract-section <URL または パス> [<URL または パス>...]
   ```

   - 例: `python "${CLAUDE_SKILL_DIR}/webref_cli.py" extract-section guide/daily-reports guide/cost-modes`
   - パスは `llms.txt` のリンク（`/guide/daily-reports.md`）から先頭の `/` と末尾の `.md` を除いたもの。フルURL (`https://ccusage.com/guide/daily-reports`) でもよい
   - `output/temp/<slug>.txt` に本文全文が書き出される（本文が `--summarize-threshold` 既定6000文字を超える場合は `aim` CLI で要約した `output/temp/<slug>.summary.md` も追加で生成される。要約時も全文ファイルへのパスは必ず案内される）
   - 見つからない場合は `output/llms.txt` に載っていない可能性がある。その旨を伝えた上で WebFetch で `https://ccusage.com/` 配下を直接参照してもよい

3. **回答する**

   - 参照した本文に基づいて回答し、参照したURL（抽出結果の `Source:` 行）を明示する

## 補足

- スクリプトは `${CLAUDE_SKILL_DIR}/output/` を読み書きする。ダウンロードは24時間以内に取得済みならスキップされる（`--force` で強制再取得、`python "${CLAUDE_SKILL_DIR}/webref_cli.py" download --force`）
- `output/temp/` は `extract-section` の作業用一時ファイル置き場（都度上書きされる想定、gitignore済み）
