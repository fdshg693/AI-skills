---
name: pr-check
description: PRの作成・状態確認・レビュー依頼・GitHub Actions操作を行う
allowed-tools: Bash(gh *) Bash(git *) Bash(uv run ${CLAUDE_SKILL_DIR}/*.py *) Bash(python ${CLAUDE_SKILL_DIR}/*.py *)
meta:
  tag: []
  requires_repo_tools: none
  requires_env: none
  dependencies: gh, git, uv
  requires_install: none
  requires_hooks: none
  requires_skills: none
  status: stable
  description: PRの作成・状態確認・Copilotレビュー依頼・マージ・GitHub Actions操作
  version: 1.1.0
---

# PR確認・管理スキル

現在のブランチに関連するPull Requestの作成・確認・レビュー依頼・マージ、およびGitHub Actionsの実行・結果取得等をユーザーのリクエストに応じて行う。

同梱スクリプトは `uv run` で実行する（標準ライブラリだけを使い、PEP 723 のメタデータで依存なしと宣言している）。uv が無い環境では `uv run` を `python` に置き換えてよい。

## 現在の状態

- ブランチ: !`git branch --show-current`
- upstream との差: !`git status -sb | head -n 1`（`[ahead N]` は未push。upstream が出なければ未設定）
- リポジトリ: !`gh repo view --json nameWithOwner --jq .nameWithOwner`

### PR一覧（現在のブランチから）

!`gh pr list --head "$(git branch --show-current)" --state open --json number,title,state,url,createdAt,reviewDecision,baseRefName --jq '.[] | "PR #\(.number): \(.title)\n  base: \(.baseRefName) | 状態: \(.state) | レビュー: \(.reviewDecision // "未レビュー")\n  URL: \(.url)\n  作成日: \(.createdAt)"'`

## 対象PRの特定

現在のブランチから**OPENなPRが複数ある場合は、作業を進める前に必ずユーザーにどのPRを対象とするかを確認する**。同時に複数PRを扱うユースケースは想定しない。

- 確認時は PR番号・タイトル・base ブランチを提示する（上の「PR一覧」の出力をそのまま引用すればよい）
- 例: 「現在のブランチから以下のOPEN PRが見つかりました。どれを対象にしますか？ #123 "feat: ...", #125 "fix: ..."」
- PRが1件のみの場合は確認不要でそのPRを対象とする

## PR詳細取得コマンド

対象PR番号を `<N>` として、必要なものだけ実行する。

| 目的                                         | コマンド                                                    |
| -------------------------------------------- | ----------------------------------------------------------- |
| PR詳細（本文・マージ可否等）                 | `uv run ${CLAUDE_SKILL_DIR}/pr-detail.py <N> view`          |
| レビューコメント（コード行指摘）             | `uv run ${CLAUDE_SKILL_DIR}/pr-detail.py <N> comments`      |
| レビュー（承認/変更リクエスト）              | `uv run ${CLAUDE_SKILL_DIR}/pr-detail.py <N> reviews`       |
| 任意の組み合わせ（スペース区切りで複数指定） | `uv run ${CLAUDE_SKILL_DIR}/pr-detail.py <N> view comments` |
| 明示的に全て取得                             | `uv run ${CLAUDE_SKILL_DIR}/pr-detail.py <N> all`           |
| 引数省略時も3つ全て取得                      | `uv run ${CLAUDE_SKILL_DIR}/pr-detail.py <N>`               |
| CIチェック状態（出力が大きいので必要時のみ） | `gh pr checks <N>`                                          |

## PR作成

`pr-create.py` を使う。事前に未コミット変更・既存PR・サブモジュールのポインタ先・リモートpush状態をチェックする。

**リポジトリに PR 手順の文書（`CONTRIBUTING.md`、ブランチ運用・PR 手順のドキュメントなど）があれば、そちらの手順・順番・マージ方式を優先する。** 例えばサブモジュールを持つリポジトリでは、サブモジュールの PR を先にマージしてからアンブレラの PR を出す、といった順番の決まりがあることが多い。

| 目的                                             | コマンド                                                                                             |
| ------------------------------------------------ | ---------------------------------------------------------------------------------------------------- |
| PR作成（merge でない commit 1 件だけのとき）     | `uv run ${CLAUDE_SKILL_DIR}/pr-create.py`                                                            |
| タイトル/本文指定（commit が複数あるときは必須） | `uv run ${CLAUDE_SKILL_DIR}/pr-create.py --title "..." --body "..."`                                 |
| 本文をファイルから                               | `uv run ${CLAUDE_SKILL_DIR}/pr-create.py --title "..." --body-file .github/pull_request_template.md` |
| ドラフトPR                                       | `uv run ${CLAUDE_SKILL_DIR}/pr-create.py --draft --title "..."`                                      |
| baseブランチ指定                                 | `uv run ${CLAUDE_SKILL_DIR}/pr-create.py --base develop --title "..."`                               |

- 作成は**ユーザーの明示的な指示**があった場合のみ実行する
- 大きな変更の場合は先に `git log --oneline origin/<base>..HEAD` でコミット一覧を確認して、タイトル・本文の方針をユーザーに提示してから実行する
- **タイトルは PR 全体を表すものを `--title` で渡す。** `--title` を省けるのは base との差分が merge でない commit 1 件だけのとき（その件名を使う）。commit が複数ある、または最新がマージ commit のときはスクリプトがエラーで止まる
- 本文を書くとき、`review` スキルで差分レビューをしていれば、その結果（実行したテスト・確認した点・残っている注意点）を本文の「確認したこと」に入れる
- スクリプトの事前チェック:
  - ポインタが変わったサブモジュールの commit が、そのサブモジュールのリモートのどのブランチにも無ければ中断する（サブモジュール内で `git fetch` してから `git branch -r --contains` で確認する）。先にサブモジュールを push する。確認を飛ばすのは `--skip-submodule-check`
  - ブランチがリモートに無い、または upstream より先行していれば push する。upstream にローカルに無い commit があれば中断する

## GitHub Actions

`pr-actions.py` でワークフロー実行の一覧・詳細・失敗ログ取得・手動実行を行う。ログ全量は巨大になるため `failed` を優先利用する。

| 目的                              | コマンド                                                                   |
| --------------------------------- | -------------------------------------------------------------------------- |
| 直近20件のrun一覧（現在ブランチ） | `uv run ${CLAUDE_SKILL_DIR}/pr-actions.py list`                            |
| 別ブランチのrun一覧               | `uv run ${CLAUDE_SKILL_DIR}/pr-actions.py list <branch>`                   |
| ワークフローで絞ったrun一覧       | `uv run ${CLAUDE_SKILL_DIR}/pr-actions.py list <branch> --workflow <name>` |
| 対象PRのHEADコミットに紐づくrun   | `uv run ${CLAUDE_SKILL_DIR}/pr-actions.py pr <N>`                          |
| run詳細（ジョブ毎の成否）         | `uv run ${CLAUDE_SKILL_DIR}/pr-actions.py view <run_id>`                   |
| 失敗ログのみ（推奨）              | `uv run ${CLAUDE_SKILL_DIR}/pr-actions.py failed <run_id>`                 |
| ワークフロー手動実行              | `uv run ${CLAUDE_SKILL_DIR}/pr-actions.py run <workflow> [ref]`            |
| 完了まで追跡                      | `uv run ${CLAUDE_SKILL_DIR}/pr-actions.py watch <run_id>`                  |

- 手動実行は対象ワークフローに `workflow_dispatch` トリガーが必要
- 手動実行も**ユーザーの明示的な指示**を前提とする

## Copilot レビュー

GitHub Copilot にコードレビューを依頼する。**個人アカウントのリポジトリでは Copilot を Collaborator として追加できない**ため、`gh pr edit --add-reviewer` や requested_reviewers API による正規のレビュアー指定は使えない（422で失敗する）。代わりに PRコメントで `@copilot review` メンションする方式を使う。

| 目的                       | コマンド                                                                               |
| -------------------------- | -------------------------------------------------------------------------------------- |
| Copilotレビュー依頼        | `gh pr comment <N> --body "@copilot review"`                                           |
| レビュー状態（依頼中含む） | `gh pr view <N> --json reviewRequests,reviews`                                         |
| Copilot起点のレビュー本文  | `uv run ${CLAUDE_SKILL_DIR}/pr-detail.py <N> reviews` （author が `copilot-*` のもの） |

- `gh pr edit --add-reviewer copilot-pull-request-reviewer` や `gh api ... requested_reviewers` でレビュアー追加を強行**しない**。個人アカウントでは原理的に通らないため、失敗ループになるだけ（詳細は [README.md](./README.md#copilotレビュー依頼の制約リグレッション防止メモ) を参照）
- レビュー反映までは数分かかることがある
- Organization リポジトリで Copilot code review が Collaborator 扱いで追加可能な環境の場合のみ、旧来のレビュアー指定方式を検討してよいが、その場合もユーザーに環境を確認してから実行する

## マージ

- マージは**必ずユーザーの明示的な指示**があった場合のみ実行する
- マージ前にCI状態とレビュー承認状態を改めて確認し報告する
- 実行コマンド: `gh pr merge <N>` （オプション: `--merge`, `--squash`, `--rebase`, `--delete-branch`）
- マージ方式は、まずリポジトリの規約（PR 手順の文書、ブランチ保護の設定）を確認する。merge commit を求めるリポジトリもある。規約が無く、ユーザーの指定も無ければユーザーに確認する

### CI の失敗が PR 由来かを見分ける

CI が失敗していたら、base ブランチでも同じワークフローが失敗しているかを比べてから報告する。

1. `uv run ${CLAUDE_SKILL_DIR}/pr-actions.py failed <run_id>` で失敗したステップとエラーを確認する
2. `uv run ${CLAUDE_SKILL_DIR}/pr-actions.py list <base> --workflow <name>` で base 側の直近の結果を見る
3. base でも同じ理由で失敗している（シークレット未設定、外部サービス障害など）なら「PR 由来ではない」と根拠つきで報告し、マージしてよいかをユーザーに判断してもらう。PR の変更で初めて失敗したなら PR 側を直す
