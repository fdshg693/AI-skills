# Cursorスキル機構リファレンス

> 出典: https://cursor.com/docs/skills.md （2026-07-20取得。原文スナップショットは [references/skills.md](references/skills.md)）/ プラグイン関連は https://cursor.com/docs/plugins.md

## 目次

- [概要](#概要)
- [発見場所](#発見場所)
- [ディレクトリ構成](#ディレクトリ構成)
- [ネストしたスキルディレクトリ](#ネストしたスキルディレクトリ)
- [モノレポ（ネストしたプロジェクトディレクトリ）](#モノレポネストしたプロジェクトディレクトリ)
- [SKILL.md フォーマット](#skillmd-フォーマット)
- [ファイルへのスコーピング（paths）](#ファイルへのスコーピングpaths)
- [自動発動の無効化](#自動発動の無効化)

## 概要

Agent Skills は、AIエージェントをドメイン固有の能力で拡張するオープン標準（[agentskills.io](https://agentskills.io)）。スキルは「特定タスクの実行方法をエージェントに教える、ポータブルでバージョン管理可能なパッケージ」で、スクリプト・テンプレート・参照資料を含められる。

4つの特性:

- **Portable**: Agent Skills標準をサポートする任意のエージェントで動く
- **Version-controlled**: ファイルとして保持され、リポジトリで追跡したりGitHubリンクからインストールできる
- **Actionable**: エージェントがツールを使って実行できるスクリプト等を含められる
- **Progressive**: リソースを必要時にオンデマンドでロードし、コンテキスト使用を効率化する

## 発見場所

Cursor起動時に以下の場所からスキルが自動ロードされる:

| 場所                | スコープ               |
| ------------------- | ---------------------- |
| `.agents/skills/`   | プロジェクト           |
| `.cursor/skills/`   | プロジェクト           |
| `~/.agents/skills/` | ユーザー（グローバル） |
| `~/.cursor/skills/` | ユーザー（グローバル） |

互換目的で、Claude・Codexのディレクトリからもロードされる: `.claude/skills/`、`.codex/skills/`、`~/.claude/skills/`、`~/.codex/skills/`。

## ディレクトリ構成

各スキルは `SKILL.md` を含むフォルダ:

```text
.agents/
└── skills/
    └── my-skill/
        └── SKILL.md
```

任意ディレクトリ:

| ディレクトリ  | 用途                                               |
| ------------- | -------------------------------------------------- |
| `scripts/`    | エージェントが実行できるコード                     |
| `references/` | 必要時にオンデマンドで読まれる追加ドキュメント     |
| `assets/`     | テンプレート・画像・データファイル等の静的リソース |

`SKILL.md` は焦点を絞り、詳細な参照資料は別ファイルに分ける（オンデマンドロードでコンテキスト効率を保つため）。

## ネストしたスキルディレクトリ

スキルルート配下は再帰的に走査され、見つかった `SKILL.md` がすべて拾われる。カテゴリ・チーム・ドメイン単位のグループ化が可能:

```text
.cursor/
└── skills/
    ├── shipping/
    │   ├── land-it/
    │   │   └── SKILL.md
    │   └── careful-merge-conflicts/
    │       └── SKILL.md
    ├── debugging/
    │   └── using-datadog-mcp/
    │       └── SKILL.md
    └── workflow/
        └── tdd/
            └── SKILL.md
```

カテゴリフォルダは純粋に整理用。スキルの識別子は `SKILL.md` を含むフォルダ名（`land-it`、`tdd` 等）であり、親カテゴリは関係ない。

## モノレポ（ネストしたプロジェクトディレクトリ）

リポジトリ内のどこにある `.cursor/skills/`（または `.agents/skills/`）も拾われるため、モノレポではスキルをパッケージと同居させられる:

```text
my-monorepo/
├── .cursor/skills/         # リポジトリ全体のスキル
│   └── land-it/SKILL.md
└── apps/
    └── web/
        └── .cursor/skills/  # アプリ固有のスキル
            └── deploy-web/SKILL.md
```

ネストしたプロジェクトディレクトリ内のスキルは、そのディレクトリ配下のファイルに自動スコープされる（上例の `deploy-web` は `apps/web/` 配下の作業時のみ表面化され、リポジトリ全体の `.cursor/skills/` はどこでも使える）。`paths` フロントマターフィールドと同様の効果が、設定なしで得られる。

## SKILL.md フォーマット

YAMLフロントマター付きのMarkdown。フロントマターフィールド:

| フィールド                 | 必須 | 説明                                                                                                                         |
| -------------------------- | ---- | ---------------------------------------------------------------------------------------------------------------------------- |
| `name`                     | Yes  | スキル識別子。小文字英数字とハイフンのみ。親フォルダ名と一致必須                                                             |
| `description`              | Yes  | 何をするか・いつ使うか。エージェントが関連性の判断に使う                                                                     |
| `paths`                    | No   | スキルをマッチするファイルにスコープするglob。カンマ区切り文字列またはリスト。設定時はマッチするファイルを扱うときのみ表面化 |
| `disable-model-invocation` | No   | `true` の場合、`/skill-name` で明示呼び出しされたときのみコンテキストに含まれる。コンテキストに基づく自動適用はされない      |
| `metadata`                 | No   | 追加メタデータの任意キーバリューマッピング                                                                                   |

## ファイルへのスコーピング（paths）

`paths` でスキルをglobパターンにマッチするファイルに限定できる。マッチするファイルの読み書き時にのみエージェントへ表面化し、無関係な作業のコンテキストにファイル固有のガイダンスが入らないようにする。

リスト形式:

```markdown
---
name: react-component-patterns
description: Conventions for writing React components in this codebase.
paths:
  - "**/*.tsx"
  - "packages/ui/**/*.ts"
---
```

カンマ区切り文字列形式:

```markdown
---
name: python-style
description: Style rules for Python files.
paths: "**/*.py, scripts/**/*.py"
---
```

標準的なglob構文に従う。開いているファイルに関係なく常時使えるスキルにするには `paths` を未設定にする。レガシーの `globs` フィールドも旧スキルのフォールバックとして受け付けられるが、新規スキルは `paths` を使う。

## 自動発動の無効化

デフォルトでは、エージェントが関連すると判断したスキルが自動適用される。`disable-model-invocation: true` を設定すると従来のスラッシュコマンド相当になり、チャットで `/skill-name` を明示入力したときだけコンテキストに含まれる。
