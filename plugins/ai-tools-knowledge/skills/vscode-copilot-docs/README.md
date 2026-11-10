# vscode-copilot-docs メンテナンス手順

`output/copilot-excerpt.md` は、抽出元 llms.txt（VS Code 公式ドキュメントの索引、[vscode-docs](../../../others/skills/vscode-docs/SKILL.md) スキルが24時間おきに再取得する）から GitHub Copilot 関連エントリを人手で抜粋した固定ファイルです。抽出元の実際のパスはこのディレクトリの直下にある **[config.yml](config.yml)** の `source` キーで定義されており、コード内にハードコードされていません（過去にリポジトリ再編でこのパスが追従できず参照が壊れた経緯があるため、ディレクトリを見ただけで抽出元が分かるようにしてある）。現在の `output/copilot-excerpt.md` は、この抜粋作業（LLM下書き→人手レビュー）が何らかの形で既に行われている前提のファイルです。ゼロから作り直したい場合（大幅な再編があり既存のキュレーションがほぼ使えなくなった場合など）は、下記の `generate_copilot_excerpt.py` で下書きを自動生成できます。

`check_copilot_excerpt.py` は SKILL.md からは呼び出されません。Claude がドキュメント質問に答えるたびに実行されるものではなく、**ユーザーが定期的に（例: 月1回、または vscode-docs 側の llms.txt を明示的に更新した後に）手動で実行して**、`copilot-excerpt.md` のタイトル・URL が抽出元とずれていないかを確認するためのスクリプトです。

この3スクリプト（`check_copilot_excerpt.py` / `generate_copilot_excerpt.py` / `extract_uncurated_entries.py`）と `verify_agent_relevance.py` は PyYAML（`config.yml` の読み込み用）に依存します。素の `python` コマンドの環境には入っていないことがあるため、必ず **`uv run <スクリプト名>.py`** で実行してください（各ファイル先頭の PEP 723 インラインスクリプトメタデータで依存を宣言しているため、`uv run` 経由なら環境を問わず自動解決される）。`python <スクリプト名>.py` のように直接実行すると `ModuleNotFoundError: No module named 'yaml'` になり得る。

## なぜ必要か

- `copilot-excerpt.md` は LLM の下書きを人手でレビューして作成したものであり、タイトルの言い換えや誤字混入のリスクがある
- 抽出元の llms.txt は定期的に再取得されるため、ページの改名・削除により `copilot-excerpt.md` が指す URL やタイトルが古くなる（drift する）ことがある

## 実行手順

1. **抽出元を最新化する**（推奨）

   [vscode-docs](../../../others/skills/vscode-docs/SKILL.md) スキルの取得スクリプトを実行する（24時間以内に取得済みならスキップされる）。抽出元の正確なパスは [config.yml](config.yml) を参照。

2. **検証スクリプトを実行する**

   ```
   uv run check_copilot_excerpt.py
   ```

   `copilot-excerpt.md` の各エントリを URL をキーに `llms.txt` と突き合わせ、以下を報告する。

   - `MISSING`: excerpt の URL が `llms.txt` に存在しない（ページが改名/削除された、または元々存在しなかった）
   - `TITLE MISMATCH`: 同じ URL が `llms.txt` に存在するが、タイトルが異なる
   - `DESCRIPTION DRIFT`（参考情報）: タイトル・URL は一致するが説明文が変わっている
   - `POSSIBLE ADDITIONS`（参考情報）: `llms.txt` 内で Copilot/AI 関連っぽいキーワードを含むが excerpt に未収録のエントリ（簡易ヒューリスティックなので鵜呑みにせず人が判断する）

   `MISSING` または `TITLE MISMATCH` が1件でもあれば終了コード1を返す。

3. **結果に対応する**

   - `MISSING` / `TITLE MISMATCH` があれば、`llms.txt` 側の該当行を確認し `output/copilot-excerpt.md` を修正する（URL変更・タイトル変更・エントリ削除のいずれかで対応）
   - `POSSIBLE ADDITIONS` は人が内容を読んで GitHub Copilot 関連と判断できたものだけ `output/copilot-excerpt.md` に追記する
   - 修正後は再度スクリプトを実行し、`OK` になることを確認する

## 補足

