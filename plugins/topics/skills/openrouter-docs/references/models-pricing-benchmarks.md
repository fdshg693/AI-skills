# Models API（価格・ベンチマーク取得）

Source:

- `guides/overview/models`（`extract_doc_section.py`でローカルキャッシュから再取得可能）
- `https://openrouter.ai/docs/api/api-reference/models/list-all-models-and-their-properties`（OpenAPI自動生成ページ。`output/llms.txt`・`output/llms-full.txt`のクロール対象外のため、`extract_doc_section.py`では取得できない。再確認は**WebFetchで直接このURLを取得**すること）
- `GET https://openrouter.ai/api/v1/models/{author}/{slug}/endpoints`（2026-08-29時点でWebFetchによる実APIレスポンスを確認）

OpenRouterは「全モデルの価格・対応パラメータ・ベンチマークスコアを横断比較する」「特定モデルをプロバイダ別の価格・稼働率で比較する」ための複数のModels系エンドポイントを公開している。認証不要（`Authorization`ヘッダなしでも200が返る）だが、レート制限緩和のためAPIキー付与が推奨される。

## エンドポイント一覧

| 用途                                 | Method / Path                                  | 備考                                             |
| ------------------------------------ | ---------------------------------------------- | ------------------------------------------------ |
| 全モデル一覧（価格・ベンチマーク込） | `GET /api/v1/models`                           | フィルタ・ソート・ページネーション対応           |
| 単一モデル取得                       | `GET /api/v1/model/{author}/{slug}`            | `models`ではなく単数形`model`。alias/variant解決 |
| モデル件数取得                       | `GET /api/v1/models/count`                     | `output_modalities`等のフィルタと組み合わせ可    |
| プロバイダ別エンドポイント一覧       | `GET /api/v1/models/{author}/{slug}/endpoints` | 同一モデルを提供する各プロバイダの価格・稼働率   |

TypeScript SDKでは`openRouter.models.list()` / `.count()` / `.listForUser()`、`openRouter.endpoints.list({author, slug})` / `.listZdrEndpoints()`に対応（`agent-sdk/typescript/api-reference/models`, `.../endpoints`）。

## `GET /api/v1/models` クエリパラメータ

| パラメータ                                          | 型      | 説明                                                                |
| --------------------------------------------------- | ------- | ------------------------------------------------------------------- |
| `offset` / `limit`                                  | integer | ページネーション（`limit`上限1000）                                 |
| `q`                                                 | string  | モデル名検索                                                        |
| `category`                                          | string  | ユースケース別フィルタ（例: `programming`）                         |
| `arch`                                              | string  | アーキテクチャ絞り込み                                              |
| `model_authors`                                     | string  | 作成組織（カンマ区切り、例: `openai,anthropic`）                    |
| `providers`                                         | string  | ホスティングプロバイダ絞り込み                                      |
| `input_modalities` / `output_modalities`            | string  | 入出力モダリティ（`text,image`等、`output_modalities=all`で全件）   |
| `supported_parameters`                              | string  | 対応APIパラメータ（例: `tools`でtool calling対応モデルのみ）        |
| `context`                                           | integer | 最小コンテキスト長                                                  |
| `min_price` / `max_price`                           | number  | プロンプト価格の範囲（$/M tokens）                                  |
| `min_output_price` / `max_output_price`             | number  | 出力価格の範囲                                                      |
| `min_age_days` / `max_age_days`                     | integer | OpenRouter追加からの経過日数                                        |
| `min_intelligence_index` / `max_intelligence_index` | number  | Artificial Analysis「Intelligence Index」の範囲                     |
| `min_coding_index` / `max_coding_index`             | number  | 同「Coding Index」の範囲                                            |
| `min_agentic_index` / `max_agentic_index`           | number  | 同「Agentic Index」の範囲                                           |
| `min_tool_success_rate` / `max_tool_success_rate`   | number  | ツール呼び出し成功率（0〜1）の範囲                                  |
| `distillable`                                       | string  | 蒸留可否フィルタ                                                    |
| `zdr`                                               | string  | Zero Data Retentionエンドポイントのみに絞る                         |
| `region`                                            | string  | データ処理リージョン（例: `eu`）                                    |
| `sort`                                              | string  | ソート順（下表）                                                    |
| `use_rss` / `use_rss_chat_links`                    | string  | RSS形式で返す（`https://openrouter.ai/api/v1/models?use_rss=true`） |

