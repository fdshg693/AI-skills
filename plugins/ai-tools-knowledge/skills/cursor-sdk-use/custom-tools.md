# Custom tools を Python SDK から使う

<!-- 2026-07-29 時点の https://cursor.com/docs/sdk/python.md#custom-tools に基づく。更新時は references/ も差し替え、cursor-docs で最新を確認すること -->

Custom tools は、**呼び出し元 Python プロセス上の関数**を local Agent にツールとして公開する仕組み。別途 MCP サーバーを立てずに、社内 API やローカル状態を Agent に渡せる。

制約:

- **Local agents のみ**（Cloud では使えない）
- `LocalAgentOptions.custom_tools` に渡す
- 実行は呼び出し元プロセス。Agent の sandbox / Cloud VM 内ではない

Cloud や他プロセスから同じ能力が必要なら MCP（[mcp.md](mcp.md)）を使う。

## 最小例

```python
import os

from cursor_sdk import Agent, CustomTool, CustomToolContext, LocalAgentOptions


def get_deployment_status(args, context: CustomToolContext):
    service = args["service"]
    # ここで社内 API やローカルキャッシュを読んでよい
    return f"Service {service} is healthy."


with Agent.create(
    model="<discovered-model-id>",
    api_key=os.environ["CURSOR_API_KEY"],
    local=LocalAgentOptions(
        cwd=".",
        custom_tools={
            "get_deployment_status": CustomTool(
                description="Look up the current deployment status for a service.",
                input_schema={
                    "type": "object",
                    "properties": {
                        "service": {
                            "type": "string",
                            "description": "Service name",
                        },
                    },
                    "required": ["service"],
                },
                execute=get_deployment_status,
            ),
        },
    ),
) as agent:
    result = agent.send("Is the checkout service healthy?").wait()
    print(result.status, result.result)
```

## `CustomTool` / 戻り値

```python
@dataclass
class CustomTool:
    execute: Callable[[Mapping[str, Any], CustomToolContext], Any]
    description: str | None = None
    input_schema: Mapping[str, Any] | None = None

class CustomToolContext:
    tool_call_id: str | None = None
```

`execute` の戻り値として使えるもの:

- `str`
- JSON 互換の値（dict / list / 数値など）
- `{"content": [...]}` 形式の mapping（リッチな tool result）

例外はツール失敗として Agent に返る想定で扱う。副作用のある処理は冪等にし、タイムアウトとリトライを呼び出し側で設計する。

## 複数ツールと安全策

```python
from pathlib import Path

from cursor_sdk import CustomTool, CustomToolContext, LocalAgentOptions

ALLOWED_SERVICES = {"checkout", "billing", "search"}


def get_deployment_status(args, context: CustomToolContext):
    service = args["service"]
    if service not in ALLOWED_SERVICES:
        raise ValueError(f"unknown service: {service}")
    return {"service": service, "status": "healthy"}


def read_runbook(args, context: CustomToolContext):
    name = Path(args["name"]).name  # パストラバーサルを避ける
    path = Path("runbooks") / f"{name}.md"
    return path.read_text(encoding="utf-8")


local = LocalAgentOptions(
    cwd=".",
    custom_tools={
        "get_deployment_status": CustomTool(
            description="Deployment status for an allowlisted service.",
            input_schema={
                "type": "object",
                "properties": {"service": {"type": "string"}},
                "required": ["service"],
            },
            execute=get_deployment_status,
        ),
        "read_runbook": CustomTool(
            description="Read an ops runbook by short name.",
            input_schema={
                "type": "object",
                "properties": {"name": {"type": "string"}},
                "required": ["name"],
            },
            execute=read_runbook,
        ),
    },
)
```

書くときのチェックリスト:

- [ ] `input_schema` で必須フィールドと型を明示した
- [ ] allowlist / パス正規化など、副作用の境界を `execute` 内で強制した
- [ ] 秘密情報を戻り値やログに出さない
- [ ] Cloud が必要なら同じ機能を MCP でも提供する設計にした

## Custom tools vs MCP vs Subagents

| 機構         | 実行場所                                        | 向き                             |
| ------------ | ----------------------------------------------- | -------------------------------- |
| Custom tools | 呼び出し元 Python プロセス                      | そのプロセスだけの API・状態     |
| MCP          | stdio/HTTP サーバー（local マシン or Cloud VM） | 共有・言語非依存・Cloud でも必要 |
| Subagents    | Agent ランタイム内の別エージェント              | 役割分担・長い専門プロンプト     |

同じ Agent に custom tools と MCP と subagents を併用できる。重複する能力を両方に晒さない。

## よくある落とし穴

1. **Cloud で `custom_tools` を渡す** — 無視またはエラー。Cloud では MCP へ移す
2. **スキーマなしで曖昧な引数** — Agent が壊れた引数を渡しやすい。`input_schema` を書く
3. **長時間ブロックする `execute`** — 呼び出し元プロセスを止める。重い処理はタイムアウトか非同期ジョブ化
4. **resume 後に関数が消える** — custom tools はプロセス内の callable。`Agent.resume()` するプロセスでも同じ `custom_tools` を再度渡す

## 関連

- 公式スナップショット: [references/python-sdk.md](references/python-sdk.md) の Custom tools 節
- MCP: [mcp.md](mcp.md)
- Subagents: [subagents.md](subagents.md)
