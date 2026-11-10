# Hooks を Python SDK から使う

<!-- 2026-07-29 時点の https://cursor.com/docs/sdk/python.md#hooks および https://cursor.com/docs/hooks.md に基づく。更新時は references/ も差し替え、cursor-docs で最新を確認すること -->

Hooks は **プログラムの callback ではない**。`.cursor/hooks.json`（とスクリプト）によるファイルベースのポリシー境界であり、SDK の `Agent.create()` / `agent.send()` にフック関数を渡す API はない。

Python SDK でやることは次の2点だけ:

1. Hooks を **エージェントが読む作業ツリー** に置く
2. そのツリーを `local.cwd` または `cloud.repos` に渡して Agent を起動する

## 配置とランタイム

| ランタイム | どこに置くか                                                   | 読み込まれるもの                                                                                              |
| ---------- | -------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------- |
| Local      | `local.cwd` 配下の `.cursor/hooks.json`                        | プロジェクト hooks。加えて `~/.cursor/hooks.json`（ユーザー）も対象                                           |
| Cloud      | `cloud.repos` で clone されるリポジトリの `.cursor/hooks.json` | プロジェクト hooks。Enterprise では team / enterprise-managed hooks も。**`~/.cursor/hooks.json` は使えない** |

- Cloud は **command-based hooks のみ**（prompt-based は不可）
- Cloud で動かないイベントもある（`sessionStart` / `sessionEnd` / MCP hooks / Tab / `workspaceOpen` など）。対応表は [references/hooks.md](references/hooks.md)
- Cloud の初期 read-only ターンでは hooks は走らない。書き込み可能な環境になってから開始する

## 最小構成（プロジェクト hooks）

リポジトリ側:

```text
repo/
  .cursor/
    hooks.json
    hooks/
      block_rm.py
```

```json
{
  "version": 1,
  "hooks": {
    "beforeShellExecution": [
      {
        "command": "python .cursor/hooks/block_rm.py",
        "timeout": 10
      }
    ]
  }
}
```

```python
# .cursor/hooks/block_rm.py
# stdin: hook 入力 JSON / stdout: 結果 JSON / exit 0 = 成功, 2 = deny 相当
import json
import sys

payload = json.load(sys.stdin)
command = payload.get("command") or ""

if "rm -rf" in command or command.strip().startswith("rm "):
    json.dump(
        {
            "continue": True,
            "permission": "deny",
            "agent_message": f"Destructive shell blocked by hook: {command!r}",
        },
        sys.stdout,
    )
    sys.exit(0)

json.dump({"continue": True, "permission": "allow"}, sys.stdout)
```

プロジェクト hooks の `command` は **リポジトリルート相対**（`.cursor/hooks/...`）。ユーザー hooks（`~/.cursor/hooks.json`）では `./hooks/...` のようにホーム配下相対になる。

## Python SDK 側の起動

Local — `cwd` がその hooks を含むリポジトリであること:

```python
import os
from pathlib import Path

from cursor_sdk import Agent, LocalAgentOptions

repo = Path("/path/to/repo")  # .cursor/hooks.json がある場所

with Agent.create(
    model="<discovered-model-id>",
    api_key=os.environ["CURSOR_API_KEY"],
    local=LocalAgentOptions(cwd=str(repo)),
) as agent:
    # Agent が shell を叩くと beforeShellExecution が走る
    result = agent.send("List files then explain the layout").wait()
    print(result.status, result.result)
```

Cloud — hooks とスクリプトを **commit 済み** のリポジトリを渡す:

```python
import os

from cursor_sdk import Agent, CloudAgentOptions, CloudRepository

with Agent.create(
    model="<discovered-model-id>",
    api_key=os.environ["CURSOR_API_KEY"],
    cloud=CloudAgentOptions(
        repos=[
            CloudRepository(
                url="https://github.com/your-org/your-repo",
                starting_ref="main",
            )
        ],
    ),
) as agent:
    result = agent.send("Refactor the auth middleware safely").wait()
    print(result.status)
```

未コミットのローカル `.cursor/hooks.json` だけを Cloud に期待しない。VM は clone した内容しか見ない。

## 設定変更後の再読込

同じ Agent を閉じずに hooks / プロジェクト MCP / ファイル定義 subagent を読み直す:

```python
agent.reload()
```

`reload` は dispose しない。長期稼働プロセスで hooks をホットリロードしたいときに使う。

## よくある落とし穴

1. **SDK に hook 関数を渡そうとする** — API はない。ファイルを置け。
2. **Local の `cwd` と hooks の場所がずれている** — 別ディレクトリを `cwd` にするとプロジェクト hooks は効かない。
3. **Cloud でユーザー hooks を期待する** — `~/.cursor/hooks.json` は Cloud VM に無い。
4. **Cloud で prompt-based hook を使う** — 非対応。command-based に書き換える。
5. **スクリプトのパスを間違える** — プロジェクト hooks はプロジェクトルートから実行される。`.cursor/hooks/...` を使う。
6. **fail-open** — 多くの hook は exit code が 0/2 以外だとアクションが通る。ブロックしたいなら exit `2` か JSON の `permission: "deny"` を明示する。

## 関連

- 公式スナップショット: [references/hooks.md](references/hooks.md)、SDK 側の一文: [references/python-sdk.md](references/python-sdk.md) の Hooks 節
- Hooks のイベント一覧・入出力スキーマの最新は **cursor-docs**（https://cursor.com/docs/hooks.md）
- Subagents と組み合わせる場合は [subagents.md](subagents.md)（`subagentStart` / `subagentStop` も hooks 側で観測できる）