`min_intelligence_index`以下のベンチマーク系フィルタ・`min_price`系の価格フィルタはOpenAPI生成ページ由来で`output/llms-full.txt`未収録のため、数値の単位や境界挙動（inclusive/exclusiveなど）を断定する前にWebFetchで該当URLを再取得して裏取りすること。

### `sort`の値（`guides/overview/models`で確認済み）

| 値                            | 説明                                                     |
| ----------------------------- | -------------------------------------------------------- |
| `pricing-low-to-high`         | 安い順（prompt/completion/request/web_searchの加重平均） |
| `pricing-high-to-low`         | 高い順                                                   |
| `context-high-to-low`         | コンテキスト長が大きい順                                 |
| `throughput-high-to-low`      | スループット（p50, tokens/sec）が高い順                  |
| `latency-low-to-high`         | 初回トークンまでのレイテンシ（p50）が短い順              |
| `most-popular` / `top-weekly` | 直近1週間の処理トークン数が多い順（同義）                |
| `newest`                      | OpenRouterへの追加が新しい順                             |

データが無いモデルはソート対象次元で末尾に回る。`sort`省略時は互換性のためデフォルト順を維持。

同じフィルタ（`output_modalities`等）は`/api/v1/models/count`でも使え、一覧結果と件数の整合性を保てる。

## 単一モデル取得: `GET /api/v1/model/{author}/{slug}`

```bash
curl "https://openrouter.ai/api/v1/model/openai/gpt-4o"
curl "https://openrouter.ai/api/v1/model/anthropic/claude-3-5-sonnet"   # aliasは正規slugへ自動解決
curl "https://openrouter.ai/api/v1/model/openai/gpt-4:free"             # :free等のvariant suffixにも対応
```

存在しない・alias先も無いモデルは`404`。レスポンスは`{"data": {...Modelオブジェクト...}}`で、一覧と同じModelオブジェクトを1件だけ返す。

## Modelオブジェクトのスキーマ（`data[]`の各要素）

| フィールド             | 型                      | 説明                                                                                            |
| ---------------------- | ----------------------- | ----------------------------------------------------------------------------------------------- |
| `id`                   | string                  | API呼び出しに使うID（例: `google/gemini-2.5-pro-preview`）                                      |
| `canonical_slug`       | string                  | 変わらない永続的slug                                                                            |
| `name`                 | string                  | 表示名                                                                                          |
| `created`              | number                  | OpenRouter追加日時（Unix timestamp）                                                            |
| `description`          | string                  | モデルの説明                                                                                    |
| `context_length`       | number                  | 最大コンテキスト長                                                                              |
| `architecture`         | Architecture            | 入出力モダリティ・tokenizer・instruct_type                                                      |
| `pricing`              | Pricing                 | 最安値の価格構造（詳細後述）                                                                    |
| `top_provider`         | TopProvider             | 代表プロバイダのcontext_length/max_completion_tokens/is_moderated                               |
| `per_request_limits`   | object \| null          | レート制限情報                                                                                  |
| `supported_parameters` | string[]                | 対応するOpenAI互換パラメータ一覧                                                                |
| `default_parameters`   | object \| null          | デフォルトパラメータ値                                                                          |
| `expiration_date`      | string \| null          | 非推奨化予定日（非推奨でなければnull）                                                          |
| `reasoning`            | object \| undefined     | `mandatory`/`default_enabled`/`default_effort`/`supported_efforts`等（reasoning対応モデルのみ） |
| `benchmarks`           | Benchmarks \| undefined | サードパーティベンチマーク（データが無いモデルはフィールド自体省略）                            |
| `links.details`        | string                  | 例: `/api/v1/models/{author}/{slug}/endpoints`（プロバイダ別エンドポイントAPIへのパス）         |

### Pricing（USD、token/request/unit単位。`"0"`は無料）

