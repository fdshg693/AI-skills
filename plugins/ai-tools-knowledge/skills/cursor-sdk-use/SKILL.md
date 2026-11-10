---
# 同梱ファイル: hooks.md / subagents.md / custom-tools.md / mcp.md（Python SDK での実践パターン）/ references/（公式ドキュメント抜粋スナップショット）
name: cursor-sdk-use
description: Use when building, reviewing, or troubleshooting Python applications that call Cursor agents through the Cursor SDK (`cursor-sdk`) — including local or cloud agents, sync or async clients, streaming, multi-turn sessions, MCP, custom tools, subagents, hooks, sandboxing, persistence, artifacts, and retries. Use the official Cursor Python SDK documentation through the cursor-docs workflow because the SDK API, models, and runtime behavior can change.
meta:
  tag: []
  requires_repo_tools: none
  requires_env: CURSOR_API_KEY
  dependencies: cursor-sdk
  requires_install: none
  requires_hooks: none
  requires_skills: cursor-docs
  status: stable
  description: no description
  version: 1.1.1
---

# Cursor Python SDK

Cursor の Agent を Python アプリケーション、CI、Bot、オーケストレーターから呼び出すときに使う。対象は PyPI パッケージ `cursor-sdk` のみとし、Cursor CLI、Cloud Agents REST API、Cursor 拡張機能 API と混同しない。

方針・ライフサイクル・デバッグは本ファイル。**Hooks / Subagents / Custom tools / MCP を実際にどう配線するか**は同梱の実践ファイルへ進む。

## 公式ドキュメントを先に確認する

実装、レビュー、デバッグの開始時に、必ず `cursor-docs` スキルを使って最新情報を確認する。

1. `cursor-plugins/meta/cursor-docs/output/llms.txt` から SDK ページを確認する。
2. Python の本文ページ `https://cursor.com/docs/sdk/python.md` を取得して、該当する節を読む。
3. 認証、MCP、Hooks、Cloud Agents、権限、料金などが関係する場合は、それぞれの公式ページも取得する。
4. ローカルの記憶や古いサンプルだけで、パッケージ名、モデル ID、引数名、戻り値の形を決めない。公式ページの取得に失敗した場合は、失敗を明示して同梱のスナップショットを使い、変動しうる点を断定しない。

公式ページにない推測で SDK の内部実装を補わない。型、例外、ストリームイベントのフィールドは、現在の公式ドキュメントとインストール済みパッケージの型・ソースを優先する。

このスキルの実践ファイル・`references/` は 2026-07-29 時点の公式ドキュメントに基づく。陳腐化しうるため、実装前は **cursor-docs** で最新を取りに行く。

## 目的別の参照先

| やりたいこと                                                 | 読むファイル                                                                                     |
| ------------------------------------------------------------ | ------------------------------------------------------------------------------------------------ |
| `.cursor/hooks.json` を Local/Cloud の SDK Agent に効かせる  | [hooks.md](hooks.md)                                                                             |
| `AgentDefinition` / `.cursor/agents/*.md` で subagent を渡す | [subagents.md](subagents.md)                                                                     |
| 呼び出し元 Python 関数を local の `custom_tools` にする      | [custom-tools.md](custom-tools.md)                                                               |
| inline / ファイル MCP、`setting_sources`、resume             | [mcp.md](mcp.md)                                                                                 |
| 公式原文の抜粋（オフライン・差分確認）                       | [references/python-sdk.md](references/python-sdk.md)、[references/hooks.md](references/hooks.md) |

SKILL 本文で足りない具体コードは、上表のファイルを読んでから実装する。

## 実装方針

### 1. ランタイムを選ぶ

