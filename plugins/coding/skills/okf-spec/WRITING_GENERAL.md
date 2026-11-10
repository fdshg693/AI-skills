# OKF概念の書き方（一般・producer向け）

新しいOKF概念ドキュメント（`.md`）を書く、または既存のものを更新するときの、バンドルを問わない一般的な実践ガイド。フィールドの意味は[SUMMARY.md](SUMMARY.md)を前提とし、ここでは「実際に何を書くか」に絞る。原文根拠は各節に§番号で示す。厳密なエッジケースはSKILL.mdの手順（Grep/サブエージェント）で`output/SPEC.md`原文にあたる。

このリポジトリ（`c--C-ai`）にOKFバンドルを作る場合の配置・frontmatterサンプルは[WRITING_REPO.md](WRITING_REPO.md)を参照（このリポジトリは現時点でOKF未対応の推奨案）。

## 目次

- [最小構成（これだけでも準拠）](#最小構成これだけでも準拠)
- [通常はここまで書く（推奨セット）](#通常はここまで書く推奨セット)
- [エージェントが生成する場合に必ず入れるフィールド](#エージェントが生成する場合に必ず入れるフィールド)
- [検証済みにする（`verified`）](#検証済みにするverified)
- [ライフサイクル](#ライフサイクル)
- [根拠を書く（`sources`と脚注）](#根拠を書くsourcesと脚注)
- [本文の構造](#本文の構造)
- [テンプレート例（リソースに紐づく概念）](#テンプレート例リソースに紐づく概念)
- [Attested Computationを書く場合](#attested-computationを書く場合)
- [index.md / log.mdを書く場合](#indexmd--logmdを書く場合)
- [よくある間違い](#よくある間違い)

## 最小構成（これだけでも準拠）

`type`だけがフロントマターの必須キー（§4.1, §11）。

```markdown
---
type: Reference
---

自由形式の本文。
```

これで完全に準拠したOKF概念になる。他のフィールドは全て任意で、後から追加できる。

## 通常はここまで書く（推奨セット）

```markdown
---
type: <種類。例: BigQuery Table / API Endpoint / Metric / Playbook / Reference>
title: <表示名>
description: <一文要約>
resource: <対象アセットの正規URI>        # 抽象概念には無くてよい
tags: [<tag1>, <tag2>]
generated: { by: <actor>, at: <ISO8601> }
---

# Schema | Examples など構造化された見出し

自由形式の本文。他概念へは `[表示名](/bundle/相対/path.md)` でリンクする。
```

- `type`は中央登録されていない自由文字列。既存の型に無理に合わせず、説明的な値を選ぶ（§4.1）
- `title`/`description`/`resource`/`tags`は**推奨**であり必須ではないが、`index.md`生成・検索スナップショット・プレビューで使われるので書く価値が高い
- ファイル名やディレクトリ構成に決まりは無い。ドメインに合わせて自由に設計する（§3）

## エージェントが生成する場合に必ず入れるフィールド

エージェントが概念を生成・更新したら、**必ず`generated`を書く**(§5.2)。

```yaml
generated: { by: reference_agent/gemini-2.5-pro, at: 2026-06-20T22:53:05Z }
```

- `by`は必須。actor記法は`<producer>/<version>`（エージェント）/ `human:<id>`（人）/ `process:<id>`（自動プロセス）の3種のみ（§7）
- `at`はISO 8601。「最後に内容が変わった時刻」であって、検証時刻ではない
- 人が確認した場合は別途`verified`を追加する（下記）。`generated`と`verified`は別物 — 誰が書いたかと誰が確認したかは独立に記録する

## 検証済みにする（`verified`）

人またはプロセスが内容を確認したら追加する（§5.2・§5.3）。

```yaml
verified: { by: human:ahormati, at: 2026-06-25T09:00:00Z }
# 複数の確認がある場合はリストにする
verified:
  - { by: human:ahormati, at: 2026-06-25T09:00:00Z }
  - { by: process:finance-nightly, at: 2026-06-26T02:00:00Z }
```

- `human:`prefixのactorが1つでも含まれれば trust tier は human-reviewed になる。それ以外のみなら machine-confirmed。`verified`自体が無ければ unverified（§5.3）
- **エージェントが自分自身の生成物に対して自分を`verified.by`として書いてはならない** — `verified`は「別の目で確認された」ことを示す記録であり、`generated`と同じactorを`verified`に書くと信頼度を偽ることになる

## ライフサイクル

```yaml
status: draft # draft | stable | deprecated（省略時はstable扱い、§5.4）
stale_after: 2026-09-23 # YYYY-MM-DD。today >= stale_after で stale（§5.5）
```

- 作成直後でレビュー前なら`status: draft`を明示する。省略すると`stable`（＝利用可能）とみなされるので注意
- 内容が時間とともに陳腐化しうる概念（数値、ダッシュボードの説明等）には`stale_after`を検討する。相対TTLではなく絶対日付で書く

## 根拠を書く（`sources`と脚注）

外部資料やバンドル内の別概念から情報を持ってきたら、`sources`に記録し、本文の主張を脚注で紐づける（§5.1）。

```yaml
sources:
  - id: ga4-schema
    resource: https://developers.google.com/analytics/bigquery/export-schema
    title: GA4 BigQuery Export schema
    author: team:ga4-docs
    last_modified: 2026-05-30
```

```markdown
`events_`テーブルは日次でシャーディングされる。[^ga4-schema]

[^ga4-schema]: GA4 BigQuery Export schema
```

- `resource`は各エントリで必須。具体的なURL/パス、または`all queries in BigQuery project X`のような「スコープ記述子」でもよい
- `id`は脚注ラベルと対応する安定キー。**位置（`sources[0]`）で参照しない** — 並び替えで誤帰属するため
- `author`/`usage_count`/`last_modified`はcredibility signal。持っている情報だけ書けばよく、スコアを自分で算出して書いてはいけない（OKFはスコアを保存しない設計）
- v0.1形式の本文末尾`# Citations`箇条書きは**書かない**。v0.2では`sources`に統合された（§13.1）。同様に旧`timestamp`キーも使わず`generated.at`を使う

## 本文の構造

自由形式のmarkdownだが、該当する場合は以下の慣習見出しを使う（§4.2）。

| 見出し          | 内容                                        |
| --------------- | ------------------------------------------- |
| `# Schema`      | 列/フィールドの構造化記述（表が読みやすい） |
| `# Examples`    | 具体的な使用例（コードフェンス推奨）        |
| `# Computation` | Attested Computationの正式な計算式（下記）  |

他概念へのリンクは**バンドルルートからの絶対パス**（`/`始まり）を優先する。ディレクトリ移動に強いため（§6.1）。

```markdown
[customers table](/tables/customers.md)
```

## テンプレート例（リソースに紐づく概念）

```markdown
---
type: BigQuery Table
title: Customer Orders
description: One row per completed customer order across all channels.
resource: https://console.cloud.google.com/bigquery?p=acme&d=sales&t=orders
tags: [sales, orders, revenue]
generated: { by: reference_agent/gemini-2.5-pro, at: 2026-05-28T14:30:00Z }
---

# Schema

| Column        | Type   | Description                                         |
| ------------- | ------ | --------------------------------------------------- |
| `order_id`    | STRING | Globally unique order identifier.                   |
| `customer_id` | STRING | Foreign key into [customers](/tables/customers.md). |

# Joins

Joined with [customers](/tables/customers.md) on `customer_id`.
```

（リソースに紐づかない抽象概念の例は`output/SPEC.md`§4.4を参照。`resource`を省略するだけで同じ形。）

## Attested Computationを書く場合

値の算出方法自体を保証したい（「その通りに計算されたか消費者が確認できる」ようにしたい）場合だけ、独立した`type: Attested Computation`概念を作る。単なる`Metric`の説明では不要（§10.1）。

```markdown
---
type: Attested Computation
title: Revenue for fiscal year
description: Recognized revenue for a fiscal year, per Finance's definition.
status: stable
runtime: bigquery
parameters:
  - { name: year, type: integer, required: true }
executor:
  resource: references/skills/run-on-bq.md
  receipt: [job_id, executed_sql, result]
attester:
  resource: references/attesters/revenue.py
generated: { by: reference_agent/gemini-2.5-pro, at: 2026-06-20T22:53:05Z }
verified: { by: human:ahormati, at: 2026-06-25T09:00:00Z }
stale_after: 2026-09-23
sources:
  - id: rev-policy
    resource: https://wiki.acme/finance/revenue-recognition
    title: Revenue recognition policy
---

# Computation

    SELECT SUM(amount) AS revenue
    FROM finance.recognized_revenue
    WHERE fiscal_year = @year

The computation binds only the declared `parameters`.[^rev-policy]

[^rev-policy]: Revenue recognition policy
```

守るべきルール（§10.2・§10.3）:

- `runtime`は必須。`parameters`の意味（SQLバインド変数か、dbt varか、Python引数か）を決める
- 計算本体は**本文の`# Computation`フェンス**か、`computation`フィールドで指す**外部ファイル**のどちらか一方。両方は書かない
- エージェントが埋めてよいのは宣言済み`parameters`の**値だけ**。computation自体（SQL/コード）を書き換えてはならない
- 値を使う側の概念（`Metric`など）はAttested Computationを本文中でリンクするだけで、自分のfrontmatterに計算詳細を持たない（§10.4）。1概念1計算1トラスト状態を保つ

## index.md / log.mdを書く場合

```markdown
# Section Heading

- [Title 1](relative-url-1) - short description of item 1

# Another Section

- [Subdirectory](subdir/) - short description
```

- `index.md`はfrontmatterを持たない（バンドルルートの`index.md`だけ`okf_version: "0.2"`を書いてよい、§12）
- エントリの説明文は、リンク先概念の`description`をそのまま転記するのがSHOULD（§8）

```markdown
# Directory Update Log

## 2026-05-22

- **Update**: Added a BigQuery table reference for [Customer Metrics](/tables/customer-metrics.md).
- **Creation**: Established the [Dataplex Playbook](/playbooks/dataplex.md).
```

- `log.md`の日付見出しは`YYYY-MM-DD`必須。先頭の太字語（`**Update**`/`**Creation**`/`**Deprecation**`）は慣習で必須ではない（§9）

## よくある間違い

- `verified`に自分自身（生成したのと同じactor）を書く → trust tierを偽ることになる。書かない
- v0.1の`timestamp`や本文`# Citations`を新規に書く → v0.2では非推奨。`generated.at`と`sources`を使う（§13.1）
- `sources[].id`を使わず位置で脚注を参照する（`[^1]`など連番） → 並び替えで誤帰属する。安定した`id`をラベルにする
- Attested Computationのcomputationフィールドとフェンスの両方を書く、またはエージェントが`# Computation`の中身を「改善」のつもりで書き換える → attestationが失敗する。値はparametersだけで渡す
- 未検証・下書きなのに`status`を省略する → 省略は`stable`扱いになる。draftなら明示する
