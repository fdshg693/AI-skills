---
name: gh-pr
description: gh で現在のブランチのPRを作成・状態確認・マージし、GitHub Actions の run の一覧・詳細取得・手動実行・追跡を行う。Actions の失敗原因の調査は cicd プラグインの diagnosing-actions を使う。
allowed-tools: Bash(gh *), Bash(git *), Bash(python *gh-pr/*.py*)
meta:
  tag: []
  requires_repo_tools: none
  requires_env: none
  dependencies: gh, git, python
  requires_install: none
  requires_hooks: none
  requires_skills: none
  status: stable
  description: 現在のブランチのPR作成・状態確認・マージとGitHub Actionsのrun一覧・詳細・手動実行
  version: 1.1.0
---

# gh-pr

現在のブランチに関連するPull Requestの作成・確認・マージ、およびGitHub Actionsのrunの確認・手動実行等をユーザーのリクエストに応じて行う。

## 対象リポジトリ

スクリプトはカレントディレクトリの git remote から対象リポジトリを決める。サブモジュールやスキルのフォルダの中で実行すると別のリポジトリを見て `HTTP 404` になるので、次のどちらかにする。

- 対象リポジトリのルートで実行する
- `-R OWNER/REPO` を付ける（`pr-detail.py`・`pr-actions.py`）。`pr-actions.py` に Actions の URL を渡したときは URL のリポジトリが使われる

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

`pr-create.py` を使う。事前に未コミット変更・既存PR・リモートpush状態をチェックし、ブランチが未pushまたは `origin/<branch>` より先行していれば push してから作る。

| 目的                                 | コマンド                                                                                 |
| ------------------------------------ | ---------------------------------------------------------------------------------------- |
| PR作成（既定: コミットから自動生成） | `python "${CLAUDE_SKILL_DIR}/pr-create.py"`                                              |
| ドラフトPR                           | `python "${CLAUDE_SKILL_DIR}/pr-create.py" --draft`                                      |
| baseブランチ指定                     | `python "${CLAUDE_SKILL_DIR}/pr-create.py" --base develop`                               |
| タイトル/本文指定                    | `python "${CLAUDE_SKILL_DIR}/pr-create.py" --title "..." --body "..."`                   |
| 本文をファイルから                   | `python "${CLAUDE_SKILL_DIR}/pr-create.py" --body-file .github/pull_request_template.md` |

- 作成は**ユーザーの明示的な指示**があった場合のみ実行する
- base との差分が 2 コミット以上あるときは `--title` が必須（直近コミットの件名では PR 全体を表せないため、省略するとコミット一覧を出して中断する）。`git log origin/<base>..HEAD` を見て全体を表すタイトルを付ける
- 大きな変更の場合は先にコミット一覧を確認して、タイトル・本文の方針をユーザーに提示してから実行する

## GitHub Actions

`pr-actions.py` でワークフロー実行の一覧・詳細・失敗ログ取得・手動実行を行う。`view`・`failed`・`watch` は run id のほか run/job の URL（`.../actions/runs/<id>`、`.../job/<id>`）を受け付ける。job URL ならその job だけを表示する。

**失敗原因の調査を頼まれたら** cicd プラグインの `diagnosing-actions` スキルを使う（失敗ログを INDEX 付きのファイルに切り出し、必要な箇所だけ読める）。このスキルで済ませるときは次の順にする。

1. `view` の ANNOTATIONS を読む。`::error::` で出したメッセージ（シークレット未設定など）はここで原因が分かる
2. それで分からないときだけ `failed` で失敗stepのログを見る。ログ全量は巨大になるため `gh run view --log` は使わない
3. シークレット未設定が疑われるときは `gh secret list`（environment のシークレットは `gh secret list --env <name>`）で登録の有無を確かめる

| 目的                              | コマンド                                                          |
| --------------------------------- | ----------------------------------------------------------------- |
| 直近20件のrun一覧（現在ブランチ） | `python "${CLAUDE_SKILL_DIR}/pr-actions.py" list`                 |
| 別ブランチのrun一覧               | `python "${CLAUDE_SKILL_DIR}/pr-actions.py" list <branch>`        |
| 対象PRのHEADコミットに紐づくrun   | `python "${CLAUDE_SKILL_DIR}/pr-actions.py" pr <N>`               |
| run詳細（ジョブ毎の成否）         | `python "${CLAUDE_SKILL_DIR}/pr-actions.py" view <run_id\|URL>`   |
| 失敗ログのみ                      | `python "${CLAUDE_SKILL_DIR}/pr-actions.py" failed <run_id\|URL>` |
| ワークフロー手動実行              | `python "${CLAUDE_SKILL_DIR}/pr-actions.py" run <workflow> [ref]` |
| 完了まで追跡                      | `python "${CLAUDE_SKILL_DIR}/pr-actions.py" watch <run_id\|URL>`  |
| 別リポジトリを対象にする          | 各コマンドに `-R OWNER/REPO` を付ける                             |

- 手動実行は対象ワークフローに `workflow_dispatch` トリガーが必要
- 手動実行も**ユーザーの明示的な指示**を前提とする

## マージ

- マージは**必ずユーザーの明示的な指示**があった場合のみ実行する
- マージ前にCI状態とレビュー承認状態を改めて確認し報告する
- 実行コマンド: `gh pr merge <N> --merge|--squash|--rebase` （任意: `--delete-branch`）
- マージ方法は、リポジトリの規約（`AGENTS.md`・`CONTRIBUTING.md`・ブランチ運用のドキュメント等）に指定があればそれに従う。作業ブランチを使い続ける運用では squash・rebase にすると作業ブランチの commit が base の祖先にならないので、規約が merge commit ならそれ以外を選ばない
- 規約にもユーザーの指示にも指定がなければユーザーに確認する