`prompt` / `completion` / `request`（リクエスト固定費） / `image` / `web_search` / `internal_reasoning` / `input_cache_read` / `input_cache_write`。

### Benchmarksオブジェクト（2系統が別々に格納される）

```jsonc
{
  "design_arena": [
    {
      "arena": "models",
      "category": "website",
      "elo": 1385.2,
      "win_rate": 62.5,
      "rank": 5,
    },
  ],
  "artificial_analysis": {
    "intelligence_index": 71.4,
    "coding_index": 63.2,
    "agentic_index": 55.8,
  },
}
```

- **Design Arena**（[designarena.org](https://designarena.org)）: `arena`（`models`/`builders`/`agents`）×`category`（`website`/`gamedev`等）の組ごとに、OpenRouter掲載モデル内での相対順位（ELO・win_rate・rank）。外部リーダーボード全体ではなくOpenRouter掲載モデル間での順位である点に注意。
- **Artificial Analysis**: `intelligence_index`/`coding_index`/`agentic_index`の3指標。`/api/v1/models`の`min_intelligence_index`等のフィルタ・ソートはこの値を参照する（推定。フィルタ名の対応関係は要WebFetch裏取り）。

ベンチマークデータが無いモデルは`benchmarks`フィールドごと省略される。ベンチマークを持つモデルだけ抽出する例:

```bash
curl -s "https://openrouter.ai/api/v1/models" | jq '.data[] | select(.benchmarks) | {id, benchmarks}'
```

## プロバイダ別価格・稼働率: `GET /api/v1/models/{author}/{slug}/endpoints`

同一モデルを複数プロバイダがホストしている場合、`/api/v1/models`の`pricing`は「最安値」1本に丸められる。プロバイダごとの実際の価格・コンテキスト長・量子化・稼働率を見るには専用エンドポイントを叩く。

```bash
curl "https://openrouter.ai/api/v1/models/openai/gpt-4o/endpoints"
```

レスポンスは`data.endpoints[]`に各プロバイダのエンドポイントが並ぶ配列で、実データで確認できたフィールドは以下（画像生成系モデルは`/api/v1/images/models/{author}/{slug}/endpoints`という別パスになる例が`guides`配下で確認できるため、モダリティによってパスが変わりうる点に注意）:

| フィールド                                              | 説明                                        |
| ------------------------------------------------------- | ------------------------------------------- |
| `name` / `model_id` / `model_name`                      | エンドポイント名・モデルID・モデル名        |
| `provider_name` / `tag`                                 | プロバイダ名・プロバイダタグ                |
| `context_length`                                        | このプロバイダでのコンテキスト長            |
| `max_prompt_tokens` / `max_completion_tokens`           | プロンプト/completion上限                   |
| `pricing`                                               | このプロバイダでのprompt/completion等の価格 |
| `quantization`                                          | 量子化方式                                  |
| `status`                                                | エンドポイントの稼働状態                    |
| `uptime_last_5m` / `uptime_last_30m` / `uptime_last_1d` | 直近稼働率                                  |
| `latency_last_30m` / `throughput_last_30m`              | 直近レイテンシ・スループット                |
| `supported_parameters` / `supports_tool_choice`         | 対応パラメータ・tool_choice対応可否         |
| `supports_implicit_caching` / `supports_voice_cloning`  | 機能フラグ                                  |

SDK版: `openRouter.endpoints.list({ author, slug })`。ZDR（Zero Data Retention）適用時に利用可能なエンドポイントだけを事前確認する`openRouter.endpoints.listZdrEndpoints()`もある。

## 実用例

```bash
# tool calling対応かつ安い順
curl "https://openrouter.ai/api/v1/models?supported_parameters=tools&sort=pricing-low-to-high"

# コーディング性能が高い順に絞り込み（min_coding_indexは要裏取り）
curl "https://openrouter.ai/api/v1/models?min_coding_index=70&sort=pricing-low-to-high"

# 特定モデルをプロバイダ別に価格・稼働率比較
curl "https://openrouter.ai/api/v1/models/deepseek/deepseek-v3/endpoints"
```
