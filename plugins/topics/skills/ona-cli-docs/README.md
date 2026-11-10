# ona-cli-docs メンテナンス手順

`output/cli-excerpt.md` は、抽出元 llms.txt（Ona公式ドキュメントの索引。[ona-docs](../ona-docs/SKILL.md) スキルが24時間おきに再取得する `output/docs/llms.txt`）から、Ona公式CLI（`ona`コマンド）に関するエントリを人手で抜粋した固定ファイルです。抽出元の実際のパスはこのディレクトリの直下にある **[config.yml](config.yml)** の `source` キーで定義されており、コード内にハードコードされていません。

このスキルは[vscode-copilot-docs](../../../../../copilot-plugins/meta/vscode-copilot-docs/README.md)（`vscode-docs`のllms.txtからCopilot関連だけを人手キュレーション＋ドリフト検知スクリプトで抜粋するパターン）を踏襲したものです。`ona-docs`が既に取得済みのllms.txtから抜粋するだけで、`ona --help`の実行結果を新規にキャプチャする方式（存在する場合）とは抽出方式が異なります。混同しないよう注意してください。

`check_cli_excerpt.py` / `generate_cli_excerpt.py` は PyYAML（`config.yml` の読み込み用）に依存します。素の `python` コマンドの環境には入っていないことがあるため、必ず **`uv run <スクリプト名>.py`** で実行してください（各ファイル先頭の PEP 723 インラインスクリプトメタデータで依存を宣言しているため、`uv run` 経由なら環境を問わず自動解決される）。`python <スクリプト名>.py` のように直接実行すると `ModuleNotFoundError: No module named 'yaml'` になり得る。

## なぜ必要か

- `cli-excerpt.md` はキーワードGrep＋人手レビューで作成したものであり、取りこぼしや誤字混入のリスクがある
- 抽出元の llms.txt は定期的に再取得されるため、ページの改名・削除により `cli-excerpt.md` が指す URL やタイトルが古くなる（drift する）ことがある

## 実行手順

1. **抽出元を最新化する**（推奨）

   [ona-docs](../ona-docs/SKILL.md) スキルの取得処理（`webref_cli.py download`）を実行する（24時間以内に取得済みならスキップされる）。抽出元の正確なパスは [config.yml](config.yml) を参照。

2. **検証スクリプトを実行する**

   ```
   uv run check_cli_excerpt.py
   ```

   `cli-excerpt.md` の各エントリを URL をキーに `llms.txt` と突き合わせ、以下を報告する。

   - `MISSING`: excerpt の URL が `llms.txt` に存在しない（ページが改名/削除された、または元々存在しなかった）
   - `TITLE MISMATCH`: 同じ URL が `llms.txt` に存在するが、タイトルが異なる
   - `DESCRIPTION DRIFT`（参考情報）: タイトル・URL は一致するが説明文が変わっている
   - `POSSIBLE ADDITIONS`（参考情報）: `llms.txt` 内で CLI 関連っぽいキーワード（`cli`/`terminal`等）を含むが excerpt に未収録のエントリ（簡易ヒューリスティックなので鵜呑みにせず人が判断する。例: "One-click" や "clients" のような部分文字列一致による誤検知が混じる）

   `MISSING` または `TITLE MISMATCH` が1件でもあれば終了コード1を返す。

3. **結果に対応する**

   - `MISSING` / `TITLE MISMATCH` があれば、`llms.txt` 側の該当行を確認し `output/cli-excerpt.md` を修正する（URL変更・タイトル変更・エントリ削除のいずれかで対応）
   - `POSSIBLE ADDITIONS` は人が内容を読んで「`ona`コマンドを実際に打つ場面の説明があるか」を基準に判断し、該当したものだけ `output/cli-excerpt.md` に追記する
   - 修正後は再度スクリプトを実行し、`OK` になることを確認する

## 補足

- このスクリプトはタイトル・URL・説明文の一致のみを検証する。「本当に Ona CLI に関連する内容か」という抽出範囲の妥当性そのものは判断しない
- `--excerpt` / `--source` オプションで対象ファイルを変更できる（`uv run check_cli_excerpt.py --help` 参照）
- `vscode-copilot-docs`の`verify_agent_relevance.py`（3方向のAIによる抽出範囲の妥当性チェック）に相当する仕組みはまだ用意していない。初版のキュレーション対象ページ数が少なく（5件）過剰な仕組みになるため。将来対象が広がった場合は追加を検討する

## `output/cli-excerpt.md` を下書きから自動生成する（任意・ゼロから作り直す場合）

`output/cli-excerpt.md` が存在しない、または大幅に作り直したい場合、`generate_cli_excerpt.py` で `llms.txt` 全エントリを AI モデル（`aim` CLI、`aim-cli` スキル参照）に判定させ、下書きの MD ファイルを生成できる。

```
uv run generate_cli_excerpt.py --out output/cli-excerpt.draft.md
```

- `generate_copilot_excerpt.py` と同じ設計方針で、**AI にエントリのリライトはさせない**。AI には「含めるエントリの URL 一覧」だけを出力させ、タイトル・説明文は必ず `llms.txt` から一字一句そのまま転記する
- 出力は必ず**未レビューの下書き**である旨を frontmatter とスクリプトの標準出力に明記する。`--out` で `output/cli-excerpt.md` 以外のパスを指定し、人がレビュー・修正してから正式な `output/cli-excerpt.md` に置き換えること。既に存在するファイルパスを `--out`（省略時のデフォルト）に指定した場合は `--force` を付けない限りエラーで終了する
- レビュー後は `check_cli_excerpt.py` を実行してタイトル・URL のずれがないことを確認してから正式ファイルとして採用する
- `--model` で判定に使うモデルを変更できる（`aim-cli` スキル参照。デフォルトは `minimax-m3`）。プロンプトは同階層の `prompts/prompt_generate_excerpt.md` に切り出してある
- `ona-docs`側の`llms.txt`は（vscode-docs側と異なり）ページ単位の`## Section`見出しをほとんど持たない（`## Docs`の1セクションにほぼ全件が入っている）。そのため下書き生成時のセクション分けはあまり意味を持たず、実質フラットなリストになる
