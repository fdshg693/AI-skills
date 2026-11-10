# Python版 Claude Agent SDK

Claude Codeをライブラリとして組み込むPythonアプリケーションの設計・実装・レビュー・トラブルシューティングに使う。SDKのAPIや挙動は変わり得るため、記憶だけで回答せず、必ず `claude-code-docs` スキルが管理する公式ドキュメントを確認する。

## 対象範囲

- パッケージは `claude-agent-sdk`、importは `claude_agent_sdk`。
- Python 3.10以上を前提にし、プロジェクトの仮想環境または `uv` を使う。
- 認証、インストール、エージェントループ、組み込みツール、セッション、ストリーミング、権限、フック、MCP、カスタムツール、サブエージェント、Agent Skills、構造化出力、コスト・運用・デプロイを扱う。
- Node.js/TypeScript SDKのAPI名やコード例を混ぜない。

## 公式情報を確認する手順

SDK スキルの起動時に `llms.txt` の小さな索引だけが更新される。`llms-full.txt` は取得しない。必要なページを選び、ページ単位のキャッシュへ保存してから検索する。

```text
python ${CLAUDE_SKILL_DIR}/scripts/webref_cli.py download \
  --slug agent-sdk/python \
  --slug agent-sdk/quickstart
python ${CLAUDE_SKILL_DIR}/scripts/webref_cli.py grep "allowed_tools|permission_mode|output_format" --ignore-case
```

最初に読むページは `agent-sdk/python`（型・snake_case）、`agent-sdk/quickstart`（最小構成）、`agent-sdk/streaming-vs-single-mode`（入力方式）である。要件に応じて `sessions`、`permissions`、`hooks`、`mcp`、`custom-tools`、`structured-outputs`、`hosting`、`secure-deployment` などを追加取得する。全ページの用途と検索キーは同梱の `reference-map.md` にある。

検索結果の Source URL を回答に示す。キャッシュに無い仕様は推測せず、`index` で索引を更新してから必要な slug を取得する。索引にも無い場合は `claude-code-docs` スキルへフォールバックする。

## 最初に行う設計判断

| 要件                                             | 選ぶAPI                             |
| ------------------------------------------------ | ----------------------------------- |
| 独立した一回限りのタスク、単純な自動化           | `query()`                           |
| 同じ会話で質問を続ける、REPLやチャットUI         | `ClaudeSDKClient`                   |
| 割り込み、動的な入力、画像添付、明示的な接続管理 | `ClaudeSDKClient` + streaming input |
| 最終結果だけ必要な短い処理                       | `query()` の結果メッセージを読む    |

`query()` は非同期イテレータを返す。継続・resume・forkが必要なら `ClaudeAgentOptions` と `agent-sdk/sessions` を確認し、複数ターンや割り込みには `ClaudeSDKClient` を使う。表示用テキストだけでなくツール呼び出し・システムメッセージ・最終結果を保存するかを先に決め、`ResultMessage.subtype` とエラー型を捨てない。

```python
import asyncio

from claude_agent_sdk import (
    AssistantMessage,
    ClaudeAgentOptions,
    ResultMessage,
    TextBlock,
    query,
)


async def main() -> None:
    options = ClaudeAgentOptions(
        allowed_tools=["Read", "Glob", "Grep"],
        max_turns=10,
    )
    async for message in query(
        prompt="コードベースのTODOを調べ、要約してください。",
        options=options,
    ):
        if isinstance(message, AssistantMessage):
            for block in message.content:
                if isinstance(block, TextBlock):
                    print(block.text)
        elif isinstance(message, ResultMessage):
            print(f"終了: {message.subtype}")


asyncio.run(main())
```

## セットアップとオプション

```powershell
py -m venv .venv
.venv/Scripts/Activate.ps1
pip install claude-agent-sdk
$env:ANTHROPIC_API_KEY = "sk-ant-..."
```

SDKは `.env` を自動ロードしない。秘密情報をソース、ログ、プロンプト、コミットへ書かない。`allowed_tools`（確認なしで許可）、`tools`（コンテキストへ載せるもの）、`disallowed_tools`（禁止）を区別し、`permission_mode`、`can_use_tool`、`system_prompt`、`cwd`、`max_turns`、`mcp_servers`、`hooks`、`output_format`、`resume`、`continue_conversation`、`setting_sources`、`skills`、`agents` の現在の型と既定値は公式リファレンスで確認する。

## ストリーミング、MCP、構造化出力

- 複数入力、途中の割り込み、画像添付、ユーザー承認が必要ならストリーミング入力と `ClaudeSDKClient` を使う。`interrupt()` 後は残りの応答を `receive_response()` で読み切る。
- アプリ内関数は `@tool` と `create_sdk_mcp_server()` のインプロセスMCPで公開できる。サーバー側でも認証、認可、入力検証、タイムアウト、レート制限、監査を行う。
- 自由文を正規表現で解析せず、`output_format={"type": "json_schema", "schema": ...}` を使う。PydanticからSchemaを生成し、`structured_output` を再検証する。JSON Schemaの制限、リトライ、成功・エラーの判定は `agent-sdk/structured-outputs` で確認する。

## 安全性、運用、トラブルシューティング

- `PreToolUse` / `PostToolUse` / `Stop` / `SessionEnd` のイベント名・型・返却値を推測しない。広い自動承認を本番や未隔離のワークスペースで使わない。
- `cwd`、環境変数、MCP資格情報、ファイルシステム、ネットワークをテナントごとに分離し、外部入力をプロンプト・シェル・パス・MCP引数へ直接連結しない。
- 本番化ではサブプロセス、コンテナやサンドボックス、セッション永続化、観測性、キャンセル、リソース上限、秘密管理を `hosting` / `secure-deployment` で確認する。
- `ModuleNotFoundError` は実行中のPythonとSDKをインストールした環境が同じか確認する。APIキー、権限待ち、MCP接続、入力ジェネレーターの例外、`max_turns`、構造化出力のSchemaと結果subtypeを順に切り分ける。

完了時には、Pythonのimportとsnake_caseのオプション名が一貫し、API選択、権限、セッション境界、失敗時の扱い、参照した公式Source URLが明示されていることを確認する。
