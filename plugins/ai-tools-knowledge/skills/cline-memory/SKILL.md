---
name: cline-memory
description: Clineのメモリ・文脈維持機能を説明・設計・設定するスキル。AGENTS.md（プロジェクトルート/グローバル/ネスト）の扱い、Rules (.clinerules) / Skills / Memory Bank の使い分け、セッションをまたぐ文脈維持やコンテキストウィンドウ管理（/newtask, /smol, Auto Compact）について質問されたり設定を依頼されたときに使う。Use when the user asks how Cline remembers context, reads AGENTS.md, or wants to set up Memory Bank.
user-invocable: true
disable-model-invocation: false
meta:
  tag: []
  requires_repo_tools: none
  requires_env: none
  dependencies: none
  requires_install: none
  requires_hooks: none
  requires_skills: cline-docs
  status: stable
  description: no description
  version: 1.0.0
---

# Cline Memory

Cline がプロジェクト知識を「記憶」する仕組みを、依頼に応じて説明・設計・設定するためのスキル。

## 最重要: メモリ機能の全体像

| 機能        | 場所                                                               | 読まれるタイミング                 | 向いている内容                     |
| ----------- | ------------------------------------------------------------------ | ---------------------------------- | ---------------------------------- |
| AGENTS.md   | プロジェクトルート / `~/.agents/AGENTS.md`                         | 常時                               | クロスツール共通の永続指示         |
| Rules       | `.clinerules/`（プロジェクト）/ `~/.cline/rules/` 等（グローバル） | 常時（条件付きは対象パス編集時）   | コーディング規約・プロジェクト制約 |
| Skills      | `.cline/skills/` 等                                                | 関連依頼時だけ                     | 手順・専門ワークフロー             |
| Memory Bank | `memory-bank/`                                                     | タスク開始時（カスタム指示による） | セッション跨ぎのプロジェクト状態   |

「毎回守るべき規約」は AGENTS.md / Rules、「特定作業の手順」は Skill、「セッションをまたぐ作業状態」は Memory Bank に置く。この切り分けが最初の判断。

## AGENTS.md の扱い

- Cline 公式対応は **プロジェクトルートの `AGENTS.md`** と **グローバルの `~/.agents/AGENTS.md`** の2箇所。
- **ネスト AGENTS.md（サブディレクトリ配置）は公式ドキュメントに記載がない。** Claude Code のネスト CLAUDE.md の挙動を類推して説明しないこと。
  - ネスト対応を質問された場合は「公式には未文書であり、ルート配置が保証された動作」と答え、最新仕様の確認が必要なら後述のフォールバック手順を実行する。
  - サブディレクトリごとの条件付き指示が必要なら、ネスト AGENTS.md に頼らず **conditional rules（`paths` frontmatter）** で実現するのが公式に保証された方法。
- AGENTS.md と Rules の両方が存在する場合は結合して読まれ、**競合時はワークスペース側（プロジェクト内）が優先**される。

## 依頼別の対応

1. **「AGENTS.md を作って/読み方を教えて」** — 上記の配置ルールに従い、ルートに1ファイルで作成する。内容は Rules と同じく具体的でスキャンしやすい箇条書きにする。
2. **「セッションをまたいで文脈を維持したい」** — Memory Bank を提案する。手順は [memory-reference.md](memory-reference.md) の「Memory Bank」セクションを読んでから設計する。
3. **「コンテキストウィンドウが溢れる」** — `update memory bank` → 新規会話 → `follow your custom instructions` の手順、または `/newtask` / `/smol` / Auto Compact を案内する。
4. **「メモリ機能の仕様について質問」** — まず [memory-reference.md](memory-reference.md) を読み、解決しなければ下記フォールバックで最新公式ドキュメントを確認する。

## フォールバック

仕様が変わっていそうな場合・記載が見つからない場合は、`cline-docs` スキルを使い次のページを確認する。

- `customization/cline-rules` — AGENTS.md を含む Rules の対応表と優先順位
- `best-practices/memory-bank` — Memory Bank の構成とカスタム指示
- `getting-started/config` — グローバル/プロジェクトの設定配置

根拠にした公式ページの URL を回答に明示し、未確認の挙動は断定しない。

## 禁止事項

- Claude Code や他エージェントの仕様（ネスト CLAUDE.md、auto memory 等）を Cline の挙動として混同して説明しない。
- 公式未文書の挙動（ネスト AGENTS.md 等）を確認済みのように断定しない。
- 秘密情報・APIキーを AGENTS.md / Rules / Memory Bank ファイルに書き込まない。
