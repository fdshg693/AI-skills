# Cline Memory Reference

> Source: Cline official docs — `customization/cline-rules`, `best-practices/memory-bank`, `getting-started/config` (docs.cline.bot)

Cline のメモリ・文脈維持機能の詳細リファレンス。`SKILL.md` の判断だけでは足りない場合に読む。仕様が古い疑いがある場合は、本文末尾の「最新確認」の手順で公式ドキュメントを再確認すること。

## 目次

- [メモリ機能の詳細比較](#メモリ機能の詳細比較)
- [AGENTS.md](#agentsmd)
- [Rules](#rules)
- [Memory Bank](#memory-bank)
- [コンテキストウィンドウ管理](#コンテキストウィンドウ管理)
- [設定ファイルの配置](#設定ファイルの配置)
- [最新確認](#最新確認)

## メモリ機能の詳細比較

| 判断軸     | AGENTS.md                      | Rules                                            | Skills              | Memory Bank                |
| ---------- | ------------------------------ | ------------------------------------------------ | ------------------- | -------------------------- |
| 場所       | ルート / `~/.agents/AGENTS.md` | `.clinerules/` / グローバル Rules                | `.cline/skills/` 等 | `memory-bank/`             |
| 読まれ方   | 常時                           | 常時（条件付きは対象パス時）                     | 関連依頼時          | タスク開始時（指示による） |
| ツール横断 | ○（agents.md 標準）            | ×（Cline 固有。`.cursorrules` 等の自動検知あり） | ×                   | ×（手法は汎用）            |
| 向く内容   | 永続指示                       | 規約・制約                                       | 手順                | セッション跨ぎの作業状態   |

## AGENTS.md

公式ドキュメント（`customization/cline-rules`）の対応表:

| Rule Type      | Location                           | Description                                  |
| -------------- | ---------------------------------- | -------------------------------------------- |
| Cline Rules    | `.clinerules/`                     | Primary rule format                          |
| Cursor Rules   | `.cursorrules`                     | Automatically detected                       |
| Windsurf Rules | `.windsurfrules`                   | Automatically detected                       |
| AGENTS.md      | `AGENTS.md`, `~/.agents/AGENTS.md` | Standard format for cross-tool compatibility |

- 検出された全ルールタイプは Rules パネルで個別に toggle できる。
- `~/.agents/AGENTS.md` は全プロジェクト共通のクロスツール用グローバル指示として読まれる。
- ワークスペースとグローバルのルールが競合する場合は **ワークスペース側が優先**される。

### ネスト AGENTS.md について

- 公式ドキュメントはルート配置とグローバル配置のみを文書化しており、**サブディレクトリ配置（ネスト）の自動検出・読み込みは公式には文書化されていない**（2026-08 時点の確認）。
- Claude Code のネスト `CLAUDE.md` と同じ挙動だと仮定して説明・設定しない。
- サブディレクトリ固有の指示は conditional rules で代用する（次セクション）。
- ネスト対応の最新状況は「最新確認」の手順で確認する。

## Rules

- 配置: プロジェクトは `.clinerules/`、グローバルは `~/.cline/rules/` と `~/Documents/Cline/Rules/`（Windows は `Documents\Cline\Rules`）。
- `.clinerules/` 内の `.md` / `.txt` はすべて結合して読まれる。数値 prefix（`01-coding.md`）は整理目的で任意。
- 条件付きルール: ファイル先頭に YAML frontmatter で対象パスを限定する。

```yaml
---
paths:
  - "src/api/**"
---
```

- frontmatter なしのファイルは常時有効。常時有効ルールと条件付きルールは別ファイルに分ける。
- toggle UI で個別に無効化できる（条件付きルールは toggle + paths の二段階制御）。

## Memory Bank

`memory-bank/` 配下に置く構造化ドキュメント。Cline をステートレスからセッション跨ぎの開発パートナーに変える手法。導入は公式のカスタム指示を Rules ファイル（例: `.clinerules/memory-bank.md`）に入れ、`initialize memory bank` を依頼する。

### コアファイル

| ファイル            | 役割                                                   |
| ------------------- | ------------------------------------------------------ |
| `projectbrief.md`   | 要件と目標の土台。他ファイルの起点                     |
| `productContext.md` | なぜ存在するか・解決する問題・UX 目標                  |
| `activeContext.md`  | 現在のフォーカス・最近の変更・次のステップ（最頻更新） |
| `systemPatterns.md` | アーキテクチャ・設計パターン・コンポーネント関係       |
| `techContext.md`    | 技術スタック・セットアップ・制約・依存                 |
| `progress.md`       | 動作しているもの・残作業・既知の問題                   |

複雑な機能ドキュメントや API 仕様などは `memory-bank/` 内に追加ファイル/フォルダを作ってよい。

### キーコマンド

| コマンド                          | 動作                                 |
| --------------------------------- | ------------------------------------ |
| `initialize memory bank`          | 新規プロジェクト用の初期構造を作成   |
| `update memory bank`              | 全ファイルの見直しと更新             |
| `follow your custom instructions` | Memory Bank を読んで中断箇所から再開 |

更新タイミング: 新パターン発見時 / 重要な変更実装後 / `update memory bank` 要求時（全ファイル必須）/ 文脈の明確化が必要なとき。

### FAQ 要点

- カスタム指示か Rules か: どちらも可。プロジェクト固有なら Rules に入れてリポジトリ共有するのが推奨。
- 更新頻度: 重要なマイルストーン・方向転換後。活発な開発では数セッションごと。ルーチンのコンテキスト管理は Auto Compact に任せ、重要なチェックポイントで手動 `update memory bank`。
- 他の AI ツールとも併用可能な「ドキュメント手法」。

## コンテキストウィンドウ管理

コンテキストが満杯に近づいたときの公式手順（手動アプローチ）:

1. `update memory bank` で現状を文書化
2. 新しい会話を開始
3. `follow your custom instructions` で再開

補助として、組み込みスラッシュコマンド `/newtask`（タスク分割でコンテキストを新しくする）と `/smol` を使える。Memory Bank 導入時は Auto Compact による自動圧縮と併用する構成が推奨されている。

## 設定ファイルの配置

| スコープ           | 場所                                                               | 対象                                 |
| ------------------ | ------------------------------------------------------------------ | ------------------------------------ |
| グローバル         | `~/.cline/`（rules, skills, hooks, agents, plugins, workflows 等） | すべての Cline アプリ（IDE/CLI/SDK） |
| グローバル（互換） | `~/Documents/Cline/Rules                                           | Hooks                                | Plugins | Workflows/` | 追加検索パス |
| プロジェクト       | `.cline/`（rules, skills, hooks, agents, plugins, cron 等）        | 現在のワークスペース                 |

- チーム共有するものはリポジトリ内（`.cline/` や `.clinerules/`）に置いて version control する。
- `~/.agents/AGENTS.md` は上記 `.cline/` とは別のクロスツール用グローバル位置。

## 最新確認

仕様が変わっていそうな場合・このリファレンスにない挙動を説明する場合は、`cline-docs` スキルで次を確認する。

- `customization/cline-rules` — ルールタイプ対応表・優先順位・条件付きルール
- `best-practices/memory-bank` — Memory Bank の構成・カスタム指示全文・FAQ
- `getting-started/config` — グローバル/プロジェクトの設定ディレクトリ構成
- `getting-started/`(該当ページ) や索引 (`llms.txt`) — AGENTS.md ネスト対応など新機能の追加状況

回答には根拠ページの URL を明示し、確認できない仕様は断定しない。
