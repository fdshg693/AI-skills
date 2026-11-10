# Cursor Python SDK — excerpt (MCP / Subagents / Custom tools / Hooks / config)

<!-- Snapshot date: 2026-07-29. Source: https://cursor.com/docs/sdk/python.md -->
<!-- This is a curated excerpt for cursor-sdk-use companions. Prefer cursor-docs for freshness. -->

## MCP servers

Agents can pick up MCP servers from inline definitions, project/user settings, plugins, and dashboard-managed configuration depending on the runtime.

```python
from cursor_sdk import (
    Agent,
    AgentOptions,
    HttpMcpServerConfig,
    LocalAgentOptions,
    McpAuth,
    StdioMcpServerConfig,
)

agent = Agent.create(
    AgentOptions(
        model="composer-2.5",
        local=LocalAgentOptions(cwd="."),
        mcp_servers={
            "docs": HttpMcpServerConfig(
                url="https://example.com/mcp",
                auth=McpAuth(client_id="client-id", scopes=["read", "write"]),
            ),
            "filesystem": StdioMcpServerConfig(
                command="npx",
                args=["-y", "@modelcontextprotocol/server-filesystem", "."],
            ),
        },
    )
)
```

Flat dictionaries (`{"type": "http", "url": ...}` and `{"type": "stdio", "command": ...}`) are also accepted as a quick-script convenience.

### What gets loaded

**Local agents** load servers from up to five sources, with first-match-wins precedence on conflicting names:

1. `mcp_servers` on `agent.send()`. Fully replaces creation-time servers for that run (not merged).
2. `mcp_servers` on `Agent.create()`. Used when no per-send override is provided.
3. Plugin servers, if `local.setting_sources` includes `"plugins"`.
4. Project servers from `.cursor/mcp.json`, if `local.setting_sources` includes `"project"`.
5. User servers from `~/.cursor/mcp.json`, if `local.setting_sources` includes `"user"`.

Without `local.setting_sources`, only inline servers are loaded. If a local MCP server requires OAuth login, the SDK can reuse a saved login from the Cursor app, but it cannot open a browser to sign you in.

**Cloud agents** load servers from:

