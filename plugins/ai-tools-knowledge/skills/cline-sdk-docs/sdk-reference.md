# Cline SDK 実装リファレンス

このファイルは、`cline-sdk-docs/SKILL.md` から必要な節だけを読むための実装寄りの要約。APIの完全な型定義や最新の仕様変更を代替しない。各節末の公式 URL と、[sdk-reference-map.md](sdk-reference-map.md) の対応表を使って一次資料へ進む。

## 目次

- [パッケージ選択](#パッケージ選択)
- [最小のAgent](#最小のagent)
- [Agentのライフサイクルと結果](#agentのライフサイクルと結果)
- [イベントとストリーミング](#イベントとストリーミング)
- [カスタムツール](#カスタムツール)
- [権限](#権限)
- [ClineCoreとセッション](#clinecoreとセッション)
- [プロバイダーと使用量](#プロバイダーと使用量)
- [プラグイン](#プラグイン)
- [本番運用の最低限](#本番運用の最低限)
- [公式ページ](#公式ページ)

## パッケージ選択

迷ったら `@cline/sdk` から import する。これは公開SDKの入口で、主なパッケージを再エクスポートする。

| 目的                                                          | 入口                          | 判断                                                |
| ------------------------------------------------------------- | ----------------------------- | --------------------------------------------------- |
| 1回の推論、短い会話、独自ツールを持つ stateless agent         | `Agent` from `@cline/sdk`     | まずこれを使う。`run` の結果を呼び出し元で処理する  |
| セッション、メッセージ永続化、組み込みツール、Hub、Automation | `ClineCore` from `@cline/sdk` | セッションIDを持つアプリや長時間サービス向け        |
| ブラウザー互換の低レベルな実行ループ                          | `@cline/agents`               | `Agent` / `AgentRuntime` を直接扱う必要がある時だけ |
| プロバイダー一覧、モデル選択、Gateway                         | `@cline/llms`                 | エージェント実行ではなくモデル層を直接制御する時    |
| 共通型・スキーマ・ヘルパー                                    | `@cline/shared`               | 直接利用が必要な場合だけ                            |

公式のインストール要件は Node.js 22 以上。

```bash
npm install @cline/sdk
```

Zodスキーマを使うカスタムツールでは、プロジェクトの依存関係にも `zod` を追加する。

出典: [SDK overview](https://docs.cline.bot/sdk/overview)、[Packages](https://docs.cline.bot/sdk/architecture/overview)

## 最小のAgent

`Agent` は `providerId`、`modelId`、必要なら `apiKey` を受け取り、`run` で実行する。APIキーやトークンをソースへ書かない。

```typescript
import { Agent } from "@cline/sdk";

const agent = new Agent({
  providerId: "anthropic",
  modelId: "claude-sonnet-4-6",
  apiKey: process.env.ANTHROPIC_API_KEY,
  systemPrompt: "Answer concisely and cite relevant files.",
  maxIterations: 5,
});

const unsubscribe = agent.subscribe((event) => {
  if (event.type === "assistant-text-delta") {
    process.stdout.write(event.text ?? "");
  }
});

try {
  const result = await agent.run(
    "Explain the authentication flow in this repository.",
  );
  if (result.status === "failed") {
    throw result.error ?? new Error("Agent run failed");
  }
  console.error(`\niterations=${result.iterations}`);
} finally {
  unsubscribe();
}
```

`modelId` は利用するプロバイダーのモデルIDに置き換える。モデル名、認証方法、`baseUrl`、`headers` はプロバイダーごとに異なるため、実際の組み合わせを公式の [Model Providers](https://docs.cline.bot/sdk/model-providers) で確認する。

## Agentのライフサイクルと結果

直接 `Agent` を使う時にまず説明するAPIは次の通り。

| API                   | 用途                                           |
| --------------------- | ---------------------------------------------- |
| `run(input)`          | 新しい実行を開始                               |
| `continue(input?)`    | 現在の会話を追加入力で継続                     |
| `abort(reason?)`      | 実行中の処理を中断                             |
| `subscribe(listener)` | `AgentRuntimeEvent` を購読。解除関数を保持する |
| `restore(messages)`   | 会話履歴を置き換えて復元                       |
| `snapshot()`          | 現在の状態・反復回数・使用量を取得             |

`run` の結果は少なくとも `status`（`completed` / `aborted` / `failed`）、`outputText`、`messages`、`iterations`、`usage` を見る。失敗時は `error` も確認する。成功したように見えるテキストだけで判定せず、`status` と使用量をログへ残す。

## イベントとストリーミング

`Agent` では `agent.subscribe` を使う。UIやログでは、テキストの差分だけでなくツール開始・終了と実行終了も扱う。

```typescript
agent.subscribe((event) => {
  switch (event.type) {
    case "assistant-text-delta":
      ui.appendText(event.text ?? "");
      break;
    case "tool-started":
      ui.showToolStart(event.toolCall.toolName);
      break;
    case "tool-finished":
      ui.showToolEnd(event.toolCall.toolName);
      break;
    case "run-finished":
      ui.showResult(event.result.status);
      break;
    case "usage-updated":
      metrics.recordTokens(event.usage.inputTokens, event.usage.outputTokens);
      break;
  }
});
```

`ClineCore` のセッション側では `cline.subscribe(listener, { sessionId })` を使い、`content_*`、`iteration_*`、`usage`、`done`、`error` などの host-facing event を扱う。低レベル `AgentRuntimeEvent` と `ClineCore` の `CoreSessionEvent` を混同しない。

出典: [Events](https://docs.cline.bot/sdk/events)、[Events reference](https://docs.cline.bot/sdk/reference/events)

## カスタムツール

最小形は `createTool`、Zodスキーマ、`execute`。名前と説明はモデルのツール選択に使われるため、何をするか・いつ使うか・何を返すか・制約を具体的に書く。

```typescript
import { Agent, createTool } from "@cline/sdk";
import { z } from "zod";

const searchOrders = createTool({
  name: "search_orders",
  description:
    "Search orders with a read-only query. Use for order history lookup; returns at most 50 rows.",
  inputSchema: z.object({
    customerId: z.string().describe("Customer identifier."),
    limit: z
      .number()
      .int()
      .min(1)
      .max(50)
      .default(10)
      .describe("Maximum number of rows."),
    status: z
      .enum(["open", "closed"])
      .optional()
      .describe("Optional order status filter."),
  }),
  async execute(input) {
    const rows = await orderStore.search(input);
    return { rows };
  },
});

const agent = new Agent({
  providerId: "anthropic",
  modelId: "claude-sonnet-4-6",
  apiKey: process.env.ANTHROPIC_API_KEY,
  tools: [searchOrders],
});
```

実装上の要点:

- 固定値は `z.enum`、数値範囲は `min` / `max` で制限し、各入力フィールドに `.describe()` を付ける。
- 長い処理は `context.signal?.aborted` を確認して中断可能にする。
- 外部APIやDBの失敗は、可能なら `{ output: { error: "..." }, isError: true }` のような構造化データで返す。例外を投げると mistake として数えられる。
- 成功条件をツール呼び出しで明示したい場合は `lifecycle: { completesRun: true }` を付ける。
- ツールはエージェントへ渡す前に単体テストし、書き込み・シェル・ネットワーク・秘密情報へのアクセスは入力検証と最小権限を適用する。

`ClineCore.start` では `config.extraTools`、`Agent` では `tools`、プラグインでは `api.registerTool` で登録する。

出典: [Creating Custom Tools](https://docs.cline.bot/sdk/guides/creating-custom-tools)、[Tools API](https://docs.cline.bot/sdk/reference/tools-api)

## 権限

`toolPolicies` にないツールは、公式ガイドの説明では既定で有効かつ自動承認される。外部作用のあるツールを使う場合は、暗黙の既定値に依存せず明示する。

```typescript
const agent = new Agent({
  // providerId, modelId, apiKey, tools ...
  toolPolicies: {
    search_orders: { autoApprove: true },
    write_order: { autoApprove: false },
    run_commands: { enabled: false },
  },
});
```

`autoApprove: false` は承認待ち、`enabled: false` はモデルから見えない状態。信頼できるサンドボックス内のバッチだけで全自動承認を検討し、一般ユーザーの入力や本番環境では、ツールごとの承認コールバック・許可ディレクトリ・コマンド allowlist を設ける。

出典: [Permission Handling](https://docs.cline.bot/sdk/guides/permission-handling)

## ClineCoreとセッション

セッションを保存・再開したり、HubやAutomationを使ったりする場合は `ClineCore` を選ぶ。

```typescript
import { ClineCore } from "@cline/sdk";

const cline = await ClineCore.create({
  clientName: "review-service",
  backendMode: "auto",
});

const session = await cline.start({
  prompt: "Summarize this repository and list risky changes.",
  config: {
    providerId: "anthropic",
    modelId: "claude-sonnet-4-6",
    apiKey: process.env.ANTHROPIC_API_KEY,
    cwd: process.cwd(),
    workspaceRoot: process.cwd(),
    enableTools: true,
  },
});

const followUp = await cline.send({
  sessionId: session.sessionId,
  prompt: "Now inspect the authentication module.",
});

await cline.dispose("request complete");
```

`ClineCore.create` の `backendMode` は `auto` / `local` / `hub` / `remote`。`start` は `sessionId`、マニフェスト、メッセージ保存先、結果を返す。よく使うセッションAPIは `subscribe`、`get`、`readMessages`、`getAccumulatedUsage`、`abort`、`stop`、`delete`、`restore`、`dispose`。

常駐サービスでは終了シグナルで `dispose` を呼ぶ。単発のリクエスト/レスポンスなら `Agent`、再起動をまたぐ状態管理なら `ClineCore` という切り分けを維持する。

出典: [ClineCore reference](https://docs.cline.bot/sdk/reference/cline-core)、[Hub & Spoke](https://docs.cline.bot/sdk/architecture/hub-spoke)

## プロバイダーと使用量

通常は `Agent` の `providerId` / `modelId` を指定する。OpenAI互換プロバイダーは `providerId: "openai-compatible"` と `baseUrl: "https://provider.example/v1"` の組み合わせを使う。Bedrockなどは標準の環境変数・SDK認証チェーンと provider-specific config を使う。

```typescript
const agent = new Agent({
  providerId: "openai-compatible",
  modelId: "your-model-id",
  apiKey: process.env.PROVIDER_API_KEY,
  baseUrl: process.env.PROVIDER_BASE_URL,
});
```

`@cline/llms` の `DefaultGateway` / `createGateway` は、プロバイダーやモデルを直接列挙・生成したい場合に使う。結果や `usage-updated` イベントには入力・出力トークンや `totalCost` が含まれるため、反復回数・トークン上限・アプリ側の費用上限を設ける。

出典: [Model Providers](https://docs.cline.bot/sdk/model-providers)、[Gateway reference](https://docs.cline.bot/sdk/reference/gateway)

## プラグイン

複数のツール、hooks、commands、eventsを再配布するならプラグインにする。SDK/CLI/Kanban向けのプラグイン実装、`AgentPlugin`、`package.json` の `cline` フィールド、配布形式は [cline-plugin-writer の plugin-reference.md](../cline-plugin-writer/plugin-reference.md) に集約している。単一ツールを1つのエージェントだけで使うなら、まず `Agent` の `tools` または `ClineCore.start` の `extraTools` で十分。

## 本番運用の最低限

- 失敗を `Agent` の `status`、`ClineCore` の `finishReason` で判定し、エラー・反復回数・使用量を構造化ログへ残す。
- `maxIterations`、必要なら `maxTokensPerTurn`、タイムアウト、連続 mistake の上限を設定する。
- ツール入力をユーザー入力と同じように扱い、パスの traversal、危険なシェル、許可外のネットワーク先を検証する。
- APIキーは環境変数または秘密管理へ置き、ログ・イベント・ツール結果へ出さない。
- `Agent` の stateless worker と `ClineCore` の persistent service を運用要件に合わせて選ぶ。

出典: [Going to Production](https://docs.cline.bot/sdk/guides/going-to-production)

## 公式ページ

主要ページは次の通り。ページが増えた場合や URL が変わった場合は [sdk-reference-map.md](sdk-reference-map.md) を先に更新する。

- [SDK overview](https://docs.cline.bot/sdk/overview)
- [Building an Agent](https://docs.cline.bot/sdk/guides/building-an-agent)
- [Agent reference](https://docs.cline.bot/sdk/reference/agent)
- [ClineCore reference](https://docs.cline.bot/sdk/reference/cline-core)
- [Creating Custom Tools](https://docs.cline.bot/sdk/guides/creating-custom-tools)
- [Events](https://docs.cline.bot/sdk/events)
- [Permission Handling](https://docs.cline.bot/sdk/guides/permission-handling)
- [Model Providers](https://docs.cline.bot/sdk/model-providers)
- [Going to Production](https://docs.cline.bot/sdk/guides/going-to-production)

最新情報の確認が必要な場合は、`cline-docs/SKILL.md` の `output/llms.txt` → 該当ページ抽出 → 必要なら公式URL直接確認、の順で調査する。`cline-cli-docs/SKILL.md` のヘルプスナップショットは `cline` コマンドの仕様確認用であり、SDKの型や実行結果の根拠にはしない。
