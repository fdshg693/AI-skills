# review スキル

## 概要

- 現在のブランチ / 作業ツリーの**差分を読み取り専用でレビューする**スキル
- 3種類のレビューに対応する
  - **ブランチ間差分レビュー**: 現在のブランチ(マージ元)から指定したブランチ(マージ先)へPRを作成したと**仮定**した場合の差分レビュー
  - **未コミット変更レビュー**: staged/unstaged/untrackedの、まだコミットしていない変更のレビュー
  - **PRレビュー**: GitHub上の既存PR(番号・URL指定)の差分とコメントを `gh` で取得してのレビュー
- `checkout`/`merge`/`commit`/`push`/`add`/`stash` など、**git状態を変更する操作は一切行わない**。使うのは `diff`/`show`/`status`相当/`merge-base`/`rev-parse` のみ
- PRレビューでも、コメント投稿・approve・mergeなど**PRの状態を変更する操作は行わない**。使うのは `gh pr view`/`gh pr diff`/`gh api`(GET) のみ

## ディレクトリ構成

```
skills/review/
├── SKILL.md              # スキル本体。レビュー種別の判定と、両レビュー共通の注意事項
├── branch-diff.md         # ブランチ間差分レビューの詳細手順(SKILL.mdから参照される)
├── uncommitted-diff.md    # 未コミット変更レビューの詳細手順(SKILL.mdから参照される)
├── pr-review.md           # PRレビューの詳細手順(SKILL.mdから参照される)
├── diff_report.py         # ブランチ間差分を取得・出力するスクリプト
├── uncommitted_report.py  # 未コミット変更の差分を取得・出力するスクリプト
├── pr_report.py           # 既存PRの差分とコメント(COMMENTS.md)をghで取得・出力するスクリプト
├── diff_common.py         # 上記3スクリプトが共有するヘルパー(チャンク分割・.diffignoreフィルタ・INDEX.md生成など)
└── .diffignore            # レビュー対象から除外するパスパターン(.gitignoreと同じ書式)

testing/
├── setup_fixture.py       # 動作確認用の使い捨てgitリポジトリを testing/fixture-repo/ に作成するスクリプト
├── .gitignore             # fixture-repo/ を無視してリポジトリ本体のgit状態を汚さないようにする
└── fixture-repo/          # setup_fixture.py実行時に生成される検証用リポジトリ(gitignore済み)
```

## 使い方

Claude Codeに対して、以下のように自然文で依頼する。マージ先ブランチ・PR番号/URLの指定有無で、どのレビュー種別かが判定される(判断がつかない場合はユーザーに確認が入る)。

- ブランチ間差分レビュー
  - 「このブランチをmainにマージする想定でレビューして」
  - 「PRの差分を確認して」
  - 「mainへのマージ前チェックをして」
- 未コミット変更レビュー
  - 「今の変更をレビューして」
  - 「コミット前にチェックして」
  - 「git diffを見てレビューして」
- PRレビュー
  - 「PR #123をレビューして」
  - 「https://github.com/OWNER/REPO/pull/123 をレビューして」
  - 「このブランチのPRをレビューして」

裏側では `SKILL.md` が種別を判定し、`branch-diff.md` / `uncommitted-diff.md` / `pr-review.md` の手順に従って `diff_report.py` / `uncommitted_report.py` / `pr_report.py` を実行する。差分は `temp/review/` 配下に出力され、分割ファイルが複数生成された場合は `INDEX.md` を先に読んでから必要な `diff_XXXX.diff` だけを読む、という流れになる。詳細な出力仕様は各 `.md` ファイルおよびスクリプト冒頭のdocstringを参照。

### スクリプトを直接実行する場合

```bash
# ブランチ間差分(マージ元は省略時に現在のブランチ)
python skills/review/diff_report.py <target-branch> [--source <branch>] [--repo <path>] [--output-dir <dir>]

# 未コミット変更(staged + unstaged + untracked)
python skills/review/uncommitted_report.py [--repo <path>] [--output-dir <dir>]

# 既存PR(PR番号 / #番号 / PRのURL。省略時は現在のブランチのPR)
python skills/review/pr_report.py [<PR>] [--gh-repo OWNER/REPO] [--repo <path>] [--output-dir <dir>]
```

## 依存関係

- `.diffignore` に実パターン(コメント以外の行)を記載する場合のみ、`pathspec` パッケージが必要
  ```bash
  pip install pathspec
  ```
