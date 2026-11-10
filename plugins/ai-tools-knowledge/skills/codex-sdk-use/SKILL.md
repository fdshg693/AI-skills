---
name: codex-sdk-use
description: Use when explaining or implementing programmatic control of local Codex agents with the official Codex SDK — the TypeScript library (@openai/codex-sdk) or the Python library (openai-codex). Covers installation, authentication, thread lifecycle, run/streamed turns, structured output, and sandbox/approval options. Do not use for one-shot shell delegation to the CLI (use codex-cli-use) or general Codex specification questions (use codex-docs).
meta:
  tag: []
  requires_repo_tools: none
  requires_env: CODEX_API_KEY
  dependencies: "@openai/codex-sdk, openai-codex, zod-to-json-schema"
  requires_install: npm install @openai/codex-sdk, pip install openai-codex
  requires_hooks: none
  requires_skills: codex-cli-use, codex-docs
  status: stable
  description: no description
  version: 1.0.3
---

# Codex SDK 利用ガイド

OpenAI公式のCodex SDKで、ローカルのCodexエージェントをアプリケーションやCI/CDからプログラム的に操作する。TypeScriptライブラリ（`@openai/codex-sdk`）とPythonライブラリ（`openai-codex`）の2系統がある。単発のシェル委譲（`codex exec`）は codex-cli-use、Codex全般の仕様調査は codex-docs の対象とする。

## 使い分け

- **Codex SDK**: コーディング中心のCodexスレッドを自分のアプリ・CI/CDパイプライン・内部ツールに埋め込む場合
- **`codex exec`（codex-cli-use）**: シェルやCIからの単発・非対話実行で十分な場合
- **Codex CLI を MCP サーバー化 + Agents SDK**: Codexが大きなオーケストレーション内の1専門家にすぎない場合（`https://developers.openai.com/codex/guides/agents-sdk` を参照）

## 実行前の確認

- TypeScript: Node.js 18 以上が必要。サーバーサイド専用
- Python: Python 3.10 以上が必要
- 認証: SDKは既存のCodex認証（`codex login` 済みのセッション）を自動で再利用する。未認証なら `codex login status` で確認し、codex-cli-use の手順でログインする。APIキーやアクセストークンをソースコード・ログ・プロンプトに直接埋め込まない

## TypeScript SDK（`@openai/codex-sdk`）

Codex CLI（`@openai/codex`）を子プロセスとして起動し、stdin/stdoutのJSONLイベントでやり取りするラッパー。

### インストール

```bash
npm install @openai/codex-sdk
```

### 基本形

```ts
import { Codex } from "@openai/codex-sdk";

const codex = new Codex();
const thread = codex.startThread();
const turn = await thread.run("Diagnose the test failure and propose a fix");

console.log(turn.finalResponse);
console.log(turn.items);
```

`run()` はターン完了までイベントをバッファし、`{ items, finalResponse, usage }` を返す。同じ `Thread` インスタンスで `run()` を繰り返すと会話が継続する。

### スレッドの再開

スレッドは `~/.codex/sessions` に永続化される。`thread.id`（最初のターン開始後に設定される）を保存しておき、`resumeThread()` で再開する。

```ts
const savedThreadId = process.env.CODEX_THREAD_ID!;
const thread = codex.resumeThread(savedThreadId);
await thread.run("Implement the fix");
```

### ストリーミング

途中経過（ツール呼び出し、ストリーミング応答、ファイル変更通知）に反応する場合は `runStreamed()` を使う。構造化イベントの非同期ジェネレータを返す。

```ts
const { events } = await thread.runStreamed(
  "Diagnose the test failure and propose a fix",
);

for await (const event of events) {
  switch (event.type) {
    case "item.completed":
      console.log("item", event.item);
      break;
    case "turn.completed":
      console.log("usage", event.usage);
      break;
  }
}
```

イベント型: `thread.started` / `turn.started` / `turn.completed` / `turn.failed` / `item.started` / `item.updated` / `item.completed` / `error`。

### 構造化出力

ターンごとにJSONスキーマを渡すと、それに従ったJSON応答を得られる。

```ts
const schema = {
  type: "object",
  properties: {
    summary: { type: "string" },
    status: { type: "string", enum: ["ok", "action_required"] },
  },
  required: ["summary", "status"],
  additionalProperties: false,
} as const;

const turn = await thread.run("Summarize repository status", {
  outputSchema: schema,
});
console.log(turn.finalResponse);
```

Zodスキーマは `zod-to-json-schema` パッケージで `target: "openAi"` を指定して変換する。`TurnOptions` はこのほか中断用の `signal: AbortSignal` を受け付ける。

### 画像入力

```ts
const turn = await thread.run([
  { type: "text", text: "Describe these screenshots" },
  { type: "local_image", path: "./ui.png" },
  { type: "local_image", path: "./diagram.jpg" },
]);
```

テキスト要素は結合されて最終プロンプトになり、画像要素はCLIの `--image` に渡される。

### スレッドオプション（`startThread()` / `resumeThread()` の `ThreadOptions`）

