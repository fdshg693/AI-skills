# Cline Skills Reference

> Source: Cline official docs extracted via `cline-docs`: <https://docs.cline.bot/customization/skills>

このファイルは、`cline-skill-writer/SKILL.md` 本体を短く保つための詳細リファレンス。Cline 用スキルの仕様確認、配置場所の判断、補助ファイル設計、description 改善が必要な時だけ読む。

## 目次

- [概要](#概要)
- [ロードモデル](#ロードモデル)
- [基本構造](#基本構造)
- [配置場所](#配置場所)
- [frontmatter](#frontmatter)
- [description の書き方](#description-の書き方)
- [補助ファイル](#補助ファイル)
- [Skill と Rule の切り分け](#skill-と-rule-の切り分け)
- [作成テンプレート](#作成テンプレート)
- [セルフレビュー](#セルフレビュー)
- [フォールバック](#フォールバック)

## 概要

Cline の Skill は、特定タスク向けのモジュール化された指示セット。Rules が常時有効なのに対し、Skills は関連する依頼の時だけロードされる。

向いている用途:

- 反復する作業手順
- ドメイン固有の調査・実装・レビュー手順
- 特定ツールやファイル形式に対するワークフロー
- テンプレートや検証スクリプトを伴う作業

向かない用途:

- すべてのタスクで常時守る規約（Rule 向き）
- 一回限りの依頼
- 単なる長文ナレッジベースの丸写し
- Cline にとって自明な一般論だけの文書

## ロードモデル

Cline 公式 docs では Skills は progressive loading と説明されている。

| レベル       | 読まれるタイミング       | 内容                                       |
| ------------ | ------------------------ | ------------------------------------------ |
| Metadata     | 起動時・常時             | YAML frontmatter の `name` / `description` |
| Instructions | Skill がトリガーされた時 | `SKILL.md` 本文                            |
| Resources    | 必要時                   | 同梱 docs / templates / scripts            |

設計上の含意:

- description は「起動判定」のための最重要フィールド。
- `SKILL.md` 本文は、起動後すぐ使う判断・手順に絞る。
- 詳細資料は別ファイルに分け、本文から読む条件を明示する。

## 基本構造

```text
my-skill/
├── SKILL.md          # 必須: metadata + main instructions
├── skills-reference.md  # 任意: 詳細仕様や長い説明
├── docs/             # 任意: 追加ドキュメント
├── templates/        # 任意: 雛形
└── scripts/          # 任意: 検証・変換などの決定的処理
```

最小の `SKILL.md`:

```markdown
---
name: my-skill
description: Do X for Y. Use when the user asks about A, B, or C.
---

# My Skill

Follow these task-specific instructions...
```

公式 docs 上の必須フィールド:

- `name`: ディレクトリ名と完全一致
- `description`: Cline がいつ使うべきかを判断する説明。最大 1024 文字

## 配置場所

公式 docs に記載されているプロジェクトスキルの配置場所:

- `.cline/skills/`（推奨）
- `.clinerules/skills/`
- `.claude/skills/`

グローバルスキル:

- macOS/Linux: `~/.cline/skills/`
- Windows: `C:/Users/USERNAME/.cline/skills/`

注意:

- 公式 docs では、同名の global skill と project skill がある場合は global skill が優先される。
- 既存スキルがあるリポジトリでは、まず周辺の慣例（置き場所・命名）に合わせる。
- チームで共有するプロジェクトスキルは、通常 `.cline/skills/` を version control するのが分かりやすい。

## frontmatter

Cline 公式 docs の基本は `name` と `description`。この環境の既存スキルでは `user-invocable` や `disable-model-invocation` も使われているが、Cline 公式仕様として利用可否が不明な項目は cline-docs で確認してから使う。

推奨:

```yaml
---
# 前提や依存スキルなど、本文に混ぜたくないメンテナ向けメモはコメントで書く
name: my-skill
description: Generate release notes from git history. Use when preparing releases, writing changelogs, or summarizing commits.
---
```

避ける:

```yaml
---
name: helper
description: Helps with various things.
---
```

## description の書き方

description は、Cline が Skill を起動するかどうかを決める検索インデックスのように扱う。

入れるべきもの:

- 先頭に「何をするか」
- 「Use when ...」で起動条件
- ユーザーが言いそうな語句
- 関連するファイル種別、ツール名、ドメイン名

良い例:

```yaml
description: Create and edit Cline skill files. Use when designing SKILL.md, writing skill descriptions, splitting supporting docs/scripts/templates, or deciding Skill vs Rule.
```

弱い例:

```yaml
description: Helps write skills.
```

落とし穴:

- 抽象語だけでは起動しない。
- 広すぎる説明は無関係な依頼で誤起動する。
- 手順要約を入れすぎると、本文を読ませたい意図が薄れる。
- 1024 文字制限に甘えず、短く具体的にする。

## 補助ファイル

公式 docs では追加ファイルとして docs / templates / scripts が例示されている。

### docs

長い説明、詳細リファレンス、トラブルシュート、プラットフォーム別手順を置く。

```text
my-skill/
├── SKILL.md
└── docs/
    ├── setup.md
    └── troubleshooting.md
```

本文には「いつ読むか」を書く。

```markdown
If authentication setup is requested, read [setup.md](docs/setup.md) before editing files.
```

### templates

設定ファイル、README、コード雛形など、Cline が埋める材料を置く。

```text
templates/config.yaml
templates/README.md
```

### scripts

検証、整形、データ取得、変換など、決定的で再現性が必要な処理を置く。

使うべき場合:

- 同じチェックを毎回正確に実行したい
- 長い計算・変換ロジックをトークンに載せたくない
- 出力だけを Cline に読ませれば十分

避けるべき場合:

- 状況判断そのものをスクリプトへ押し込む
- OS 差分を無理にシェルスクリプトで吸収する
- エラーハンドリングがない

## Skill と Rule の切り分け

| 判断軸             | Skill                                         | Rule                                   |
| ------------------ | --------------------------------------------- | -------------------------------------- |
| 読まれるタイミング | 関連タスク時だけ                              | 常時                                   |
| 向く内容           | 手順、専門ワークフロー、ツール操作            | コーディング規約、禁止事項、永続的方針 |
| コスト             | on-demand                                     | 常時コンテキスト消費                   |
| 例                 | release notes 生成、AWS deploy 手順、CSV 分析 | TypeScript 必須、テスト方針、設計制約  |

迷った時:

- 「この指示を毎回守らないと危険か？」→ Rule
- 「特定の依頼でだけ必要か？」→ Skill
- 「手順ではなくプロジェクト知識か？」→ Rule / Memory Bank / docs を検討

## 作成テンプレート

```markdown
---
name: example-skill
description: Do a specific workflow. Use when the user asks to handle concrete trigger phrases, file types, or domain tasks.
---

# Example Skill

One-sentence purpose. Avoid generic background.

## When to use

- Use for ...
- Do not use for ...

## Workflow

1. Confirm the goal and constraints.
2. Inspect existing files/patterns before editing.
3. Apply the task-specific procedure.
4. Validate using the project’s normal checks.

## References

- For detailed options, read [details.md](details.md) only when needed.
```

## セルフレビュー

作成・更新後に確認する。

- [ ] `name` とディレクトリ名が完全一致している
- [ ] description が具体的で、起動してほしい依頼文を含んでいる
- [ ] description が広すぎず、誤起動しにくい
- [ ] `SKILL.md` の先頭に最重要判断がある
- [ ] Cline に自明な説明を削っている
- [ ] 長い詳細は補助ファイルに分離している
- [ ] 補助ファイルへのリンクに「読む条件」がある
- [ ] scripts は決定的処理に限定され、失敗時の出力が分かる
- [ ] Rule にすべき永続指示を Skill に混ぜていない
- [ ] 公式仕様が曖昧な項目は cline-docs で確認済み

## フォールバック

1. このリファレンスで解決する。
2. Rule との切り分けなら `cline-rule-writer` を使う。
3. Cline 仕様の最新確認が必要なら `cline-docs` スキルを使う。
   - 参照 slug: `customization/skills`
   - 公式 URL: <https://docs.cline.bot/customization/skills>