1. `mcp_servers` on `agent.send()`. Fully replaces creation-time servers for that run (not merged).
2. `mcp_servers` on `Agent.create()`. Used when no per-send override is provided.
3. Your user and team MCP servers from [cursor.com/agents](https://cursor.com/agents).

If an inline server doesn't include `auth` or `headers` and you've previously authorized that server URL on cursor.com/agents, runs authenticated with a personal API token reuse those OAuth tokens automatically. Service account API keys cannot fall back to user auth as they are not associated with a user.

`local.setting_sources` does not apply to cloud agents.

### Cloud

Cloud agents accept authenticated MCP configs inline too. Cloud MCP supports HTTP and stdio transports. Use HTTP `headers` for static API keys or Bearer tokens. Use HTTP `auth` for OAuth-protected servers. Use stdio `env` when the server runs inside the cloud VM and reads credentials from environment variables.

- HTTP `headers` and `auth` are handled by Cursor's backend. Sensitive fields are redacted and do not enter the VM.
- Stdio `env` values are passed into the VM because the server runs there. Treat them like any other runtime secret.
- OAuth for MCP servers configured on cursor.com/agents stays per-user, even for team-level servers.

## Subagents

Define named subagents that the main agent can spawn via the `Agent` tool. Pass them inline:

```python
from cursor_sdk import Agent, AgentDefinition, AgentOptions, LocalAgentOptions

agent = Agent.create(
    AgentOptions(
        model="composer-2.5",
        local=LocalAgentOptions(cwd="."),
        agents={
            "code-reviewer": AgentDefinition(
                description="Expert code reviewer for quality and security.",
                prompt="Review code for bugs, security issues, and proven approaches.",
                model="inherit",
            ),
            "test-writer": AgentDefinition(
                description="Writes tests for code changes.",
                prompt="Write comprehensive tests for the given code.",
            ),
        },
    )
)
```

Subagents committed to the repo at `.cursor/agents/*.md` (with `name`, `description`, and optional `model` frontmatter) are also picked up. Inline definitions override file-based ones with the same name.

### Nested subagents

Subagents can spawn their own subagents, within a nesting limit. When a subagent uses the `Agent` tool, it reaches the same subagent executor the parent has, so a parent can delegate to a subagent that delegates further. Each level sees the same set of named subagents. The top-level agent and its direct subagents can launch subagents, but a subagent launched by another subagent can't launch further ones.

## Custom tools

Custom tools let you expose Python functions to local agents without standing up a separate MCP server. Pass them on `LocalAgentOptions.custom_tools`.

```python
from cursor_sdk import Agent, CustomTool, CustomToolContext, LocalAgentOptions

def get_deployment_status(args, context: CustomToolContext):
    service = args["service"]
    return f"Service {service} is healthy."

with Agent.create(
    model="composer-2.5",
    local=LocalAgentOptions(
        cwd=".",
        custom_tools={
            "get_deployment_status": CustomTool(
                description="Look up the current deployment status for a service.",
                input_schema={
                    "type": "object",
                    "properties": {
                        "service": {"type": "string", "description": "Service name"},
                    },
                    "required": ["service"],
                },
                execute=get_deployment_status,
            ),
        },
    ),
) as agent:
    agent.send("Is the checkout service healthy?").wait()
```

`execute` receives the parsed arguments and a `CustomToolContext` with `tool_call_id` when available. It can return a string, a JSON-compatible value, or a mapping with a `content` list. Custom tools are local agents only.

## Hooks

Hooks are file-based only. There is no programmatic hook callback. Hooks are a project policy boundary, not a per-run knob.

- **Local:** Add `.cursor/hooks.json` to the repo passed as `local.cwd`, or add `~/.cursor/hooks.json` for user-level hooks.
- **Cloud:** Commit `.cursor/hooks.json` and its scripts to the repo passed in `cloud.repos`. SDK-created cloud agents load project hooks automatically. On Enterprise plans, they also run team hooks and enterprise-managed hooks.

See [Hooks](https://cursor.com/docs/hooks.md) for the configuration format and [Cloud Agents hooks support](https://cursor.com/docs/cloud-agent.md#hooks-support) for cloud behavior.

## Agent / Local / definition fields (excerpt)

### AgentOptions (selected)

| Property      | Type                                                 | Description                    |
| ------------- | ---------------------------------------------------- | ------------------------------ |
| `mcp_servers` | `Mapping[str, McpServerConfig]`                      | Inline MCP server definitions. |
| `agents`      | `Mapping[str, AgentDefinition \| Mapping[str, Any]]` | Subagent definitions.          |

### LocalAgentOptions (selected)

| Property          | Type                                  | Description                                                        |
| ----------------- | ------------------------------------- | ------------------------------------------------------------------ |
| `cwd`             | path(s)                               | Workspace path or paths.                                           |
| `setting_sources` | `Sequence[SettingSource]`             | `"project"`, `"user"`, `"team"`, `"mdm"`, `"plugins"`, or `"all"`. |
| `sandbox_options` | `SandboxOptions \| Mapping`           | Local sandbox options.                                             |
| `auto_review`     | `bool`                                | Route local tool calls through Auto-review when supported.         |
| `custom_tools`    | `Mapping[str, CustomTool \| Mapping]` | Custom tools for local agents.                                     |

### AgentDefinition

| Property      | Required | Description                                                          |
| ------------- | -------- | -------------------------------------------------------------------- |
| `description` | yes      | When to use this subagent. Shown to the parent.                      |
| `prompt`      | yes      | System prompt for the subagent.                                      |
| `model`       | no       | Override. `None` and `"inherit"` use the parent.                     |
| `mcp_servers` | no       | MCP servers for this subagent. Names reference parent `mcp_servers`. |

### CustomTool

```python
@dataclass
class CustomTool:
    execute: Callable[[Mapping[str, Any], CustomToolContext], Any]
    description: str | None = None
    input_schema: Mapping[str, Any] | None = None

class CustomToolContext:
    tool_call_id: str | None = None
```

### Agent.reload

`reload` — Re-read filesystem config (hooks, project MCP, subagents) without disposing.

## Known limitations (excerpt)

- Inline MCP servers are not persisted across `Agent.resume()`. Pass them again on resume if needed.
- Custom tools (`local.custom_tools`) are local agents only.
- `local.setting_sources` (and the file-based MCP and subagent paths it gates) does not apply to cloud agents. Cloud always loads `project`, `team`, and `plugins`.
- Hooks are file-based only (`.cursor/hooks.json`). No programmatic callbacks.