- `local` は、呼び出し元のマシン上の作業ツリーを対象にする開発スクリプトや CI に使う。
- `cloud` は、リポジトリを Cursor 管理の分離 VM に clone して実行する。呼び出し元にリポジトリがない場合、並列実行、切断後も継続する処理、PR 作成に向く。
- `local` と `cloud` を同じ処理として扱い、差分（ファイルの場所、MCP、環境変数、アーティファクト、永続化、sandbox）をコードと説明に明示する。
- Python の最低バージョン、`cursor-sdk` のバージョン、利用可能なモデルは実装前に公式ドキュメントとプロジェクトの依存関係から確認する。

### 2. 認証と秘密情報を分離する

通常は `CURSOR_API_KEY` を環境変数に設定し、コードへキーを埋め込まない。ユーザー API キーまたは Service Account API キーを使い、Team Admin API キーは対応対象外として扱う。キーの種類による請求先と権限の違いを説明する。

Cloud の短命な資格情報は、エージェント全体の `env_vars` と単一 run の `send()` オプションを使い分ける。変数名、ログ、例外、プロンプトに秘密情報を出さない。`CURSOR_` で始まる環境変数を SDK のエージェント用変数として渡さない。

### 3. 型付き API を基本にする

アプリケーションコードでは、型付きの dataclass / client API を優先する。短いスクリプトや外部 JSON をそのまま渡す場合だけ辞書形式を使い、snake_case の正規化に依存する箇所を限定する。

同期処理は `Agent`、サーバー・Bot・並行オーケストレーションは `AsyncAgent` と `AsyncClient` を使う。同期と非同期のクライアントを同じ処理経路で混在させない。複数ワークスペース、bridge のライフサイクル、HTTP クライアント、タイムアウトを明示的に管理する必要がある場合は `CursorClient` / `AsyncClient` を使う。

### 4. エージェントと run のライフサイクルを管理する

- `Agent.create()` は会話状態を持つ durable な Agent を作り、`agent.send()` は一つの要求を表す Run を返す。
- 一回限りなら `Agent.prompt()` を使う。複数ターンなら同じ Agent に `send()` を続け、前の会話コンテキストを利用する。
- 同期 Agent は `with`、非同期 Agent は `async with` で確実に閉じる。長寿命サービスでは明示的な close と終了処理も用意する。
- プロセス再起動後に続ける場合は `agent_id` を保存し、`Agent.resume()` / `AsyncAgent.resume()` で再接続する。新しい `Agent.create()` は新しい会話を開始する。
- 実行中の run を並列に重ねない。必要なら `wait()`、`cancel()`、状態確認を行い、cloud の busy 状態を処理する。

最小構成の形は次のとおり。モデル ID は固定で信頼せず、実装時に `Cursor.models.list()` で確認する。

```python
import os

from cursor_sdk import Agent, LocalAgentOptions


with Agent.create(
    model="<discovered-model-id>",
    api_key=os.environ["CURSOR_API_KEY"],
    local=LocalAgentOptions(cwd="."),
) as agent:
    result = agent.send("Summarize this repository").wait()
    if result.status != "finished":
        raise RuntimeError(result.error or result.status)
    print(result.result)
```

### 5. ストリーミングと結果を正しく扱う

UI、ログ転送、進捗表示が必要な場合は `run.messages()`、`run.events()`、`run.iter_text()` の用途を選ぶ。イベントは discriminated な `type` で分岐し、assistant の text block だけをユーザー表示へ送る。最終結果は `run.text()` または `run.wait()` の結果から読む。

tool call の引数・結果は内部ツールの変更で形が変わりうるため、未知のフィールドや値を許容して防御的に扱う。ストリームの消費中に例外が起きても Agent を閉じ、必要なら run を cancel する。トークン使用量が必要な場合は run/result の `usage` を確認し、未提供をゼロと解釈しない。

### 6. モデルを発見して選ぶ

起動時またはプロセス単位で `Cursor.models.list()` を呼び、利用可能なモデル ID、パラメータ、variant を確認する。モデル ID やパラメータを盲目的にハードコードせず、能力・利用可能性で選び、必要な `ModelSelection.params` を明示する。モデルが見つからない場合は設定を再確認してからフォールバックを検討する。

