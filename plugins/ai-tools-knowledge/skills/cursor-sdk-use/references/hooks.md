# Hooks — excerpt (SDK / Cloud agents)

<!-- Snapshot date: 2026-07-29. Source: https://cursor.com/docs/hooks.md -->
<!-- Curated for cursor-sdk-use. Prefer cursor-docs for freshness and full event schemas. -->

## Overview

Hooks let you observe, control, and extend the agent loop using custom scripts. Define hooks in `hooks.json` files at the project or user level, or install them through plugins from **Customize**. Hooks are spawned processes that communicate over stdio using JSON in both directions. They run before or after defined stages of the agent loop and can observe, block, or modify behavior.

### Agent hooks (selection)

- `sessionStart` / `sessionEnd` — Session lifecycle
- `preToolUse` / `postToolUse` / `postToolUseFailure` — Generic tool use
- `subagentStart` / `subagentStop` — Subagent lifecycle
- `beforeShellExecution` / `afterShellExecution` — Shell commands
- `beforeMCPExecution` / `afterMCPExecution` — MCP tool usage
- `beforeReadFile` / `afterFileEdit` — File access and edits
- `beforeSubmitPrompt` — Validate prompts
- `preCompact` — Context compaction
- `stop` — Agent completion
- `afterAgentResponse` / `afterAgentThought` — Track responses

## Cloud agent support

Cloud agents run command-based hooks from your repository. If you have hooks defined in `.cursor/hooks.json` at the root of your project, cloud agents pick them up and run them during their work.

On Enterprise plans, cloud agents also run team hooks and enterprise-managed hooks configured through the web dashboard.

Cloud agents sometimes begin in a read-only environment for early exploratory turns. Hooks do not run during those turns. They start once the agent has a writable environment.

### Supported hooks (cloud)

| Hook                   | Supported |
| ---------------------- | --------- |
| `beforeShellExecution` | Yes       |
| `afterShellExecution`  | Yes       |
| `beforeReadFile`       | Yes       |
| `afterFileEdit`        | Yes       |
| `preToolUse`           | Yes       |
| `postToolUse`          | Yes       |
| `postToolUseFailure`   | Yes       |
| `subagentStart`        | Yes       |
| `subagentStop`         | Yes       |
| `beforeSubmitPrompt`   | Yes       |
| `preCompact`           | Yes       |
| `afterAgentResponse`   | Yes       |
| `afterAgentThought`    | Yes       |
| `stop`                 | Yes       |

### Hooks not available in cloud agents

| Hook                                       | Reason                                                                     |
| ------------------------------------------ | -------------------------------------------------------------------------- |
| `sessionStart`                             | Deferred while cloud agents can still start read-only; would fire too late |
| `sessionEnd`                               | Tied to IDE session, not cloud agent chat                                  |
| `beforeMCPExecution` / `afterMCPExecution` | Deferred; MCP hook timing unclear in early read-only phase                 |
| `beforeTabFileRead` / `afterTabFileEdit`   | Tab is IDE-only                                                            |
| `workspaceOpen`                            | IDE lifecycle only                                                         |

### Configuration sources (cloud)

- **Project hooks** (`.cursor/hooks.json` in your repo)
- **Team hooks** (Enterprise, dashboard)
- **Enterprise hooks** (Enterprise, managed)

User-level hooks (`~/.cursor/hooks.json`) are **not** available in cloud agents.

### Execution type limits (cloud)

Cloud agents run **command-based hooks only**. Prompt-based hooks are not available in the cloud execution environment.

## Project vs user hooks

- **Project:** `/.cursor/hooks.json` — scripts run from the **project root**. Use paths like `.cursor/hooks/script.py`
- **User:** `~/.cursor/hooks.json` — scripts run from `~/.cursor/`. Use paths like `./hooks/script.sh`

## Command-based hooks (shape)

```json
{
  "version": 1,
  "hooks": {
    "beforeShellExecution": [
      {
        "command": "python .cursor/hooks/block_rm.py",
        "timeout": 30,
        "matcher": "rm |curl|wget"
      }
    ]
  }
}
```

Exit code behavior:

- `0` — Hook succeeded; use JSON stdout
- `2` — Block the action (equivalent to `permission: "deny"`)
- Other — Hook failed; action proceeds (fail-open by default)

## Relation to the Python SDK

From the Python SDK docs: hooks are file-based only; there is no programmatic hook callback. Pass `local.cwd` / `cloud.repos` so the agent sees the hooks files. Use `agent.reload()` to re-read filesystem config (hooks, project MCP, subagents) without disposing.
