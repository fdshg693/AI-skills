---
name: claude-agent-sdk
description: Use when building, reviewing, or troubleshooting Python or Node.js/TypeScript applications that use Anthropic's Claude Agent SDK, including agent loops, sessions, tools, MCP, permissions, hooks, streaming, structured output, and deployment. Use the official Claude Code documentation cache for API details that may have changed.
allowed-tools: Bash(python ${CLAUDE_SKILL_DIR}/scripts/webref_cli.py *)
meta:
  tag: []
  requires_repo_tools: none
  requires_env: ANTHROPIC_API_KEY
  dependencies: claude-agent-sdk or @anthropic-ai/claude-agent-sdk
  requires_install: see python.md or node.md
  requires_hooks: none
  requires_skills: claude-code-docs
  status: stable
  description: no description
  version: 1.0.3
---

# Claude Agent SDK

Claude Agent SDKを使う案件では、まず対象言語を判定し、対応する詳細ファイルだけを読む。公式ドキュメントは SDK 専用の小さな索引とページ単位キャッシュから参照する。Claude Code 全体の `llms-full.txt` を取得・走査する必要はない。

- Python: `${CLAUDE_SKILL_DIR}/python.md`
- Node.js / TypeScript: `${CLAUDE_SKILL_DIR}/node.md`

起動時に次のコマンドが自動実行され、`llms.txt` 索引だけが24時間キャッシュ付きで更新される。

!`python ${CLAUDE_SKILL_DIR}/scripts/webref_cli.py index`

## 公式ドキュメントの調べ方

1. 対応する言語ファイルの「参照ページ」と [reference-map.md](reference-map.md) から、必要な slug と検索キーを選ぶ。
2. 必要なページだけを取得する。ページ本文は `output/pages/agent-sdk/<slug>.md` に24時間キャッシュされる。

   ```text
   python ${CLAUDE_SKILL_DIR}/scripts/webref_cli.py download --slug agent-sdk/python --slug agent-sdk/quickstart
   ```

3. 取得済みページから必要な項目だけを検索する。正規表現が不要なら `--fixed-strings` を使う。

   ```text
   python ${CLAUDE_SKILL_DIR}/scripts/webref_cli.py grep "permission_mode|allowed_tools" --ignore-case
   ```

   検索結果には該当ページの Source URL と前後の行が表示される。詳細が必要な場合だけ、そのページファイルを Read する。

4. キャッシュが壊れた、または仕様の更新を明示的に確認したい場合だけ `download` / `index` に `--force` を付ける。`download --all` は全ページ取得になるため、通常は使わない。

`llms.txt` に載っていない URL が必要な場合は、推測で補わず `claude-code-docs` スキルへフォールバックする。回答・実装判断に使ったページの `Source:` URL を明示する。

両言語が混在する場合だけ、両方のファイルを読む。SDKのAPIや挙動は変わり得るため、詳細ファイルの手順に従って `claude-code-docs` の公式ドキュメントを確認し、別言語のAPI名やコード例を混ぜない。