## ツールと設定（要約）

詳細な配線例は同梱ファイルを読む。ここは判断用の要約のみ。

### MCP → [mcp.md](mcp.md)

- inline は `Agent.create` / `agent.send` の `mcp_servers`。`send` 側は作成時を **置き換え**（マージしない）
- Local のファイル MCP（`.cursor/mcp.json`）は `local.setting_sources` が必要。未指定は inline のみ
- Inline MCP は resume で消える。再度渡すかファイルベースにする
- Custom tools で足りる local 専用処理と、Cloud でも必要な MCP を混同しない

### Custom tools と subagents → [custom-tools.md](custom-tools.md) / [subagents.md](subagents.md)

- `custom_tools` は呼び出し元プロセスの関数。**local のみ**。Cloud では MCP へ
- 名前付き subagent は `AgentOptions.agents`（inline）または `.cursor/agents/*.md`。同名は inline 優先
- Local のファイル定義 subagent も `setting_sources` でゲートされる。Cloud は project/team/plugins を常読込
- description / prompt を狭くし、subagent の `mcp_servers` は必要な名前だけ渡す

### Hooks、sandbox、Auto-review → [hooks.md](hooks.md)

- Hooks はプログラム callback ではない。`.cursor/hooks.json` + スクリプト。SDK は `cwd` / `repos` でそのツリーを見せるだけ
- Local はプロジェクト + ユーザー hooks。Cloud はリポジトリ（と Enterprise の team/enterprise）。ユーザー hooks は Cloud に無い
- Cloud は command-based のみ。一部イベントは非対応
- 設定変更後は `agent.reload()` で hooks / プロジェクト MCP / ファイル subagent を再読込できる
- `sandbox_options` / `auto_review` は公式と型を確認。`auto_review` を強い境界にしない。強制は hooks

## デバッグと検証

1. まず `CURSOR_API_KEY`、SDK のインストール、Python バージョン、対象 workspace / repository、モデル ID を確認する。
2. 実際の変更を依頼する前に、読み取り専用の短い prompt で local / cloud の接続と結果取得を確認する。
3. run の `status`、`error`、`duration`、`usage`、Git 情報を記録し、サポートや追跡に使える `request_id` があれば併記する。API キーや prompt 内の秘密情報は記録しない。
4. `CursorSdkError` の `code`、`status`、`is_retryable`、`request_id`、`cause` を見て分類する。認証エラーはキーと権限、設定エラーはモデル・パス・ポリシー、busy は既存 run、network / rate limit は指数バックオフと上限を確認する。
5. retry は `is_retryable` と idempotency を確認してから行う。同じ副作用を二重実行しないため、書き込み操作は idempotency key、状態確認、または再実行安全な prompt を設計する。
6. 実装後は型チェック、単体テスト、最小の実 API smoke test を分ける。モデル呼び出しを単体テストの暗黙の前提にせず、課金・変更・PR 作成が発生するテストには明示的な実行条件を設ける。

## 困ったときは

1. 該当トピックの同梱ファイル（[hooks.md](hooks.md) / [subagents.md](subagents.md) / [custom-tools.md](custom-tools.md) / [mcp.md](mcp.md)）を読む
2. 一次情報の抜粋が必要なら [references/](references/)
3. 仕様が変わっている可能性がある、またはスナップショットに無い節が要る場合は **cursor-docsスキル**

## 関連ドキュメント

- [Cursor Python SDK](https://cursor.com/docs/sdk/python.md) — SDK 本文・API・例
- [Cursor SDK のドキュメント一覧](https://cursor.com/llms.txt) — `cursor-docs` が使う索引
- [MCP](https://cursor.com/docs/mcp.md) — MCP 設定の詳細
- [Hooks](https://cursor.com/docs/hooks.md) — Hooks の設定とポリシー
- [Cloud Agents API](https://cursor.com/docs/cloud-agent/api/endpoints.md) — SDK ではなく REST API が必要な場合
