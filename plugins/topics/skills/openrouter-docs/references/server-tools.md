# Server Tools

Source: `guides/features/server-tools`（Beta、API・挙動は変わりうる）

OpenRouterがサーバー側で実行するツール群。モデルが「呼ぶかどうか・何回呼ぶか」を判断し、実行はOpenRouterが行う点でPluginsやユーザー定義Tool Callingと異なる。

|                  | Server Tools           | Plugins             | User-Defined Tools     |
| ---------------- | ---------------------- | ------------------- | ---------------------- |
| 呼ぶか決めるのは | モデル                 | 常に実行            | モデル                 |
| 実行するのは     | OpenRouter             | OpenRouter          | 自アプリ               |
| 呼び出し回数     | リクエストあたり0〜N回 | リクエストあたり1回 | リクエストあたり0〜N回 |
| 指定方法         | `tools`配列            | `plugins`配列       | `tools`配列            |
| type prefix      | `openrouter:*`         | N/A                 | `function`             |

## 利用可能なServer Tools

| Tool                                                                                         | type                          | 概要                                                                                                                        |
| -------------------------------------------------------------------------------------------- | ----------------------------- | --------------------------------------------------------------------------------------------------------------------------- |
| [Web Search](https://openrouter.ai/docs/guides/features/server-tools/web-search)             | `openrouter:web_search`       | Web検索でリアルタイム情報を取得                                                                                             |
| [Datetime](https://openrouter.ai/docs/guides/features/server-tools/datetime)                 | `openrouter:datetime`         | 現在日時を取得                                                                                                              |
| [Image Generation](https://openrouter.ai/docs/guides/features/server-tools/image-generation) | `openrouter:image_generation` | テキストから画像生成                                                                                                        |
| [Web Fetch](https://openrouter.ai/docs/guides/features/server-tools/web-fetch)               | `openrouter:web_fetch`        | URLの内容を取得・抽出                                                                                                       |
| [Apply Patch](https://openrouter.ai/docs/guides/features/server-tools/apply-patch)           | `openrouter:apply_patch`      | V4A diffでファイル編集を提案（Responses API限定）                                                                           |
| [Files](https://openrouter.ai/docs/guides/features/server-tools/files)                       | `openrouter:files`            | Files API経由でワークスペースファイルの読み書き・編集・一覧（詳細は[beta-files-classifiers.md](beta-files-classifiers.md)） |
| [Fusion](https://openrouter.ai/docs/guides/features/server-tools/fusion)                     | `openrouter:fusion`           | 複数モデル＋judgeモデルによる多角的分析                                                                                     |
| [Advisor](https://openrouter.ai/docs/guides/features/server-tools/advisor)                   | `openrouter:advisor`          | 生成途中でより強いモデルに助言を求める                                                                                      |
| [Subagent](https://openrouter.ai/docs/guides/features/server-tools/subagent)                 | `openrouter:subagent`         | 自己完結タスクを小型・高速なモデルに委譲                                                                                    |

## 使い方

`tools`配列に`{"type": "openrouter:web_search"}`のように追加するだけ（ユーザー定義の`function`ツールと同一リクエストで併用可）。使用状況はレスポンスの`usage.server_tool_use`で追跡できる。

```json
{
  "model": "openai/gpt-5.2",
  "messages": [...],
  "tools": [
    { "type": "openrouter:web_search", "parameters": { "max_results": 3 } },
    { "type": "openrouter:datetime" },
    { "type": "function", "function": { "name": "get_stock_price", "...": "..." } }
  ]
}
```

個別ツールの詳細（パラメータ・レスポンス形式）は上表のリンク先を`extract_doc_section.py`で取得すること。

## Python SDK（openrouterライブラリ）での使い方

> これらはSDK内部の型情報であり、openrouter.ai/docsの公開ページには載っていない。SDKバージョンにより変わりうるので、怪しい場合はドキュメントを鵜呑みにせずインストール済みパッケージの実体（`site-packages/openrouter/components/*.py`）を確認すること。

`from openrouter import OpenRouter`でクライアントを作り、`client.chat.send(model=..., messages=[...], stream=False, tools=[...])`（非同期なら`await client.chat.send_async(...)`）の`tools`引数にServer Toolsの辞書を渡す。

`chat.py`上の`tools`引数の型は`Optional[Union[Iterable[components.ChatFunctionTool], Iterable[components.ChatFunctionToolTypedDict]]]`。`ChatFunctionTool`という名前だが実体は`openrouter/components/chatfunctiontool.py`で定義された`Union`で、ユーザー定義の`function`ツールに加え、`OpenRouterWebSearchServerTool`（`openrouter/components/openrouterwebsearchservertool.py`、type: `openrouter:web_search`）や`WebFetchServerTool`（`openrouter/components/webfetchservertool.py`、type: `openrouter:web_fetch`）などOpenRouter組み込みのServer Toolsを含む。

そのためコンポーネントクラスをimportしなくても、プレーンな辞書を渡せば`ChatFunctionToolTypedDict`経由でSDKが検証・変換してくれる。

```python
res = client.chat.send(
    model=model_id,
    messages=[{"role": "user", "content": prompt}],
    stream=False,
    tools=[
        {"type": "openrouter:web_search"},
        {"type": "openrouter:web_fetch"},
    ],
)
```

両ツールとも`parameters`辞書で細かい設定を渡せる（`WebSearchServerToolTypedDict`/`OpenRouterWebSearchServerTool`の`parameters: WebSearchConfig`、`WebFetchServerToolConfig`など）。個々のフィールドは上表のリンク先を参照。Server Toolsはあくまで「使ってよい」と伝えるだけで、実際に呼ぶかどうかはモデルがリクエストごとに判断する。

このリポジトリでの実例は[tools/aim/aim_cli.py](../../../../../../tools/aim/aim_cli.py)。モジュールレベルで`WEB_TOOLS = [{"type": "openrouter:web_search"}, {"type": "openrouter:web_fetch"}]`を定義し、`--web`フラグ指定時に`tools=WEB_TOOLS if web else None`を`client.chat.send(...)`/`client.chat.send_async(...)`へ渡している。