- このスクリプトはタイトル・URL・説明文の一致のみを検証する。「本当に GitHub Copilot に関連する内容か」という抽出範囲の妥当性そのものは判断しない
- `--excerpt` / `--source` オプションで対象ファイルを変更できる（`uv run check_copilot_excerpt.py --help` 参照）

## `output/copilot-excerpt.md` を下書きから自動生成する（任意・ゼロから作り直す場合）

`output/copilot-excerpt.md` が存在しない、または大幅に作り直したい場合、`generate_copilot_excerpt.py` で `llms.txt` 全エントリを AI モデル（`aim` CLI、`aim-cli` スキル参照）に判定させ、下書きの MD ファイルを生成できる。

```
uv run generate_copilot_excerpt.py --out output/copilot-excerpt.draft.md
```

- `verify_agent_relevance.py` と同じ設計方針で、**AI にエントリのリライトはさせない**。AI には「含めるエントリの URL 一覧」だけを出力させ、タイトル・説明文は必ず `llms.txt` から一字一句そのまま転記する（AI が言い換えて `check_copilot_excerpt.py` の TITLE MISMATCH を誘発するのを防ぐため）
- 出力は必ず**未レビューの下書き**である旨を frontmatter とスクリプトの標準出力に明記する。`--out` で `output/copilot-excerpt.md` 以外のパスを指定し、人がレビュー・修正してから正式な `output/copilot-excerpt.md` に置き換えること。既存の `output/copilot-excerpt.md` を誤って上書きしないよう、既に存在するファイルパスを `--out`（省略時のデフォルト）に指定した場合は `--force` を付けない限りエラーで終了する
- レビュー後は `check_copilot_excerpt.py` を実行してタイトル・URL のずれがないことを確認してから正式ファイルとして採用する
- `--model` で判定に使うモデルを変更できる（`aim-cli` スキル参照。デフォルトは `mini-m3`）。プロンプトは同階層の `prompts/prompt_generate_excerpt.md` に切り出してある

## 抽出範囲の妥当性を確認する（任意・AIモデルによる二次チェック）

`check_copilot_excerpt.py` は「excerpt に載っているエントリのタイトル・URL が壊れていないか」しか見ない。「excerpt に載っていないエントリを正しく除外できているか」（キーワードヒューリスティックの誤検知・見逃し）を確認したい場合は、`verify_agent_relevance.py` を使う。

```
uv run verify_agent_relevance.py
```

内部で以下を順に実行する。

1. `check_copilot_excerpt.py` を実行し、drift（MISSING/TITLE MISMATCH）があれば中断する
2. `extract_uncurated_entries.py` を実行し、excerpt に含まれないエントリを `llms.txt` のセクション名付きで抽出、キーワードヒューリスティックで「エージェント関連候補」「非該当」の2ファイルに分ける（`output/verification/uncurated_agent_candidates.md` / `uncurated_non_candidates.md`）
3. 以下の3ファイルをそれぞれ丸ごと `aim` CLI（`aim-cli` スキル参照）に渡し、AIモデルに自然言語で判定させる（計3回呼び出し）
   - `output/copilot-excerpt.md`（キュレーション済みファイル自体） → 本当に GitHub Copilot / AI エージェント関連と言える内容だけが載っているか（誤って載っているエントリがないか）
   - 候補ファイル（`uncurated_agent_candidates.md`） → キーワードにたまたま一致しただけの false positive がないか
   - 非該当ファイル（`uncurated_non_candidates.md`） → ヒューリスティックが見逃した false negative がないか
   - 結果はそれぞれ `output/verification/llm_judgement_excerpt.md` / `llm_judgement_agent_candidates.md` / `llm_judgement_non_candidates.md` に出力される

各呼び出しのプロンプトは `verify_agent_relevance.py` に埋め込まず、同階層の `prompt_excerpt.md` / `prompt_agent_candidates.md` / `prompt_non_candidates.md`（英語で記述）に切り出してある。プロンプトの文言だけを調整したい場合はこれらの Markdown ファイルを直接編集すればよく、スクリプト本体の変更は不要。

このスクリプトは判定結果をファイル出力するところまでがスコープで、`output/copilot-excerpt.md` の更新は行わない。結果ファイルを読んで実際に追記・修正するかどうかは人が判断すること。`output/verification/` は再生成される作業用フォルダなので `.gitignore` されている。

`--model` で `aim` に渡すモデルを変更できる（`aim-cli` スキル参照。デフォルトは `mini-m3`）。
