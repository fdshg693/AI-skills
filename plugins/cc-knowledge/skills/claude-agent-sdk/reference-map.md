# Claude Agent SDK reference map

公式索引の URL 一覧は `scripts/webref_cli.py index` でも確認できる。このファイルは、どのページを先にキャッシュし、どの語で検索すればよいかを迷わないための手掛かりである。URL の本文をここに複製せず、必要なページだけを取得する。

## 使い方

1. 起動時に更新される `output/llms.txt` から候補ページを確認する。
2. 必要な slug だけを取得する。複数指定時は `--slug` を繰り返す。

```text
python ${CLAUDE_SKILL_DIR}/scripts/webref_cli.py download \
  --slug agent-sdk/python \
  --slug agent-sdk/quickstart \
  --slug agent-sdk/permissions
```

3. 取得済みページだけをキーワード検索する。ヒットにはページの Source URL が付く。

```text
python ${CLAUDE_SKILL_DIR}/scripts/webref_cli.py grep "permission|allowed_tools|canUseTool" --ignore-case
```

`grep` が「No matches」を返した場合は、対象ページを先に `download` する。`--all` は通常使わず、必要な slug を選ぶ。

## ページと検索キー

### 導入・全体像

- `agent-sdk/overview` — SDK の位置づけ、Claude Code as a library、production agent
- `agent-sdk/quickstart` — install、`query`、Python、TypeScript、first agent、環境変数
- `agent-sdk/examples` — recipes、working examples、common agent patterns、sample code
- `agent-sdk/agent-loop` — message lifecycle、assistant、tool、result、turn、context window
- `agent-sdk/migration-guide` — Claude Code SDK、Claude Agent SDK、migration、breaking change、package
- `agent-sdk/troubleshooting` — error、debug、API key、permissions、MCP、process、timeout

### 言語別 API

- `agent-sdk/python` — `claude_agent_sdk`、`query`、`ClaudeSDKClient`、`ClaudeAgentOptions`、`async`
- `agent-sdk/typescript` — `@anthropic-ai/claude-agent-sdk`、`query`、`ClaudeAgentOptions`、`async iterator`、camelCase
- `agent-sdk/typescript-v2-preview` — V2 session API、removed、deprecated、migration（現行実装の根拠にはしない）

### 入力・出力・対話

- `agent-sdk/streaming-vs-single-mode` — streaming input、single prompt、`AsyncIterable`、multi-turn、interrupt
- `agent-sdk/streaming-output` — streaming response、message、text、tool call、partial、real-time
- `agent-sdk/user-input` — approval、user input、`can_use_tool`、`canUseTool`、question、permission
- `agent-sdk/structured-outputs` — JSON Schema、`output_format`、`outputFormat`、Pydantic、Zod、`structured_output`

### ツール・MCP・Claude Code 機能

- `agent-sdk/custom-tools` — `@tool`、`tool`、`create_sdk_mcp_server`、`createSdkMcpServer`、in-process MCP
- `agent-sdk/mcp` — MCP server、stdio、SSE、HTTP、authentication、transport、error、tool search
- `agent-sdk/tool-search` — many tools、defer loading、tool discovery、large tool set、MCP
- `agent-sdk/claude-code-features` — `CLAUDE.md`、settings、hooks、skills、setting sources
- `agent-sdk/skills` — Agent Skills、`setting_sources`、`settingSources`、skill discovery、load
- `agent-sdk/plugins` — plugin、plugin marketplace、skills、agents、hooks、MCP
- `agent-sdk/modifying-system-prompts` — `system_prompt`、`systemPrompt`、preset、append、custom prompt

### 権限・フック・状態

- `agent-sdk/permissions` — `permission_mode`、`permissionMode`、`allowed_tools`、`allowedTools`、deny、allow、sandbox
- `agent-sdk/hooks` — `PreToolUse`、`PostToolUse`、`Stop`、`SessionEnd`、callback、timeout、decision
- `agent-sdk/sessions` — session、`resume`、`continue`、`fork`、conversation、session ID
- `agent-sdk/session-storage` — persistence、S3、Redis、transcript、external storage、resume
- `agent-sdk/file-checkpointing` — checkpoint、rewind、file changes、`rewind_files`、`enable_file_checkpointing`
- `agent-sdk/subagents` — subagent、agent definition、parallel、isolated context、task delegation
- `agent-sdk/todo-tracking` — todo、task list、progress、tracking、display

### 本番運用・安全性

- `agent-sdk/cost-tracking` — usage、tokens、cost、prompt caching、cache、`total_cost_usd`
- `agent-sdk/observability` — OpenTelemetry、trace、metrics、events、instrumentation、telemetry
- `agent-sdk/hosting` — subprocess、Docker、Kubernetes、scaling、session persistence、multi-tenant
- `agent-sdk/secure-deployment` — isolation、sandbox、credentials、network、secret、container、security

### 更新時の扱い

このマップは現在の `llms.txt` に掲載されている Agent SDK ページを網羅する。新しいページが追加された場合は、まず `index` の出力で確認し、用途と検索キーをこのファイルへ追記する。公式ページの仕様は必ずキャッシュ本文と Source URL を根拠にし、記憶で API 名や既定値を補わない。
