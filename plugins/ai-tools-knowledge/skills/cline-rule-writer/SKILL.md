---
name: cline-rule-writer
description: Cline 用のルールファイル (.clinerules/*.md) を設計・作成・更新するためのスキル。Cline公式ドキュメントの Rules / /newrule / Memory Bank の方針に沿って、簡潔で実用的なルールへ落とし込む。
user-invocable: true
disable-model-invocation: false
meta:
  tag: []
  requires_repo_tools: none
  requires_env: none
  dependencies: none
  requires_install: none
  requires_hooks: none
  requires_skills: none
  status: stable
  description: no description
  version: 1.0.0
---

# Cline Rule Writer

このスキルは、**Cline 用のルールファイル**を作るためのものです。対象は主にワークスペースルールで、出力先は原則として **`.clinerules/` 配下の Markdown ファイル**です。

このスキルを使うときは、以下の公式ドキュメント方針を必ず守ってください。

- Rules は Markdown ファイルで永続的な指示を与える仕組み
- ワークスペースルールは `.clinerules/` に置く
- 1ファイル1関心事を基本にする
- 必要に応じて YAML frontmatter の `paths` で conditional rules を使う
- 長すぎるルールは避け、具体的でスキャンしやすい形にする
- Memory Bank を導入する場合は、Rules にその運用指示を保存してよい

## このスキルのゴール

ユーザーの要望を、**Cline が継続的に読みやすく、毎回の会話で再利用しやすいルールファイル**に変換すること。

作る成果物は次のいずれかです。

1. 新規ルールファイルの作成
2. 既存ルールファイルの整理・分割・更新
3. conditional rule への変換
4. Memory Bank 用ルールの追加

## 最初に確認すること

ルールを書き始める前に、以下を確認してください。

1. **これは本当にルール化すべきか?**
   - 複数タスクで繰り返し出る指示か
   - 個人の一時的メモではなく、継続的に効く方針か
   - 単発の依頼ならルールではなく、その場の指示で十分ではないか

2. **どの粒度で分けるべきか?**
   - コーディング規約
   - テスト方針
   - ドキュメント更新方針
   - アーキテクチャ制約
   - Memory Bank 運用
   - 特定ディレクトリ専用の conditional rule

3. **どこに置くべきか?**
   - プロジェクト共有なら `.clinerules/`
   - 全プロジェクト共通の個人設定ならグローバルルール
   - このスキルでは、ユーザーから明示がない限り **`.clinerules/` のワークスペースルールを優先**する

## 実行フロー

### 1. 目的を明確化する

ユーザーの依頼から、ルールの目的を 1 文で言い換えてください。

例:

- 「TypeScript を強制し、テスト方針も明文化したい」
- 「`docs/` を編集するときだけ文書ルールを出したい」
- 「Memory Bank の運用を Cline に徹底させたい」

依頼が曖昧なら、書き始める前に不足情報を確認してください。特に次が曖昧なら質問が必要です。

- ルールの適用範囲（全体か、特定ディレクトリか）
- 既存パターンの参照先ファイル
- 禁止事項・制約の強さ
- Memory Bank を導入済みかどうか

### 2. 既存ルールを確認する

可能なら先に `.clinerules/` を確認し、以下を把握してください。

- 既存ルール名
- 重複しそうな内容
- 追記で済むか、新規ファイルに分けるべきか
- すでに conditional rule が使われているか

重複ルールを増やさないこと。似た内容があるなら、**新規作成より統合や整理を優先**してください。

### 3. ファイル配置を決める

原則:

- `.clinerules/coding.md` — 言語・命名・設計・実装規約
- `.clinerules/testing.md` — テスト方針
- `.clinerules/docs.md` — ドキュメント更新ルール
- `.clinerules/architecture.md` — 構造上の制約
- `.clinerules/memory-bank.md` — Memory Bank 専用ルール

必要なら数値 prefix を使ってもよいです。

- `01-coding.md`
- `02-testing.md`

ただし prefix は**整理目的でのみ使用**し、必須ではありません。

### 4. conditional rule にするか判断する

次のような場合は `paths` frontmatter を使ってください。

- フロントエンド専用ルール
- バックエンド専用ルール
- `docs/` 編集時だけの文体ルール
- `memory-bank/` に関係する作業だけで有効にしたいルール

使わないほうがよい場合:

- 常に有効であるべき全体ルール
- 対象パスがユーザー自身もまだ決めていない曖昧な段階

conditional rule を作るときは、先頭に以下のような YAML frontmatter を置いてください。

```yaml
---
paths:
  - "src/components/**"
  - "src/hooks/**"
---
```

パターンは必要最小限にしてください。広すぎる glob は避けてください。

### 5. ルール本文を書く

ルール本文は、**短く、具体的で、箇条書き中心**で書いてください。

推奨構成:

```markdown
# Rule Title

短い背景説明（必要なら）

## Scope

- 何に適用するか

## Instructions

- 守るべき具体的なルール
- 参考にする既存ファイル
- 禁止事項や例外

## When Unsure

- 判断に迷ったときの優先順位
```

ルール本文で守るべきこと:

- vague な表現を避ける
- 「なぜそうするか」を短く添えてよい
- 必要なら既存ファイルパスを具体的に書く
- 長い style guide 全文を貼らない
- 1 ファイルに複数の unrelated な関心事を詰め込まない

悪い例:

- 「いい感じに整理する」
- 「適切にテストを書く」
- 「保守しやすくする」

良い例:

- 「新規コードは TypeScript で作成する。新規 `.js` ファイルは追加しない」
- 「API のビジネスロジックには unit test を追加する」
- 「エラーハンドリングは `src/utils/errors.ts` の既存パターンを踏襲する」

### 6. Memory Bank ルールが必要なら公式パターンを優先する

ユーザーが Memory Bank を作りたい、またはセッションをまたいで文脈を維持したい場合は、**Memory Bank 専用のルールファイル**を作成してください。

出力先の原則:

- `.clinerules/memory-bank.md`

このときは、Cline 公式ドキュメントの方針に沿って以下を含めてください。

- Cline は毎タスク開始時に Memory Bank を読む
- `projectbrief.md`, `productContext.md`, `activeContext.md`, `systemPatterns.md`, `techContext.md`, `progress.md` を core files とする
- 重要な変更後や方向転換時に更新する
- `update memory bank` 要求時は全ファイルを見直す

Memory Bank ルールは通常の coding/testing ルールとは**別ファイル**に分けてください。

### 7. 出力時の必須条件

ルールファイルを作成・更新するときは、以下を満たしてください。

- 保存先の**正確なパス**を明示する
- 新規か更新かを明示する
- conditional rule の場合は `paths` の意図を説明する
- 既存ルールとの重複がないことを確認する
- ルールは Markdown としてそのまま保存できる形で出す

## 出力テンプレート

ユーザーに提示するときは、可能なら以下の形式を使ってください。

### A. 事前提案

- 目的
- 提案するファイルパス
- 新規作成 / 既存更新
- conditional の有無
- 含める主要セクション

### B. 実際のルール本文

```markdown
# ...
```

### C. 簡単な理由

- なぜ 1 ファイルにしたか
- なぜ conditional にしたか / しなかったか
- 参照すべき既存ファイルや今後の分割候補

## よくある作成パターン

### パターン1: 全体コーディング規約

- ファイル例: `.clinerules/coding.md`
- いつ使うか: 言語、命名、設計、禁止事項を毎回言っているとき
- conditional: 基本不要

### パターン2: docs 専用ルール

- ファイル例: `.clinerules/docs-style.md`
- conditional: 推奨
- 例:

```yaml
---
paths:
  - "docs/**"
  - "README.md"
  - "**/*.md"
---
```

ただし `**/*.md` は広すぎる場合があるため、リポジトリ構成に応じて狭めてください。

### パターン3: frontend / backend 分離

- `.clinerules/frontend.md`
- `.clinerules/backend.md`
- それぞれ `paths` で対象を分離する

### パターン4: Memory Bank 導入

- `.clinerules/memory-bank.md`
- 公式の Memory Bank custom instructions をベースにする
- 必要なら `memory-bank/**` に限定した conditional rule も検討する

## 禁止事項

このスキルでは次を避けてください。

- `.clinerules/` 以外に無造作にルールを散らす
- 1ファイルに unrelated な方針を大量に詰め込む
- 実装例や参照先があるのに抽象論だけで済ませる
- 毎回読み込むには長すぎる文章を貼る
- conditional rule が適切なのに always-on ルールにしてノイズを増やす
- always-on であるべき基礎ルールを過度に細分化して見失わせる

## ルール作成後のセルフレビュー

作成後は必ず次を確認してください。

1. **具体性** — 曖昧な文が残っていないか
2. **分離** — 1ファイル1関心事になっているか
3. **適用範囲** — conditional の path が広すぎないか/狭すぎないか
4. **参照性** — 既存ファイルやディレクトリ参照が正確か
5. **簡潔性** — 毎タスクで読ませても重すぎないか
6. **運用性** — ユーザーが将来 toggle / 更新しやすいか

## 最終的な振る舞い

このスキルが呼ばれたら、以下の優先順位で行動してください。

1. 依頼内容から「何をルール化するか」を要約する
2. 既存 `.clinerules/` の重複を確認する
3. 新規作成か既存更新かを決める
4. 必要なら conditional rule を選ぶ
5. Cline が読みやすい Markdown でルール本文を書く
6. 保存先パスと、なぜその構成にしたかを短く説明する

## 公式ドキュメント由来の重要ポイント（要約）

- Rules は persistent instructions である
- `.clinerules/` の `.md` / `.txt` はまとめて読み込まれる
- workspace rules は global rules より優先される
- `/newrule` は対話的に rule file を作る内蔵コマンド
- conditional rules は YAML frontmatter の `paths` で定義する
- Memory Bank は rule file に入れて運用できる
