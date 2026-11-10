# Subagents を Python SDK から使う

<!-- 2026-07-29 時点の https://cursor.com/docs/sdk/python.md#subagents に基づく。更新時は references/ も差し替え、cursor-docs で最新を確認すること -->

親 Agent が `Agent` ツール経由で名前付き subagent を spawn できる。定義手段は2つ:

1. **Inline** — `AgentOptions.agents` に `AgentDefinition` を渡す（SDK コード側）
2. **ファイル** — リポジトリの `.cursor/agents/*.md`（frontmatter + 本文）

同名なら **inline がファイル定義を上書き**する。

## Inline 定義（推奨の開始点）

```python
import os

from cursor_sdk import Agent, AgentDefinition, AgentOptions, LocalAgentOptions

with Agent.create(
    AgentOptions(
        model="<discovered-model-id>",
        api_key=os.environ["CURSOR_API_KEY"],
        local=LocalAgentOptions(cwd="."),
        agents={
            "code-reviewer": AgentDefinition(
                description="Expert code reviewer for quality and security.",
                prompt=(
                    "Review the given code for bugs, security issues, "
                    "and maintainability. Return concrete findings only."
                ),
                model="inherit",
            ),
            "test-writer": AgentDefinition(
                description="Writes tests for code changes.",
                prompt="Write focused regression tests for the given change.",
            ),
        },
    )
) as agent:
    # 親が必要と判断したときに Agent ツールで code-reviewer / test-writer を起動する
    result = agent.send(
        "Implement the fix in src/auth.py, then have the code-reviewer "
        "review it and the test-writer add a regression test."
    ).wait()
    print(result.status, result.result)
```

### `AgentDefinition` フィールド

| フィールド    | 必須   | 意味                                                                                     |
| ------------- | ------ | ---------------------------------------------------------------------------------------- |
| `description` | はい   | 親が「いつ spawn するか」を判断する材料                                                  |
| `prompt`      | はい   | subagent の system prompt                                                                |
| `model`       | いいえ | 上書き。`None` / `"inherit"` は親の選択を使う                                            |
| `mcp_servers` | いいえ | この subagent が使える MCP。親の `mcp_servers` の **名前参照**（または定義オブジェクト） |

`description` と `prompt` は狭く書く。広い description だと親が過剰に委譲し、不要な権限や MCP を持ち込む。

### Subagent に MCP を限定する

```python
from cursor_sdk import (
    Agent,
    AgentDefinition,
    AgentOptions,
    HttpMcpServerConfig,
    LocalAgentOptions,
)

with Agent.create(
    AgentOptions(
        model="<discovered-model-id>",
        local=LocalAgentOptions(cwd="."),
        mcp_servers={
            "docs": HttpMcpServerConfig(url="https://example.com/mcp"),
            "linear": HttpMcpServerConfig(
                url="https://mcp.linear.app/mcp",
                headers={"Authorization": "Bearer ..."},
            ),
        },
        agents={
            "ticket-triage": AgentDefinition(
                description="Triage Linear tickets related to this repo.",
                prompt="Only read and summarize tickets. Do not edit code.",
                # 親が持つ MCP のうち linear だけを渡す
                mcp_servers=["linear"],
            ),
        },
    )
) as agent:
    agent.send("Triage open bugs tagged sdk").wait()
```

## ファイル定義（`.cursor/agents/*.md`）

リポジトリに置く:

```text
repo/
  .cursor/
    agents/
      code-reviewer.md
```

```markdown
---
name: code-reviewer
description: Expert code reviewer for quality and security.
model: inherit
---

Review code for bugs, security issues, and proven approaches.
Return concrete findings with file paths. Do not rewrite the whole module.
```

### Local でファイル定義を読む条件

Local では ambient 設定を読み込むために `setting_sources` が必要。ファイルベースの MCP / subagent パスはこれでゲートされる:

```python
from cursor_sdk import Agent, LocalAgentOptions

with Agent.create(
    model="<discovered-model-id>",
    local=LocalAgentOptions(
        cwd=".",
        setting_sources=["project"],  # .cursor/agents と .cursor/mcp.json 等
    ),
) as agent:
    agent.send("Review src/auth.py with the code-reviewer subagent").wait()
```

- `setting_sources` 未指定（デフォルト）→ **inline のみ**（ファイル定義 subagent は読まれない想定）
- Cloud → `setting_sources` は効かない。常に `project` / `team` / `plugins` を読む

Inline とファイルを併用する場合、同じ名前は inline が勝つ。実験用の上書きに便利。

## ネスト

- 親と、親が直接起動した subagent は、さらに別の名前付き subagent を起動できる
- **subagent が起動した subagent** は、さらに下へは起動できない（ネスト上限）
- 各レベルから見える名前付き subagent の集合は同じ（親の `agents` セット）

深いツリーを前提にしない。委譲は1段か2段までに留める。

## Cloud でも同じ

```python
from cursor_sdk import Agent, AgentDefinition, AgentOptions, CloudAgentOptions, CloudRepository

with Agent.create(
    AgentOptions(
        model="<discovered-model-id>",
        cloud=CloudAgentOptions(
            repos=[CloudRepository(url="https://github.com/your-org/your-repo")],
        ),
        agents={
            "code-reviewer": AgentDefinition(
                description="Review PRs for security regressions.",
                prompt="Focus on auth, secrets, and input validation.",
            ),
        },
    )
) as agent:
    agent.send("Fix the reported issue, then run code-reviewer").wait()
```

ファイル定義を Cloud で使うなら `.cursor/agents/*.md` をリポジトリに commit する。

## Hooks との組み合わせ

`subagentStart` / `subagentStop` は hooks 側で観測・制御できる（Cloud でも対応）。ポリシーをコードで強制したい場合は [hooks.md](hooks.md) を併用する。

設定をディスク上で変えたあと、同じ Agent で再読込するなら `agent.reload()`。

## よくある落とし穴

1. **Local で `.cursor/agents` を置いたのに効かない** — `setting_sources` に `"project"`（または `"all"`）を付けたかを確認する
2. **description が曖昧** — 親が spawn しない、または無関係なタスクでも spawn する
3. **subagent に親の全 MCP を渡す** — 必要な名前だけ `mcp_servers=[...]` で渡す
4. **ネストしすぎ** — 2段目の subagent からはさらに spawn できない
5. **resume 後に inline `agents` を忘れる** — 永続化の扱いは公式の最新を確認する。ファイル定義 + `setting_sources` の方が再開に強いことが多い

## 関連

- 公式スナップショット: [references/python-sdk.md](references/python-sdk.md) の Subagents / AgentDefinition 節
- MCP の渡し方: [mcp.md](mcp.md)
- Custom tools（呼び出し元プロセスの関数）: [custom-tools.md](custom-tools.md) — subagent とは別機構
