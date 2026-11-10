---
name: claude-code-docs
description: Use when answering questions about Claude Code (CLI) features, settings, hooks, skills, slash commands, subagents, MCP, memory, etc. Grounds answers in the latest official docs (code.claude.com) instead of training-data memory, which may be stale.
allowed-tools: Bash(python ${CLAUDE_SKILL_DIR}/*.py *)
# !`<command>`を使ってスクリプトを実行することで、動的にコマンド結果を注入できるようにする。
meta:
  tag: []
  requires_repo_tools: none
  requires_env: none
  dependencies: none
  requires_install: none
  requires_hooks: none
  requires_skills: none
  status: stable
  description: no description
  version: 1.0.3
---

!`python ${CLAUDE_SKILL_DIR}/download_claude_code_reference.py`

# Claude Code 最新ドキュメント参照

## 手順

1. **関連箇所を探す**

   - まず `${CLAUDE_SKILL_DIR}/output/llms.txt` を Grep/Read して、質問に関連しそうなページの URL・slug を特定する
   - 詳細な本文が必要なら `${CLAUDE_SKILL_DIR}/output/llms-full.txt` を Grep して該当セクションのおおよその位置を掴む

2. **該当セクションを抽出する**（本文が長い場合に推奨）

   ```bash
   python ${CLAUDE_SKILL_DIR}/extract_doc_section.py <slug または URL> [<slug または URL>...]
   ```

   - 例: `python ${CLAUDE_SKILL_DIR}/extract_doc_section.py hooks skills`
   - `${CLAUDE_SKILL_DIR}/output/temp/<slug>.txt` に該当セクションだけが書き出されるので、それを Read して内容を確認する

3. **回答する**

   - 抽出した本文に基づいて回答し、参照した URL（`Source:` 行）を明示する
   - `${CLAUDE_SKILL_DIR}/output/llms-full.txt` に該当ページが見つからない場合は、その旨を伝えた上で WebFetch 等で `code.claude.com` を直接参照してもよい

## 補足

- スクリプトは`${CLAUDE_SKILL_DIR}/output/`を読み書きする
- `${CLAUDE_SKILL_DIR}/output/temp/` は作業用の一時ファイル置き場（都度上書きされる想定）