| オプション              | 型                                                           | 用途                                                        |
| ----------------------- | ------------------------------------------------------------ | ----------------------------------------------------------- |
| `model`                 | string                                                       | モデルID                                                    |
| `sandboxMode`           | `"read-only"` / `"workspace-write"` / `"danger-full-access"` | ファイルシステム権限                                        |
| `approvalPolicy`        | `"never"` / `"on-request"` / `"on-failure"` / `"untrusted"`  | 承認ポリシー                                                |
| `workingDirectory`      | string                                                       | 作業ディレクトリ（既定はカレント。原則Gitリポジトリが必須） |
| `skipGitRepoCheck`      | boolean                                                      | Gitリポジトリチェックを省略する                             |
| `modelReasoningEffort`  | `"minimal"` / `"low"` / `"medium"` / `"high"` / `"xhigh"`    | 推論量                                                      |
| `networkAccessEnabled`  | boolean                                                      | ネットワークアクセスを許可する                              |
| `webSearchMode`         | `"disabled"` / `"cached"` / `"live"`                         | Web検索モード                                               |
| `webSearchEnabled`      | boolean                                                      | Web検索を有効化する                                         |
| `additionalDirectories` | string[]                                                     | 追加でアクセスを許可するディレクトリ                        |

### `Codex` コンストラクタオプション（`CodexOptions`）

| オプション          | 用途                                                                                                                       |
| ------------------- | -------------------------------------------------------------------------------------------------------------------------- |
| `codexPathOverride` | 使用するcodex CLI実行ファイルのパス                                                                                        |
| `baseUrl`           | `--config openai_base_url=...` としてCLIに渡される                                                                         |
| `apiKey`            | APIキー（`CODEX_API_KEY` としてCLIに注入される）                                                                           |
| `config`            | 追加の `--config key=value` オーバーライド。ネストしたオブジェクトはドット区切りに平坦化され、値はTOMLリテラルに変換される |
| `env`               | CLIプロセスへ渡す環境変数。指定すると `process.env` の継承をやめる（SDKが必要な変数は引き続き注入される）                  |

```ts
const codex = new Codex({
  config: {
    show_raw_agent_reasoning: true,
    sandbox_workspace_write: { network_access: true },
  },
});
```

重複する設定では、グローバルの `config` オーバーライドよりスレッドオプションが優先される（後から出力されるため）。

## Python SDK（`openai-codex`）

ローカルのCodex app-serverをJSON-RPCで制御する。公開ビルドは固定バージョンのCLIランタイム（`openai-codex-cli-bin`）を自動インストールする。特定のローカル実行ファイルを使いたい場合だけ `CodexConfig(codex_bin=...)` を渡す。ベータ期間中は `pip install openai-codex` が最新の公開ベータビルドを選択する。

### インストール

```bash
pip install openai-codex
```

### 基本形

```python
from openai_codex import Codex, Sandbox

with Codex() as codex:
    thread = codex.thread_start(
        model="gpt-5.4",
        sandbox=Sandbox.workspace_write,
    )
    result = thread.run("Make a plan to diagnose and fix the CI failures")
    print(result.final_response)
```

`thread.run(...)` はターンを開始して完了を待ち、`TurnResult` を返す。主なフィールドは `id` / `status` / `error` / `started_at` / `completed_at` / `duration_ms` / `final_response` / `items` / `usage`。文字列は `TextInput(...)` の省略形である。

非同期アプリケーションでは `AsyncCodex` を使う。

```python
import asyncio

from openai_codex import AsyncCodex


async def main() -> None:
    async with AsyncCodex() as codex:
        thread = await codex.thread_start(model="gpt-5.4")
        result = await thread.run("Implement the plan")
        print(result.final_response)


asyncio.run(main())
```

### 認証

既存のCodex認証を自動で再利用する。明示的にログインする場合:

```python
with Codex() as codex:
    codex.login_api_key("sk-...")          # APIキー
    login = codex.login_chatgpt()          # ChatGPTブラウザログイン
    print(login.auth_url)
    print(login.wait().success)
```

デバイスコード方式は `login_chatgpt_device_code()` を使い、`verification_url` と `user_code` を表示して `wait()` で完了を待つ。

### サンドボックス

スレッド作成時と、後のターンでの変更時に、同じ `Sandbox` プリセットを使う。

```python
from openai_codex import Codex, Sandbox

with Codex() as codex:
    thread = codex.thread_start(sandbox=Sandbox.workspace_write)
    thread.run("Make the requested change.")
    review = thread.run("Review the diff only.", sandbox=Sandbox.read_only)
```

- `Sandbox.read_only`: 書き込みを許可せず読み取りのみ
- `Sandbox.workspace_write`: ワークスペースと設定済みの書き込みルート内で書き込み可
- `Sandbox.full_access`: ファイルシステム制限なし

`sandbox=` を省略するとapp-serverの設定済みデフォルトが使われる。`run(...)` / `turn(...)` に渡したサンドボックスは、そのターンとスレッド上の以降のターンに適用される。

### スレッド操作（`Codex` / `AsyncCodex`）

