# OKF v0.2 要約

[output/SPEC.md](output/SPEC.md)（GoogleCloudPlatform/knowledge-catalog, `okf/SPEC.md`, v0.2）の要約。ほとんどの質問はこのファイルで足りる。条文の正確な文言・エッジケースが必要な場合のみ、SKILL.mdの手順（Grep/サブエージェント）で原文にあたる。

## 目次

- [1. 何のためのフォーマットか](#1-何のためのフォーマットか)
- [2. 用語](#2-用語)
- [3. バンドル構造](#3-バンドル構造)
- [4. 概念ドキュメント](#4-概念ドキュメント)
- [5. Provenance / Trust / Lifecycle](#5-provenance--trust--lifecycleすべて任意フィールド)
- [6. クロスリンクとパス](#6-クロスリンクとパス)
- [7. Actor記法](#7-actor記法)
- [8. index.md](#8-indexmd8)
- [9. log.md](#9-logmd9)
- [10. Attested Computation](#10-attested-computation10-要点のみ詳細な例はwritingmd)
- [11. Conformance（準拠条件）](#11-conformance準拠条件)
- [12. バージョニング](#12-バージョニング)
- [13. v0.1からの変更点](#13-v01からの変更点)
- [原文の節番号対応](#原文の節番号対応)

## 1. 何のためのフォーマットか

OKF (Open Knowledge Format) は、データ・システムを取り巻く「知識」（メタデータ・文脈・キュレーションされた洞察）を表現するための、人間にもエージェントにも読み書きしやすいフォーマット。実体は**YAML frontmatter付きMarkdownファイルのディレクトリ**。スキーマレジストリも中央機関も必須ツールもない。`cat`で読め、`git clone`で運べる。

**ゴール**: (1) 誰でも書き込める共通フォーマットの定義 (2) エージェント/UI/検索/決定論的コードが読み・辿る方法の提示 (3) 組織横断での知識交換 (4) エージェントが継続的にメンテする知識コーパスを「信頼できる」ものにする最小限のfrontmatterフィールドの標準化。

**非ゴール**: 概念タイプの固定タクソノミー化、ストレージ/配信/クエリ基盤の規定、既存ドメインスキーマ（Avro/Protobuf/OpenAPI等）の代替（OKFはそれらを参照するだけ）、executor/attesterのパッケージング・起動方式の規定（インターフェースだけ固定）。

v0.2で **provenance（出所）・trust（信頼度）・freshness（鮮度）・lifecycle（バージョン状態）・attestation（証明）** が一級市民になった。理由: 知識コーパスの多くがエージェントにより継続生成されるようになった今、「何から作られ、どう検証されたか」「どれだけ信じてよいか」「まだ正しいか」「最新版か」「宣言した通りの手順で算出されたか」に答える必要があるため。

## 2. 用語

- **Knowledge Bundle（バンドル）**: 知識ドキュメントの階層的コレクション。配布の単位。
- **Concept（概念）**: バンドル内の知識1単位＝1つのmarkdownドキュメント。有形資産（テーブル、API）から抽象概念（メトリクス、業務プロセス）まで。
- **Concept ID**: バンドル内でのファイルパスから`.md`を除いたもの。
- **Frontmatter**: ファイル先頭の`---`区切りYAMLメタデータブロック。
- **Body**: frontmatter以降の本文。
- **Link**: 概念間の標準markdownリンク。親子階層以外の関係を表す。
- **Source**: 概念が由来する材料（`sources`フィールドに記録）。
- **Provenance**: 概念が由来するsourcesの集合。
- **Credibility signal**: `author`/`usage_count`/`last_modified`など、信頼度を推論するための客観的な per-source 事実（OKFはスコアではなくシグナルを記録する）。
- **Actor**: 誰/何が行動したかを示す文字列。エージェントは`<producer>/<version>`、人は`human:<id>`、自動プロセスは`process:<id>`（§7）。
- **Trust tier**: `verified`フィールドから導出される段階: unverified / machine-confirmed / human-reviewed（§5.3）。
- **Attested Computation**: `type: Attested Computation`の概念。値の算出方法を宣言し、消費者が「その通りに算出されたか」を確認できるようにする（§10）。
- **Executor**: 計算を実行しreceiptを返す実行手段・コード。
- **Receipt**: 実行が返す証跡（`executor.receipt`が形を決める、バンドルには保存しないランタイム成果物）。
- **Attester**: receiptを検査して判定を返す決定論的（LLM不使用）コード。

## 3. バンドル構造

```
path/to/bundle/
  index.md                      # 任意。ディレクトリ一覧（progressive disclosure）
  log.md                        # 任意。更新履歴
  <concept>.md                  # ルート直下の概念
  <subdirectory>/                # サブディレクトリで概念をグループ化
    index.md
    <concept>.md
    <subdirectory>/...
```

配布形態: gitリポジトリ（推奨。履歴・帰属・diffが得られる）/ tarball・zip / より大きなリポジトリ内のサブディレクトリ。

**予約ファイル名**（概念ドキュメントとして使用不可）: `index.md`（§8）、`log.md`（§9）。それ以外の`.md`はすべて概念ドキュメント。タグは別ファイル形式を持たず、`tags`フロントマターで表現する（タグ一覧ビューは消費者側でその場合成する）。

## 4. 概念ドキュメント

UTF-8 markdownで、(1) YAML frontmatter（`---`〜`---`）と (2) 自由形式のmarkdown bodyの2部構成。

### 4.1 Frontmatter

```yaml
---
type: <Type name> # 必須。唯一の常時必須フィールド
title: <表示名> # 推奨
description: <一文要約> # 推奨
resource: <対象アセットの正規URI> # 推奨（抽象概念には無いこともある）
tags: [<tag>, ...] # 任意
# ... provenance/trust/lifecycle/computation系（§5, §10）
# ... producer独自のキー
---
```

- `type`は中央登録制ではない。producerは説明的な値を選ぶべき（例: `BigQuery Table`, `BigQuery Dataset`, `API Endpoint`, `Metric`, `Playbook`, `Reference`, `Attested Computation`）。consumerは未知のtypeを許容し、汎用概念として扱う。
- `type`だけの概念でも完全に準拠（§11）。
- **拡張**: producerは任意の追加キーを持てる。consumerは未知キーを保持し、拒否してはならない。

### 4.2 Body

構造化されたmarkdown（見出し・リスト・表・コードフェンス）を自由文より優先すべき。必須の本文セクションは無いが、以下の見出しは慣習的な意味を持つ:

| 見出し          | 用途                                    |
| --------------- | --------------------------------------- |
| `# Schema`      | アセットの列/フィールドの構造化記述     |
| `# Examples`    | 具体的な使用例（多くはコードフェンス）  |
| `# Computation` | Attested Computationの正式な計算（§10） |

外部ソースへのper-claim引用は、本文の引用リストではなく`sources`エントリに紐づくmarkdown脚注を使う（§5.1）。

## 5. Provenance / Trust / Lifecycle（すべて任意フィールド）

不在にも意味がある: 未検証の概念は検証済みと区別できるが、決して拒否されない（§11）。

### 5.1 Provenance: `sources`

```yaml
sources:
  - id: ga4-schema # 任意。本文の脚注ラベルと対応
    resource: https://.../export-schema # 必須。URL/バンドル相対パス、または"スコープ記述子"
    title: GA4 BigQuery Export schema # 任意
    author: team:ga4-docs # 任意（credibility signal）
    usage_count: 5000 # 任意（credibility signal）
    last_modified: 2026-05-30 # 任意（credibility signal）
usage_window: { from: 2026-06-01, to: 2026-06-30 } # usage_countの期間（エントリ単位で上書き可）
```

- credibility signal（`author`/`usage_count`/`last_modified`）はスコアではなく客観的事実。信頼度はこれらから*推論*する。
- `usage_count`は粗いシグナル（生存/order-of-magnitude/自身の履歴推移の比較には使えるが、種類の異なる利用同士の精密な順位付けには使わない）。
- per-claim引用は`sources[].id`をラベルにしたmarkdown脚注: `本文の主張[^ga4-schema]` / `[^ga4-schema]: GA4 BigQuery Export schema`。位置インデックス（`sources[0]`）ではなく安定したidを使う理由: エージェントが頻繁に書き換えるため、並び替えで誤帰属しないように。
- lineageは専用フィールドではなくリンクで表現する。`resource`が別のOKF概念を指す場合、そのderivationエッジはバンドルグラフ内に既にあるので、consumerはそのsourceの`sources`へ再帰してcredibilityを伝播させてよい。

### 5.2 Trust: `generated` / `verified`

```yaml
generated: { by: reference_agent/gemini-2.5-pro, at: 2026-06-20T22:53:05Z } # by必須
verified:
  - { by: human:ahormati, at: 2026-06-25T09:00:00Z }
  - { by: process:finance-nightly, at: 2026-06-26T02:00:00Z }
```

- `generated`＝誰が/いつ*書いた*か。`verified`＝誰が/いつ*確認した*かのリスト（複数可）。両者は独立: 内容は再確認なしに変わりうるし、再生成なしに再確認されうる。
- 単一verifierはリストのdashなしの`{ by, at }`一つのマッピングで書いてよく、consumerは1要素リストとして扱わなければならない。

### 5.3 Trust tiers（`verified`から導出、低→高）

- `verified`キーなし ⇒ **unverified**
- `human:`以外のactorのみ ⇒ **machine-confirmed**
- `human:<id>`によるverified ⇒ **human-reviewed**

trust frontmatterが無い概念も消費可能。consumerは拒否してはならない。trust tierはアクセス制御ではなく助言的シグナル。

### 5.4 Lifecycle: `status`

```yaml
status: stable # draft | stable | deprecated
```

`draft`=未レビュー・不完全な可能性、`stable`=既定・利用可能、`deprecated`=リンク・履歴のため保持・現行ではない。不在 ⇒ `stable`。

### 5.5 Lifecycle: `stale_after`

```yaml
stale_after: 2026-09-23 # YYYY-MM-DD 絶対日付
```

`today >= stale_after`でstale。相対TTLではなく絶対日付にすることで、「いつ読んだか」に依存しない単純な日付比較になる。

## 6. クロスリンクとパス

- **絶対（バンドル相対）**: `/`始まり、バンドルルートから解決。**推奨**（サブディレクトリ内で移動してもリンクが安定）。例: `[customers table](/tables/customers.md)`
- **相対**: 通常のmarkdown相対パス。例: `[neighboring concept](./other.md)`
- リンクは「関係がある」ことだけを主張する。関係の種類（親子/参照/join/依存）は周辺の散文で表現し、リンク自体には型が無い。consumerはリンク切れを許容しなければならない（未執筆の知識を意味しうるため）。
- パス値フィールド（`resource`, `sources[].resource`, `computation`, `executor.resource`, `attester.resource`）は絶対URL / `/`始まりバンドル相対パス / 相対パスのいずれかを受け付ける。
- `references/`サブディレクトリは、外部資料・実行手順・コードをバンドル内の第一級概念としてミラーする慣習（必須ではない）。

## 7. Actor記法

`generated.by` / `verified[].by`で使う: `<producer>/<version>`（エージェント/ツール）、`human:<id>`（人）、`process:<id>`（自動プロセス）。trust tier分類は`human:`prefixで判定するため、人が書いた/確認したコンテンツには必ずこのprefixを使う。

## 8. index.md（§8）

任意のディレクトリ（バンドルルート含む）に置ける。frontmatterは持たない（例外: バンドルルートの`index.md`だけ`okf_version`キーを持ってよい、§12）。中身は見出しでグループ化した箇条書きリンク:

```markdown
# Section / Group Heading

- [Title 1](relative-url-1) - short description
- [Title 2](relative-url-2) - short description
```

progressive disclosure（全体を開く前に何があるか把握する）のためのもの。producerが自動生成してもよく、consumerは無ければその場で合成してよい。

## 9. log.md（§9）

任意の階層に置ける更新履歴。日付見出し（ISO 8601 `YYYY-MM-DD`必須）でグループ化した新しい順のフラットリスト。先頭の太字語（`**Update**`/`**Creation**`/`**Deprecation**`）は慣習であり必須ではない。

## 10. Attested Computation（§10、要点のみ。詳細な例はWRITING_GENERAL.md）

「値が何を意味するか」（provenance）と「宣言した通りの手順で算出されたか」（attestation）は別問題。`type: Attested Computation`の独立した概念として持ち、使う側（Metric等）はリンクするだけ。

契約フィールド: `runtime`（必須、`parameters`の意味を決める。例: `bigquery`/`postgres`/`dbt`/`python`/`Looker`）、`parameters`（`{name, type, required}`のリスト）、`computation`（本文`# Computation`フェンスの代わりに外部ファイルを指す場合のパス）、`executor`（`resource`=実行手順/コード、`receipt`=実行が返すべきフィールド）、`attester`（`resource`=receiptを検査するLLM不使用の決定論的コード）。

エージェントは宣言済み`parameters`の値だけを埋めてよく、computation自体を書き換えてはならない。フロー: discover（`type`で発見）→ load（frontmatter+body）→ parameterize（値を埋める）→ execute（executorがreceiptを返す）→ attest（attesterが判定）→ gate（失敗したattestationは表示しない、stale_after超過は警告/拒否）。

`verified`（定義がポリシーと一致しているかのdoc-level・低頻度チェック）とattestation（1回の実行が正しい手順で値を算出したかのper-call・runtimeチェック）は別物で、両方が必要。

## 11. Conformance（準拠条件）

バンドルがOKF v0.2準拠なのは:

1. 予約名以外の全`.md`がパース可能なYAML frontmatterを持つ
2. 全frontmatterが空でない`type`を持つ
3. 予約ファイル名（`index.md`/`log.md`）が存在する場合、§8/§9の構造に従う

trust/lifecycle/provenance/computation系フィールドがある場合、producerは§5〜§10に従うべき（SHOULD）。consumerは: bareな`verified`マッピングを1要素リストとして扱わなければならない／任意ファミリーの不在を理由に概念を拒否してはならない／trust tierとstalenessはここで定義されたフィールドからのみ導出すべき／attestation失敗は隠さず表面化すべき。

**consumerが拒否してはならないもの**: 任意frontmatterフィールドの欠如、未知の`type`値、未知の追加frontmatterキー、リンク切れ、`index.md`の欠如。

## 12. バージョニング

現行は **v0.2**。`<major>.<minor>`。minorは後方互換な追加（新しい任意フィールド、新しい慣習見出し）、majorは破壊的変更（必須フィールドのリネーム、予約ファイル名の変更）になりうる。バンドルはルート`index.md`のfrontmatterで`okf_version: "0.2"`を宣言してよい（これがindex.mdでfrontmatterが許される唯一の場所）。consumerは未知バージョンでも拒否せずbest-effortで読むべき。

## 13. v0.1からの変更点

- **破壊的**: `timestamp` → `generated.at`（consumerは`generated`不在時に legacy `timestamp`へフォールバック可）。本文の`# Citations`リスト → `sources`（consumerはv0.1文書の`# Citations`をパースしてもよい）。
- **追加的**（不在ならv0.1相当になるだけ）: `sources`とcredibility signals、`usage_window`、`generated`/`verified`、`status`/`stale_after`（§5）。新しい概念タイプ`Attested Computation`とその計算系キー（§10）。新しい慣習見出し`# Computation`。Actor記法（§7）。

バンドル構造・予約ファイル名・必須`type`・推奨`title`/`description`/`resource`/`tags`・クロスリンク・index/logファイル・寛容なconformanceは変更なし。

## 原文の節番号対応

| 節         | 内容                                            |
| ---------- | ----------------------------------------------- |
| §1         | 動機・ゴール・非ゴール                          |
| §2         | 用語集                                          |
| §3         | バンドル構造・予約ファイル名                    |
| §4         | 概念ドキュメント（frontmatter/body）            |
| §5         | Provenance/Trust/Lifecycle                      |
| §6         | クロスリンク・パス                              |
| §7         | Actor記法                                       |
| §8         | index.md                                        |
| §9         | log.md                                          |
| §10        | Attested Computation                            |
| §11        | Conformance                                     |
| §12        | Versioning                                      |
| §13        | v0.1→v0.2差分                                   |
| Appendix A | income statementのv0.1→v0.2移行のフルワークト例 |
