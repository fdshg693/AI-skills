---
name: vscode-copilot-docs
description: Use when answering questions about GitHub Copilot's presence inside VS Code itself (Copilot Chat, Agent mode/Agents window, agent customization, MCP servers, inline suggestions, custom instructions/prompt files, etc.). Grounds answers in a curated excerpt of code.visualstudio.com's official docs instead of training-data memory, which may be stale.
meta:
  tag: []
  requires_repo_tools: aim
  requires_env: none
  dependencies: none
  requires_install: none
  requires_hooks: none
  requires_skills: vscode-docs,github-copilot-docs,aim-cli
  status: stable
  description: no description
  version: 1.0.6
---

# VS Code 内の GitHub Copilot 最新ドキュメント参照（抜粋版）

VS Code エディタに統合された GitHub Copilot 機能（Chat, Agent mode, Agents window, MCP, カスタムインストラクション等）に関する質問に、学習データの記憶ではなく `code.visualstudio.com` の公式ドキュメントを根拠に回答するためのスキル。

## 手順

1. **抜粋ファイルを探す**

   - `./output/copilot-excerpt.md` を Grep/Read して、質問に関連しそうなページの URL と短い説明を特定する
   - セクション見出し（`## Agents` `## Agent Customization` `## Using Chat` `## Guides` など）で大まかなカテゴリを絞り込める

2. **該当ページの本文を取得する**（説明文だけで回答できない場合）

   - 見つけた URL を WebFetch で取得する
   - 複数ページにまたがりそうな質問なら、関連しそうな URL を複数 WebFetch してよい

3. **回答する**

   - 取得した本文に基づいて回答し、参照した URL を明示する
   - `./output/copilot-excerpt.md` に該当ページが見つからない場合は、[vscode-docs](../vscode-docs/SKILL.md) スキルの `skills/plugins/others/skills/vscode-docs/output/llms.txt` 全体（VS Code の他機能も含む）を探すか、`https://code.visualstudio.com/docs` 配下を WebFetch 等で直接探索してもよい
   - GitHub Copilot 全般（GitHub.com 側の機能、Copilot CLI 単体、plans/billing 等）については [github-copilot-docs](../github-copilot-docs/SKILL.md) スキルの方が適切な場合がある