- `thread_start(...)`: 新規スレッド。主な引数は `model` / `sandbox` / `cwd` / `approval_mode`（既定 `ApprovalMode.auto_review`）/ `config` / `base_instructions` / `developer_instructions` / `ephemeral` / `model_provider` / `personality`
- `thread_resume(thread_id, ...)`: 保存済みスレッドを再開する
- `thread_fork(thread_id, ...)`: 既存スレッドをフォークする
- `thread_list(...)` / `thread_archive(thread_id)` / `thread_unarchive(thread_id)`: 一覧・アーカイブ操作
- `models()`: 接続中のランタイムで利用可能なモデル一覧

### ターンの制御と構造化出力

`thread.run(...)` / `thread.turn(...)` は `approval_mode` / `cwd` / `effort` / `model` / `output_schema` / `personality` / `sandbox` / `service_tier` / `summary` をターン単位で受け付ける。

```python
with Codex() as codex:
    thread = codex.thread_start(model="gpt-5.4", config={"model_reasoning_effort": "high"})
    result = thread.run(
        "Summarize repository status",
        output_schema={
            "type": "object",
            "properties": {
                "summary": {"type": "string"},
                "status": {"type": "string", "enum": ["ok", "action_required"]},
            },
            "required": ["summary", "status"],
            "additionalProperties": False,
        },
    )
    print(result.final_response)
```

`thread.turn(...)` は `TurnHandle` を返し、完了を待たずに `stream()`（通知のストリーミング）、`steer(...)`（ターン中の追加入力）、`interrupt()`（中断）を使える。`handle.run()` で `TurnResult` を収集する。画像入力は `LocalImageInput(path=...)`（ローカル画像）や `ImageInput(url="data:image/...")`（base64データURL。HTTP/HTTPS URLは非推奨）を使う。

APIの詳細は `help(openai_codex)` / `help(Codex)` / `python -m pydoc openai_codex` でも確認できる。

## モデル選択

モデルIDはこのリポジトリの規約（codex-cli-use）に従う。

| タスクの性質                                                                 | モデルID       |
| ---------------------------------------------------------------------------- | -------------- |
| ほとんどの実装、調査、レビュー、定型作業                                     | `gpt-5.6-luna` |
| 高度な推論が必要な設計判断、難しいバグ、セキュリティ、正確性が最重要のタスク | `gpt-5.6-sol`  |

公式ドキュメントの例に出てくる `gpt-5.4` は例示であり、そのまま使わない。利用可能なモデルはCLIの `codex debug models` またはPython SDKの `codex.models()` で確認する。

## 権限とサンドボックスの指針

自動実行では、作業内容に応じて最小限の権限を指定する。

- 読み取り・要約・レビュー: `"read-only"` / `Sandbox.read_only`
- ワークスペース内の実装: `"workspace-write"` / `Sandbox.workspace_write`
- `"danger-full-access"` / `Sandbox.full_access`: 原則として使わない。外部から完全に隔離された専用ランナーで、かつ明示的な要件がある場合だけ検討する
- 承認ポリシー: 非対話の自動実行で承認待ちにしない場合、TypeScriptは `approvalPolicy: "never"` を指定する。Pythonのスレッド開始は既定で `ApprovalMode.auto_review` であり、必要に応じて `approval_mode=` で上書きする

書き込みを伴うタスクでは、プロンプトにも「変更対象」「変更禁止範囲」「実行してよい検証」「デプロイしないこと」を明記する。完了後は呼び出し元で差分とテスト結果を確認する。

## 検証

SDKを使うコードを書いたら、環境が許す限り最小のスモークテストを実行して確認する。

- TypeScript: `npm install @openai/codex-sdk` の後、`thread.run(...)` を1ターン実行して `finalResponse` を表示する
- Python: `pip install openai-codex` の後、`with Codex() as codex:` で1ターン実行して `final_response` を表示する

認証未設定やランタイム不足で失敗する場合は、エラーメッセージをそのまま報告し、インストール・認証の手順を案内する。

## 最新仕様の調査先

このスキルの内容は公式ドキュメントのスナップショットである。詳細な仕様や最新情報が必要な場合は、次の順で調べる。

1. codex-docs スキルで公式ドキュメント（`https://developers.openai.com/codex/codex-sdk`）を引く
2. リポジトリのREADMEとソースを確認する
   - TypeScript: `https://github.com/openai/codex/tree/main/sdk/typescript`
   - Python: `https://github.com/openai/codex/tree/main/sdk/python`（`docs/api-reference.md` と実行可能な `examples/` がある）
3. このスキルの例と最新のREADMEが食い違う場合は最新情報を優先し、必要ならこのスキルを更新する

参照した公式ドキュメント:

- https://developers.openai.com/codex/codex-sdk
- https://github.com/openai/codex/blob/main/sdk/typescript/README.md
- https://github.com/openai/codex/blob/main/sdk/python/README.md
- https://github.com/openai/codex/blob/main/sdk/python/docs/getting-started.md
- https://github.com/openai/codex/blob/main/sdk/python/docs/api-reference.md
