# モデルごとの料金・課金体系

出典: `docs/models-and-pricing.md`, `help/models-and-usage/available-models.md`, `help/models-and-usage/usage-limits.md`, `help/models-and-usage/token-rate.md`

**注意**: この価格情報は 2026-07-09 時点のスナップショット。変動が激しいため、スキル本体には転記せず、実装時・回答時は `cursor-docs` スキル経由で `docs/models-and-pricing.md` を都度再取得すること（他のフィールドと同じく24時間キャッシュの仕組みが使える）。

## 2つの使用量プール（個人プラン共通）

毎月の請求サイクルでリセットされる、独立した2つのプール:

1. **First-party models pool**: Auto / Composer 2.5 / Grok 4.5 専用。含まれる使用量が多め。
2. **API pool**: 個別モデルを選択したときに消費される、モデルの API 料金そのままのプール。個人プランは最低 $20/月分の API 使用量を含む（上位プランはより多い）。

両方ともエディタ設定と [usage dashboard](https://cursor.com/dashboard/usage) で確認可能。

## Auto の固定レート

モデル選択に関わらず固定（100万トークンあたり）:

| トークン種別        | 価格  |
| ------------------- | ----- |
| Input + Cache Write | $1.25 |
| Output              | $6.00 |
| Cache Read          | $0.25 |

## 個別モデルの API 料金（抜粋）

`docs/models-and-pricing.md` の "Model pricing" テーブルに全モデル（OpenAI/Anthropic/Google/Cursor/Z.ai/Moonshot 等、約30種）が載っている。100万トークンあたりの価格で、Cursor はプロバイダの API 料金に上乗せなしで課金する。抜粋（Anthropic / Cursor 製モデルのみ）:

| モデル          | Input | Cache write | Cache read | Output | 備考                                                                                                 |
| --------------- | ----- | ----------- | ---------- | ------ | ---------------------------------------------------------------------------------------------------- |
| Claude Sonnet 5 | $3    | $3.75       | $0.3       | $15    | 2026-08-31 まで $2/$10 のローンチ割引。リクエストベースプランでは Max Mode 必須                      |
| Claude Opus 4.8 | $5    | $6.25       | $0.5       | $25    | Fast mode (`claude-opus-4-8-fast`) は Max Mode 必須、Opus 4.7 fast の 1/3 の単価                     |
| Claude Fable 5  | $10   | $12.5       | $1         | $50    | Enterprise/Privacy Mode 利用時はデータ保持同意が必要。ガードレール抵触時は自動で Opus にルーティング |
| Composer 2.5    | $0.5  | -           | $0.2       | $2.5   | Cursor 自社モデル                                                                                    |
| Grok 4.5        | $2    | -           | $0.5       | $6     | Cursor と SpaceXAI の共同開発。EU 未対応                                                             |

他の GPT-5系・Gemini系・GLM・Kimi 等は原本テーブル参照。

## プラン

| プラン   | 価格    | API 使用量込み | First-party pool |
| -------- | ------- | -------------- | ---------------- |
| Pro      | $20/mo  | $20            | 潤沢             |
| Pro Plus | $60/mo  | $70            | 潤沢             |
| Ultra    | $200/mo | $400           | 潤沢             |

含まれる使用量を超えた場合:

- **On-demand usage を有効化**: 同じ API 単価での従量課金（品質・速度が落ちることはない）
- **プランをアップグレード**

Teams: Standard ($40/user/mo) と Premium ($120/user/mo、Standard の5倍の Agent 上限)。Enterprise は要問い合わせ。

## Cursor Token Rate（Teams のみ）

Teams プランで **Auto 以外** のエージェントリクエストに対し、100万トークンあたり **$0.25** の追加課金。included usage・on-demand usage・BYOK usage すべてに適用される。Auto は免除。回避するには Auto を使う。

## Max Mode

- モデルが対応する最大コンテキストウィンドウまで拡張。
- 現行の個人プランでは Max Mode もモデルの API レートでそのまま課金（トークンベース）。
- レガシーなリクエストベースプランでは Max Mode に 20% のサーチャージが付く。
- Teams プランの non-Auto リクエストには Cursor Token Rate が Max Mode 使用時にも上乗せされる。

## 使用量の確認・リセット

- 確認: `cursor.com/dashboard` の Usage セクション（リアルタイム）。
- リセット: 月次、サブスクライブ日時基準（繰越なし）。チームは全員同じタイミングでリセット。
