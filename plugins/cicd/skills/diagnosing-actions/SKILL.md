---
name: diagnosing-actions
description: GitHub Actionsの失敗原因を特定する。runやjobのURL、PR番号、PRのURLを渡されたとき、CIが落ちているとき、Actionsの失敗ログを調べるときに使う。ワークフローの再実行やPRへの書き込みは行わない。
argument-hint: "[ActionsのURL | PR番号 | PRのURL]"
arguments: [target]
allowed-tools: Bash(python ${CLAUDE_SKILL_DIR}/actions_report.py *)
# 前提: gh CLI が PATH にあり、`gh auth login` 済みであること。未インストール・未認証はスクリプトがエラーで終了する。
# 読み取り専用。gh pr view / gh run view / gh api (GET) のみ。再実行・watch・コメント・merge はしない。
# 失敗ログは temp/actions/ に切り出し、INDEX.md から必要なファイルだけを読む。全文を会話に出さない。
meta:
  tag: []
  requires_repo_tools: none
  requires_env: none
  dependencies: none
  requires_install: gh CLI
  requires_hooks: none
  requires_skills: none
  status: experimental
  description: Actionsの失敗ログを temp/actions の INDEX 付きファイルに切り出して原因箇所を読めるようにする
  version: 1.0.0
---

GitHub Actions の失敗を特定する。**行うのは失敗情報の読み取りだけ**で、ワークフローの再実行、`gh run watch`、PRへのコメント、approve、merge はしない。

ログの取得に `gh run view --log-failed` を直接実行しない。失敗ログは長くなるため、同梱の `actions_report.py` だけを使う。

## 対象を決める

`$target` または依頼文から、次のいずれか1つを使う。判断がつかないときは推測せずに確認する。

- Actions の URL。`.../actions/runs/<id>`、`.../attempts/<n>`、`.../job/<id>`、古い `.../runs/<job_id>` を含む
- PR の URL、または PR 番号（`123` / `#123`）
- `run:<id>`。番号だけを run id とは扱わない
- 指定が無く「このブランチのCI」「このPRのチェック」のように現在のPRを指している場合は、引数を省略する

## 手順

1. **失敗情報を書き出す**

   ```
   python ${CLAUDE_SKILL_DIR}/actions_report.py <TARGET>
   ```

   - `$target` が空なら引数なしで実行する（カレントブランチのPRを `gh` が検出する）
   - URL 以外の番号で、カレントと別のリポジトリを見るときだけ `--gh-repo OWNER/REPO` を付ける
   - 出力先を変えるときだけ `--output-dir <dir>` を付ける。省略時はリポジトリの `temp/actions/<timestamp>_<label>/`

2. **INDEX を読む**

   標準出力の1行目が `INDEX.md` のパス。次の行に失敗ジョブ数と、ジョブごとの先頭エラーが出る。

   `INDEX.md` の表が、開くファイルの一覧。列は workflow、job、失敗step、行数、先頭エラー。成功したチェックのログは書いていない。

3. **必要なファイルだけ読む**

   表の「先頭」で原因が言い切れる場合でも、そのファイルの該当stepを開き、抜粋が途中で切れていないかを確認する。`part` が複数あるときは、表のstep列に出ているファイルだけを開く。cancelled や Actions 以外の失敗は INDEX の後半に名前と URL だけがある。

4. **結果を報告する**

   - 読み取りのみで、再実行や PR への書き込みはしていないこと
   - 出力先ディレクトリ
   - 失敗した workflow / job / step
   - 原因のエラー（ファイルからの引用）
   - 失敗が複数あるときは、互いに独立したものに分ける
   - ログを取得できなかった場合、または Actions 以外のチェックの場合はその旨
   - ログにトークンや秘密値が含まれていたら、値は伏せる

   依頼が失敗の特定までなら、ここで止める。修正や再実行は求められたときだけ、このスキルの外で行う。
