---
name: pr-agent-docs
description: Use when answering questions about PR-Agent (also known as Qodo Merge / CodiumAI PR-Agent) — installation (GitHub/GitLab/Bitbucket/Azure/local), configuration, automation, tools such as /review /describe /improve /ask /add_docs /generate_labels /update_changelog, core abilities (interactivity, compression, dynamic context, ticket context), or how to run and customize the open-source PR review agent. Grounds answers in the latest official docs from The-PR-Agent/pr-agent instead of training-data memory, which may be stale.
allowed-tools: Bash(python ${CLAUDE_SKILL_DIR}/*.py *)
# 前提:
#   - GitHub CLI (`gh`) が PATH にあること（ファイル取得はこのスキルの download スクリプトが `gh api` を呼ぶ）
#   - 公開リポジトリの読み取りなので認証は必須ではないが、レート制限回避のため `gh auth login` 済みが望ましい
# !`<command>` で起動時に必ずスナップショットを更新/確認する
meta:
  tag: []
  requires_repo_tools: none
  requires_env: none
  dependencies: gh
  requires_install: none
  requires_hooks: none
  requires_skills: none
  status: stable
  description: PR-Agent 公式 docs/docs をローカルにミラーして使い方を根拠付きで答えるスキル
  version: 1.0.1
---

!`python "${CLAUDE_SKILL_DIR}/download_pr_agent_docs.py"`

# PR-Agent 最新ドキュメント参照

PR-Agent（Qodo Merge）の使い方・設定・各ツールについて、学習データの記憶ではなく GitHub 上の公式ドキュメント（`The-PR-Agent/pr-agent` の `docs/docs`）を根拠に回答する。

## スナップショットの範囲

- 索引は `${CLAUDE_SKILL_DIR}/output/summary.md`（上流の TOC）
- 本文は TOC からリンクされている `.md` のみ（`docs/docs` 配下にあっても TOC 未掲載のページは取得しない）
- 取得は `download_pr_agent_docs.py` が `gh api` で行う。7日以内に取得済みならスキップ（`--force` で強制再取得）

## 手順

1. **関連ページを特定する**

   - まず `${CLAUDE_SKILL_DIR}/output/summary.md` を Read/Grep し、質問に関係するパスを探す
   - カテゴリの目安: `installation/`（導入）、`usage-guide/`（設定・自動化）、`tools/`（各コマンド）、`core-abilities/`（振る舞い）、`faq/`

2. **本文を読む**

   - 対応ファイルは `${CLAUDE_SKILL_DIR}/output/<相対パス>`（例: `tools/review.md` → `${CLAUDE_SKILL_DIR}/output/tools/review.md`）
   - 必要なページだけ Read する。`output/` 配下をまとめてコンテキストに流さない
   - 複数ツールや設定項目にまたがる質問なら、関連する数ファイルまで広げてよい

3. **回答する**

   - 読んだ本文に基づいて答え、参照した相対パス（と可能なら上流 URL）を明示する
   - 上流 URL の形: `https://github.com/The-PR-Agent/pr-agent/blob/main/docs/docs/<相対パス>`
   - `summary.md` に無い話題の場合は、その旨を伝え、必要なら上流リポジトリや公式サイトを別途確認する

## 補足

- メタ情報（取得時刻・ファイル一覧）は `${CLAUDE_SKILL_DIR}/output/_meta.json`
- 強制再取得: `python "${CLAUDE_SKILL_DIR}/download_pr_agent_docs.py" --force`
