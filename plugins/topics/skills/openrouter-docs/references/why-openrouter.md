# OpenRouterを経由してモデルを使う意味

Source: `guides/overview/principles`, `quickstart`, `guides/overview/auth/byok`

OpenRouterは「複数プロバイダのモデルを単一の統一APIでルーティングする層」であり、OpenAI/Anthropic等のプロバイダAPIを直接叩くのとは以下が異なる。

- **統一API**: `POST /api/v1/chat/completions`（OpenAI Chat Completions互換。`/api/v1/messages`でAnthropic Messages互換も可）1本で400以上のモデル・数十プロバイダを呼び分けられる。モデル/プロバイダを切り替えてもコード変更不要（OpenAI SDKをbaseURLだけ変えてそのまま使うことも可能）
- **自動フェイルオーバー/最適ルーティング**: プロバイダ障害時に自動でフォールバック。価格・レイテンシ・スループットのどれを優先するか選べる（[Provider Routing](https://openrouter.ai/docs/guides/routing/provider-selection)）
- **統合請求 & 高いレート上限**: 何プロバイダ使っても請求は1本化。OpenRouterがプロバイダと直接交渉した上限を利用できるため、単体契約より高いレート上限になることが多い
- **BYOK (Bring Your Own Key)**: OpenRouterクレジットの代わりに自分のプロバイダAPIキーを登録して直接課金・レート制御することも可能（[BYOK](https://openrouter.ai/docs/guides/overview/auth/byok)）。BYOK時もOpenRouter側の付加機能（ルーティング、observability等）はそのまま使える
- **OpenRouter独自の付加機能**: [server-tools.md](server-tools.md) / [observability.md](observability.md) / [beta-files-classifiers.md](beta-files-classifiers.md) に加え、Guardrails、Presets、Workspaces、モデルバリアント（`:nitro`/`:online`/`:thinking`/`:free`/`:extended`/`:exacto`）、各種Router（Auto Router/Fusion Router/Pareto Router等）、Response Caching、Router Metadata、Zero Completion Insuranceなど。これらはプロバイダAPIを直接叩くだけでは得られない
- **トレードオフ**: プロキシ層を挟む分の追加ホップ、（BYOKでない場合の）手数料、OpenRouterの可用性への依存、リクエストがOpenRouterを経由すること（Zero Data Retentionや各observability機能のPrivacy Modeで軽減可能）が挙げられる

料率・レート上限の具体値は変わりやすいので、断定的に答える前に上記Sourceパスを`extract_doc_section.py`で再取得して裏取りすること。