- `.diffignore` が存在しない、またはコメントのみの場合は何もフィルタされず、全差分が対象になる(依存パッケージが無くてもエラーにならない)
- PRレビュー(`pr_report.py`)のみ、[gh CLI](https://cli.github.com/) のインストールと認証(`gh auth login`)が必須。見つからない・未認証の場合はエラーで終了する(gitへのフォールバックはしない)

## スキルのテスト方法

スクリプト自体はClaude Codeを介さず、単体で動作確認できる。本体リポジトリのgit状態を汚さないよう、`testing/fixture-repo/` という使い捨てのgitリポジトリを使う(`testing/.gitignore` で除外済み)。

### 1. フィクスチャリポジトリを作成する

`testing/` ディレクトリで実行する。既存の `fixture-repo/` があれば削除してから作り直されるため、何度実行しても同じ状態から始められる。

```bash
cd skills/plugins/review/testing
python setup_fixture.py
```

作成されるシナリオ:

- **ブランチ間差分レビュー用**: `main` ブランチと `feature` ブランチ
  - `feature` ブランチでのみ `a.txt` の変更 / `feature.txt` の新規追加あり
- **未コミット変更レビュー用**(`feature` ブランチをcheckoutした状態):
  - staged変更(`b.txt`) / unstaged変更(`a.txt`) / 未追跡ファイル(`untracked.txt`) / 削除(`keep.txt`) / バイナリファイル(`bin.dat`) / `.diffignore`動作確認用ファイル(`pkg.lock`)

`--bulk N` を付けると、未追跡ファイルを `N` 件追加できる。チャンク分割・`INDEX.md` 生成(1ファイルあたり約300行を超えた場合の挙動)を試したい場合に使う。

```bash
python setup_fixture.py --bulk 40
```

### 2. 各スクリプトを実行して確認する

`testing/` ディレクトリから、`--repo fixture-repo` を指定して実行する。

```bash
# ブランチ間差分レビュー(feature -> main へのPRを想定)
python ../skills/review/diff_report.py main --repo fixture-repo

# 未コミット変更レビュー
python ../skills/review/uncommitted_report.py --repo fixture-repo
```

確認observationポイント:

- 分割ファイルが1つのみの場合は差分本文が標準出力にそのまま出ること
- `--bulk` で大量ファイルを追加した場合は `INDEX.md` が生成され、標準出力には `INDEX.md` のパスのみが出力されること
- `bin.dat`(バイナリ)が `original_lines`/`new_lines` = `N/A (binary)` として扱われ、差分本文が省略されること
- `keep.txt` の削除(unstaged)が `status: D` として検出されること

### 3. `.diffignore` によるフィルタを確認する

デフォルトの `skills/review/.diffignore` はコメントのみでフィルタが無効な状態。動作確認する場合は、一時的にパターンを追加してから再実行する。

```bash
# skills/review/.diffignore に一時的に追記する例
echo '*.lock' >> ../skills/review/.diffignore

python ../skills/review/uncommitted_report.py --repo fixture-repo
# -> pkg.lock が除外され、"除外: 1件" のように件数が報告されることを確認する

# 確認後は追記した内容を元に戻す(git checkout等ではなく、追記した行を手動で削除する)
```

### 4. 異常系を確認する

- `main` と `feature` に同一ブランチを指定 → 「差分はありません」で正常終了
- 存在しないブランチ名を指定 → エラーメッセージで終了(実際のgit操作は行われない)
- 独立した(共通祖先の無い)ブランチ間を指定 → merge-base取得エラーで終了

### 5. PRレビューを確認する

PRはフィクスチャで再現できないため、公開リポジトリの既存PRを指定して実行する。PRへの書き込みは行わないので、他人のリポジトリを指定しても問題ない。

```bash
# URL指定(分割1ファイル → 標準出力に差分本文)
python ../skills/review/pr_report.py https://github.com/cli/cli/pull/14517 --output-dir tmp-pr1

# 番号 + --gh-repo 指定(変更ファイルが多いPR → INDEX.md と COMMENTS.md のパスのみ出力)
python ../skills/review/pr_report.py "#14507" --gh-repo cli/cli --output-dir tmp-pr2
```

確認ポイント:

- 出力先に `COMMENTS.md`(PR本文・会話コメント・レビュー本文・インラインコメント)が生成されること
- 各ブロックの数値列が `additions` / `deletions` になっていること
- `gh` がPATHに無い場合、および不正なPR指定(`abc` 等)の場合にエラーで終了すること

### 後片付け

`testing/fixture-repo/` は `testing/.gitignore` で無視されているため放置してもよいが、不要であれば削除して構わない。再検証時は `setup_fixture.py` を再実行すれば作り直される。

```bash
rm -rf fixture-repo
```
