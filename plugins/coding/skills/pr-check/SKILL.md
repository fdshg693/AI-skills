---
name: pr-check
description: PRの作成・状態確認・レビュー依頼・GitHub Actions操作を行う
allowed-tools: Bash(gh *), Bash(git *), Bash(python skills/plugins/use-github/skills/pr-check/*.py *)
meta:
  tag: []
  requires_repo_tools: none
  requires_env: none
  dependencies: gh, git, python
  requires_install: none
  requires_hooks: none
  requires_skills: none
  status: stable
  description: no description
  version: 1.0.4
---

# PR確認・管理スキル

現在のブランチに関連するPull Requestの作成・確認・レビュー依頼・マージ、およびGitHub Actionsの実行・結果取得等をユーザーのリクエストに応じて行う。

## 現在の状態

- ブランチ: !`git branch --show-current`
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

| 目的                                         | コマンド                                                      |
| -------------------------------------------- | ------------------------------------------------------------- |
| PR詳細（本文・マージ可否等）                 | `python "${CLAUDE_SKILL_DIR}/pr-detail.py" <N> view`          |
| レビューコメント（コード行指摘）             | `python "${CLAUDE_SKILL_DIR}/pr-detail.py" <N> comments`      |
| レビュー（承認/変更リクエスト）              | `python "${CLAUDE_SKILL_DIR}/pr-detail.py" <N> reviews`       |
| 任意の組み合わせ（スペース区切りで複数指定） | `python "${CLAUDE_SKILL_DIR}/pr-detail.py" <N> view comments` |
| 明示的に全て取得                             | `python "${CLAUDE_SKILL_DIR}/pr-detail.py" <N> all`           |
| 引数省略時も3つ全て取得                      | `python "${CLAUDE_SKILL_DIR}/pr-detail.py" <N>`               |
| CIチェック状態（出力が大きいので必要時のみ） | `gh pr checks <N>`                                            |

## PR作成

`pr-create.py` を使う。事前に未コミット変更・既存PR・リモートpush状態をチェックする。

| 目的                                 | コマンド                                                                                 |
| ------------------------------------ | ---------------------------------------------------------------------------------------- |
| PR作成（既定: コミットから自動生成） | `python "${CLAUDE_SKILL_DIR}/pr-create.py"`                                              |
| ドラフトPR                           | `python "${CLAUDE_SKILL_DIR}/pr-create.py" --draft`                                      |
| baseブランチ指定                     | `python "${CLAUDE_SKILL_DIR}/pr-create.py" --base develop`                               |
| タイトル/本文指定                    | `python "${CLAUDE_SKILL_DIR}/pr-create.py" --title "..." --body "..."`                   |
| 本文をファイルから                   | `python "${CLAUDE_SKILL_DIR}/pr-create.py" --body-file .github/pull_request_template.md` |

- 作成は**ユーザーの明示的な指示**があった場合のみ実行する
- 大きな変更の場合は先に `git log origin/<base>..HEAD` でコミット一覧を確認して、タイトル・本文の方針をユーザーに提示してから実行する

## GitHub Actions

`pr-actions.py` でワークフロー実行の一覧・詳細・失敗ログ取得・手動実行を行う。ログ全量は巨大になるため `failed` を優先利用する。

| 目的                              | コマンド                                                          |
| --------------------------------- | ----------------------------------------------------------------- |
| 直近20件のrun一覧（現在ブランチ） | `python "${CLAUDE_SKILL_DIR}/pr-actions.py" list`                 |
| 別ブランチのrun一覧               | `python "${CLAUDE_SKILL_DIR}/pr-actions.py" list <branch>`        |
| 対象PRのHEADコミットに紐づくrun   | `python "${CLAUDE_SKILL_DIR}/pr-actions.py" pr <N>`               |
| run詳細（ジョブ毎の成否）         | `python "${CLAUDE_SKILL_DIR}/pr-actions.py" view <run_id>`        |
| 失敗ログのみ（推奨）              | `python "${CLAUDE_SKILL_DIR}/pr-actions.py" failed <run_id>`      |
| ワークフロー手動実行              | `python "${CLAUDE_SKILL_DIR}/pr-actions.py" run <workflow> [ref]` |
| 完了まで追跡                      | `python "${CLAUDE_SKILL_DIR}/pr-actions.py" watch <run_id>`       |

- 手動実行は対象ワークフローに `workflow_dispatch` トリガーが必要
- 手動実行も**ユーザーの明示的な指示**を前提とする

## Copilot レビュー

GitHub Copilot にコードレビューを依頼する。**個人アカウントのリポジトリでは Copilot を Collaborator として追加できない**ため、`gh pr edit --add-reviewer` や requested_reviewers API による正規のレビュアー指定は使えない（422で失敗する）。代わりに PRコメントで `@copilot review` メンションする方式を使う。

| 目的                       | コマンド                                                                                 |
| -------------------------- | ---------------------------------------------------------------------------------------- |
| Copilotレビュー依頼        | `gh pr comment <N> --body "@copilot review"`                                             |
| レビュー状態（依頼中含む） | `gh pr view <N> --json reviewRequests,reviews`                                           |
| Copilot起点のレビュー本文  | `python "${CLAUDE_SKILL_DIR}/pr-detail.py" <N> reviews` （author が `copilot-*` のもの） |

- `gh pr edit --add-reviewer copilot-pull-request-reviewer` や `gh api ... requested_reviewers` でレビュアー追加を強行**しない**。個人アカウントでは原理的に通らないため、失敗ループになるだけ（詳細は [README.md](./README.md#copilotレビュー依頼の制約リグレッション防止メモ) を参照）
- レビュー反映までは数分かかることがある
- Organization リポジトリで Copilot code review が Collaborator 扱いで追加可能な環境の場合のみ、旧来のレビュアー指定方式を検討してよいが、その場合もユーザーに環境を確認してから実行する

## マージ

- マージは**必ずユーザーの明示的な指示**があった場合のみ実行する
- マージ前にCI状態とレビュー承認状態を改めて確認し報告する
- 実行コマンド: `gh pr merge <N>` （オプション: `--squash`, `--rebase`, `--delete-branch`）
- マージ方法の指定がなければユーザーに確認する
