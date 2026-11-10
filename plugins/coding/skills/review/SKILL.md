---
name: review
description: コードの差分を読み取り専用でレビューする。(1) 現在のブランチから指定したマージ先ブランチへPRを作成したと仮定してのブランチ間差分レビュー、(2) まだコミットしていない変更(staged/unstaged/untrackedファイル)のレビュー、(3) GitHub上の既存PR(番号・URL指定)の差分とコメントをgh CLIで取得してのPRレビュー、に対応する。実際のgit操作(checkout/merge/commit/push/add/stash等)やPRへのコメント投稿・approve等、状態を変更する操作は一切行わない。「このブランチをmainにマージする想定でレビューして」「mainへのマージ前チェックをして」のようなマージ先ブランチが分かっている差分レビュー、「今の変更をレビューして」「コミット前にチェックして」「git diffを見てレビューして」のような作業ツリーの変更レビュー、「PR #123をレビューして」「このPRのURLを見て」「このブランチのPRをレビューして」のような既存PRのレビュー、いずれの依頼にも使う。
argument-hint:
  [
    merge先ブランチ名 | PR番号/PRのURL (省略可。未コミット変更のレビューでは不要),
  ]
arguments: [target]
allowed-tools: Bash(python plugins/review/skills/review/*.py *)
# Python依存: pathspec (`.diffignore` で除外パターンを指定する場合のみ必要。事前に `pip install pathspec` でグローバルインストールしておくこと)
# PRレビューのみ gh CLI(認証済み)が必須。無い場合はエラーで終了する
meta:
  tag: []
  requires_repo_tools: none
  requires_env: none
  dependencies: pathspec, git, python, gh
  requires_install: pathspec
  requires_hooks: none
  requires_skills: none
  status: stable
  description: no description
  version: 1.1.1
---

コードの差分をレビューする。**実際にgit状態を変更する操作(checkout/merge/commit/push/add/stashなど)や、PRへのコメント投稿・approve・mergeなどは一切行わない。行うのは既存の状態の読み取り(diff/status/show、PRの閲覧)のみ。**

## レビュー種別を判定する

依頼内容から、以下のいずれかを判定する。判断がつかない場合はユーザーに確認する(推測で決めない)。特に「PRの差分を確認して」のようにPR番号もマージ先ブランチも無い依頼は、既存PRのレビューか、PRを出す前提のブランチ間差分レビューかを確認する。

- **PRレビュー**: GitHub上に既に存在するPRの差分とコメントをレビューする。`$target` がPR番号(`123` / `#123`)またはPRのURLの場合、または「このブランチのPRをレビューして」のように既存PRを指している場合。
  → 詳細手順は同階層の `pr-review.md`(`${CLAUDE_SKILL_DIR}/pr-review.md`)を参照して従う。

- **ブランチ間差分レビュー**: 現在のブランチ(マージ元)から指定したブランチ(マージ先)へPRを作成したと**仮定**した場合の差分をレビューする。マージ先ブランチが分かっている/指定されている、または「マージ前チェック」のように依頼されている場合。
  → 詳細手順は同階層の `branch-diff.md`(`${CLAUDE_SKILL_DIR}/branch-diff.md`)を参照して従う。

- **未コミット変更レビュー**: 現在の作業ツリーにある、まだコミットしていない変更(staged/unstaged/untrackedファイル)をレビューする。マージ先ブランチやPRの指定がなく、「今の変更を見て」「コミット前にレビューして」のように依頼されている場合。
  → 詳細手順は同階層の `uncommitted-diff.md`(`${CLAUDE_SKILL_DIR}/uncommitted-diff.md`)を参照して従う。

## 全レビューに共通する事項

- 差分取得スクリプトは読み取り専用のコマンドのみを使う(ブランチ間/未コミットは git、PRは gh)。
- 差分は `temp/review/` 配下に出力される。分割ファイルが複数生成された場合は、まず `INDEX.md` を読んで全体像(ファイル別のstatus/行数)を把握してから、必要な `diff_XXXX.diff` だけを個別に読む。1ファイルのみで済んだ場合は標準出力に差分本文がそのまま出るため、追加でファイルを読む必要はない。
- 同階層の `.diffignore` に記載したパターン(`.gitignore` と同じ書式)にマッチするファイルは、レビュー対象から自動的に除外される。
- 取得した差分は、通常のコードレビューと同じ観点でレビューする(バグ・既存動作への影響・命名やスタイルの一貫性・テストの有無・意図しないファイルの混入など)。各ブロックの数値列(`original_lines` / `new_lines`、PRレビューでは `additions` / `deletions`)は変更規模の把握に使う。
- 結果を報告する際は、以下を明記する。
  - どの種別のレビューか、および状態を変更する操作は行っていないこと
  - 差分ファイルの出力先ディレクトリのパス
  - `.diffignore` によって除外されたファイルがあれば、その件数
