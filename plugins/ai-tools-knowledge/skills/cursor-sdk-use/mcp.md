# MCP を Python SDK から使う

<!-- 2026-07-29 時点の https://cursor.com/docs/sdk/python.md#mcp-servers に基づく。更新時は references/ も差し替え、cursor-docs で最新を確認すること -->

MCP サーバーは inline 定義、プロジェクト/ユーザー設定、プラグイン、ダッシュボード設定から載る。ランタイム（local / cloud）で読み込み元が違う。

## Inline（いちばん明示的）

```python
import os

from cursor_sdk import (
    Agent,
    AgentOptions,
    HttpMcpServerConfig,
    LocalAgentOptions,
    McpAuth,
    StdioMcpServerConfig,
)

with Agent.create(
    AgentOptions(
        model="<discovered-model-id>",
        api_key=os.environ["CURSOR_API_KEY"],
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
) as agent:
    agent.send("Use the docs server to answer: what is the auth flow?").wait()
```

辞書形式（`{"type": "http", "url": ...}` など）も短いスクリプト向けに受け付ける。アプリコードでは dataclass を優先する。

## 読み込み優先順位

### Local

名前が衝突したら **先勝ち**:

1. `agent.send(..., mcp_servers=...)` — その run では作成時のサーバーを **置き換え**（マージしない）
2. `Agent.create(..., mcp_servers=...)`
3. Plugin servers（`setting_sources` に `"plugins"`）
4. `.cursor/mcp.json`（`setting_sources` に `"project"`）
5. `~/.cursor/mcp.json`（`setting_sources` に `"user"`）

`setting_sources` 未指定 → **inline のみ**。

```python
from cursor_sdk import Agent, LocalAgentOptions

# プロジェクトの .cursor/mcp.json も使う
with Agent.create(
    model="<discovered-model-id>",
    local=LocalAgentOptions(
        cwd=".",
        setting_sources=["project"],
    ),
) as agent:
    agent.send("Use project MCP tools to inspect the issue tracker").wait()
```

OAuth 必須の local MCP は、SDK がブラウザログインを開けない。Cursor アプリで保存済みの資格情報に依存する。

### Cloud

1. `agent.send()` の `mcp_servers`（置き換え）
2. `Agent.create()` の `mcp_servers`
3. [cursor.com/agents](https://cursor.com/agents) の user / team MCP

`local.setting_sources` は Cloud に効かない。Cloud は常に project / team / plugins 相当を読む。

```python
from cursor_sdk import (
    Agent,
    AgentOptions,
    CloudAgentOptions,
    CloudRepository,
    HttpMcpServerConfig,
    StdioMcpServerConfig,
)

with Agent.create(
    AgentOptions(
        model="<discovered-model-id>",
        cloud=CloudAgentOptions(
            repos=[CloudRepository(url="https://github.com/your-org/your-repo")],
        ),
        mcp_servers={
            "linear": HttpMcpServerConfig(
                url="https://mcp.linear.app/mcp",
                headers={"Authorization": "Bearer linear_pat_xxx"},
            ),
            "github": StdioMcpServerConfig(
                command="npx",
                args=["-y", "@modelcontextprotocol/server-github"],
                env={"GITHUB_TOKEN": "ghp_xxx"},
            ),
        },
    )
) as agent:
    agent.send("Open a draft PR description from the Linear ticket").wait()
```

秘密情報の扱い:

- HTTP の `headers` / `auth` → Cursor バックエンドが処理し、機密は VM に入る前に redact
- stdio の `env` → **VM に渡る**。ランタイム秘密情報として扱う
- Service account キーは、ユーザー個人の OAuth フォールバックに使えない

## send() での置き換え

```python
# 作成時に docs + filesystem があっても、この run では docs だけになる（マージされない）
run = agent.send(
    "Answer from docs only",
    mcp_servers={
        "docs": HttpMcpServerConfig(url="https://example.com/mcp"),
    },
)
run.wait()
```

一時的に MCP を外したい・絞りたいときに使う。意図せずサーバーが消えるので、部分上書きだと思わない。

## resume と永続化

Inline MCP は **resume 後に残らない**（秘密をメモリに持つ想定）。`Agent.resume()` 時に再度渡すか、ファイルベース（`.cursor/mcp.json` + local の `setting_sources`）にする。

```python
from cursor_sdk import Agent, AgentOptions, HttpMcpServerConfig

with Agent.resume(
    previous_agent_id,
    AgentOptions(
        api_key=os.environ["CURSOR_API_KEY"],
        mcp_servers={
            "docs": HttpMcpServerConfig(url="https://example.com/mcp"),
        },
    ),
) as agent:
    agent.send("Continue with docs MCP available").wait()
```

## Subagent への絞り込み

親の `mcp_servers` のうち名前だけを subagent に渡せる。詳細は [subagents.md](subagents.md)。

## Local の sandbox / Auto-review（隣接設定）

MCP と同時に触りやすい local 専用オプション:

```python
from cursor_sdk import Agent, LocalAgentOptions

with Agent.create(
    model="<discovered-model-id>",
    local=LocalAgentOptions(
        cwd=".",
        setting_sources=["project"],
        # sandbox_options=...,  # 公式の SandboxOptions 形を実装時に確認
        auto_review=True,       # 対応バックエンドなら tool call を Auto-review 経由に
    ),
) as agent:
    agent.send("Make a small docs-only change").wait()
```

- `sandbox_options` のフィールドは公式ドキュメントとインストール済みパッケージの型を確認する（SKILL 本文で断定しない）
- `auto_review` は補助分類であり、強いセキュリティ境界ではない。強制ポリシーは [hooks.md](hooks.md)

ディスク上の MCP / hooks / agents を変えたら `agent.reload()` で再読込できる。

## よくある落とし穴

1. **`send(mcp_servers=...)` をマージだと思う** — 完全置換
2. **Local で `.cursor/mcp.json` だけ置いて `setting_sources` を忘れる** — 読まれない
3. **resume で inline MCP を渡し忘れる** — ツールが消える
4. **Cloud の stdio `env` に本番秘密を平然と載せる** — VM に入る
5. **Custom tools で済ませられるのに Cloud 前提で MCP 化するのを忘れる** — 逆に Cloud 必須なら最初から MCP

## 関連

- 公式スナップショット: [references/python-sdk.md](references/python-sdk.md) の MCP 節
- Custom tools（local 専用・プロセス内関数）: [custom-tools.md](custom-tools.md)
- Subagents: [subagents.md](subagents.md)
- Hooks: [hooks.md](hooks.md)
