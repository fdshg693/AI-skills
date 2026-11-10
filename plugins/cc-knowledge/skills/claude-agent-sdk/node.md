# Node.js / TypeScript版 Claude Agent SDK

Claude Codeをライブラリとして組み込むNode.js/TypeScriptアプリケーションの設計・実装・レビュー・トラブルシューティングに使う。SDKのAPIや挙動は変わり得るため、記憶だけで回答せず、必ず `claude-code-docs` スキルが管理する公式ドキュメントを確認する。

## 対象範囲

- パッケージは `@anthropic-ai/claude-agent-sdk`、Node.js 18以上を前提にする。
- TypeScriptの型、async iterator、セッション、ストリーミング、権限、フック、MCP、カスタムツール、サブエージェント、Agent Skills、構造化出力、コスト・運用・デプロイを扱う。
- Python SDKのAPI名（`ClaudeAgentOptions`、snake_caseのオプション等）やコード例を混ぜない。

## 公式情報を確認する手順

SDK スキルの起動時に `llms.txt` の小さな索引だけが更新される。`llms-full.txt` は取得しない。必要なページを選び、ページ単位のキャッシュへ保存してから検索する。

```text
python ${CLAUDE_SKILL_DIR}/scripts/webref_cli.py download \
  --slug agent-sdk/typescript \
  --slug agent-sdk/quickstart
python ${CLAUDE_SKILL_DIR}/scripts/webref_cli.py grep "allowedTools|permissionMode|outputFormat" --ignore-case
```

最初に読むページは `agent-sdk/typescript`（型・camelCase）、`agent-sdk/quickstart`（最小構成）、`agent-sdk/streaming-vs-single-mode`（入力方式）である。要件に応じて `sessions`、`permissions`、`hooks`、`mcp`、`custom-tools`、`structured-outputs`、`hosting`、`secure-deployment` などを追加取得する。全ページの用途と検索キーは同梱の `reference-map.md` にある。

検索結果の Source URL を回答に示す。キャッシュに無い仕様は推測せず、`index` で索引を更新してから必要な slug を取得する。索引にも無い場合は `claude-code-docs` スキルへフォールバックする。

## セットアップと最小ループ

新規TypeScriptプロジェクトでは、ES module設定と実行用の `tsx` を用意する。既存のCommonJSプロジェクトでは `agent.mts` を使う方法も公式Quickstartで確認する。

```bash
npm init -y
npm pkg set type=module
npm install @anthropic-ai/claude-agent-sdk
npm install --save-dev tsx
```

SDKはClaude Codeのネイティブバイナリをoptional dependencyとして同梱する。パッケージマネージャーがoptional dependencyを省略していないか、SDKとバンドルCLIのバージョンが機能要件を満たすかを確認する。APIキーは実行プロセスの環境変数へ渡し、`.env` は自動ロードを前提にしない。

```typescript
import { query } from "@anthropic-ai/claude-agent-sdk";

for await (const message of query({
  prompt: "コードベースのTODOを調べ、要約してください。",
  options: {
    allowedTools: ["Read", "Glob", "Grep"],
    maxTurns: 10,
  },
})) {
  if (message.type === "assistant" && message.message?.content) {
    for (const block of message.message.content) {
      if ("text" in block) {
        console.log(block.text);
      }
    }
  } else if (message.type === "result") {
    console.log(`終了: ${message.subtype}`);
  }
}
```

`query()` はメッセージをストリームするasync iteratorで、`prompt`には文字列または `AsyncIterable<SDKUserMessage>` を渡せる。表示用テキストだけでなくツール呼び出し、システムメッセージ、最終結果を保存するかを先に決め、`result` メッセージの `subtype` と例外を捨てない。

## オプションと設計判断

TypeScriptではオプション名をcamelCaseで書く。`allowedTools`（確認なしで許可）、`tools`（利用可能なツール設定）、`disallowedTools`（禁止）、`permissionMode`、`canUseTool`、`systemPrompt`、`cwd`、`maxTurns`、`mcpServers`、`hooks`、`outputFormat`、`resume`、`continue`、`settingSources`、`skills`、`agents`、`abortController`、`enableFileCheckpointing` の現在の型と既定値は `agent-sdk/typescript` で確認する。

- 独立した一回限りの処理には、文字列promptで `query()` を使う。
- 複数ターン、動的入力、画像添付、途中の割り込み、入力キューが必要なら、`AsyncIterable<SDKUserMessage>` を使うストリーミング入力を選ぶ。
- 継続・resume・fork・外部保存が必要なら `agent-sdk/sessions` と `agent-sdk/session-storage` を確認する。
- `allowedTools` は利用可能なツールを限定する設定ではない。未許可の呼び出しは `permissionMode` や `canUseTool` に進むため、禁止には `disallowedTools` を使う。

## MCP、構造化出力、フック

- TypeScriptのカスタムMCPは `tool()` と `createSdkMcpServer()` を使う。ツール入力はZod schemaで定義し、実処理側でも認証、認可、入力検証、タイムアウト、レート制限、監査を行う。
- 自由文を正規表現で解析せず、`outputFormat: { type: "json_schema", schema: ... }` を使う。ZodからJSON Schemaを生成する場合は公式例に合わせてdraft-07を指定し、`structured_output` の存在と `result` の `subtype` を確認する。
- フックのイベント名、callbackの引数、タイムアウト、例外、allow/deny/deferの意味を推測しない。広い自動承認や `bypassPermissions` を本番・未隔離環境で使わない。

## 安全性、運用、トラブルシューティング

- `cwd`、環境変数、MCP資格情報、ファイルシステム、ネットワークをテナントごとに分離し、外部入力をプロンプト・シェル・パス・MCP引数へ直接連結しない。
- 本番化ではSDKが起動するClaude Codeプロセス、コンテナやサンドボックス、セッション永続化、観測性、キャンセル、リソース上限、秘密管理を `hosting` / `secure-deployment` で確認する。
- ストリーミング入力のgeneratorで例外が起きると、元の例外ではなく `Claude Code process aborted by user` のように見えることがある。generator内のファイルI/Oや外部I/Oを先に確認する。
- `Native CLI binary ... not found` はoptional dependency、対象プラットフォーム、`pathToClaudeCodeExecutable` を確認する。APIキー、権限待ち、MCP接続、`maxTurns`、構造化出力のSchemaと結果subtypeも順に切り分ける。

完了時には、TypeScriptのimport、camelCaseのオプション名、async iteratorの処理が一貫し、API選択、権限、セッション境界、失敗時の扱い、参照した公式Source URLが明示されていることを確認する。
