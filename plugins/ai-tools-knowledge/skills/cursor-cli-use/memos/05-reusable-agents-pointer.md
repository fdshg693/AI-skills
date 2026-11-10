# 繰り返し指示を避けるための「Cursorエージェント作成方法」— 別スキル切り出しメモ

**方針**: このトピック（似たような指示の繰り返しを避けるための再利用可能な Cursor エージェント作成）は `cursor-cli-use` 本体には実装せず、**別スキルに切り出して `cursor-cli-use` から参照する**。理由は、対象範囲が CLI の「使い方」というより「カスタマイズ機構の設計」であり独立して育てる価値があるため。このメモはその別スキルを作る際の一次調査資料（種）として残す。

## 別スキル化する際の検討事項

- **候補名**: `cursor-subagents`, `cursor-cli-agents`, `cursor-custom-agents` あたり。Claude Code 側の `writing-subagents`（`skills/plugins/cc-knowledge/skills/writing-subagents`）と対になる命名にすると探しやすい。
- **スコープ**: Cursor で「繰り返し指示」を避ける仕組みは実は3つある（Subagents / Rules / Skills）。ユーザーの要望は「Cursorエージェント作成方法」だが、Subagents だけでなく Rules・Skills との使い分け（決定境界）まで扱わないと、読んだ人が誤った手段を選ぶ恐れがある。別スキルはこの3つの使い分け表を中心に構成するとよい。

## Subagents（`.cursor/agents/*.md`）— 本命

出典: `docs/subagents.md`

- **定義**: 親エージェントが委譲する専門特化サブエージェント。それぞれ独立したコンテキストウィンドウを持ち、結果だけを親に返す。
- **組み込み3種**（設定不要、自動使用）: `Explore`（コードベース探索、高速モデルで並列検索）、`Bash`（シェルコマンド実行、ノイズの多い出力を隔離）、`Browser`（MCP 経由のブラウザ操作）。
- **カスタムサブエージェントの配置場所**（プロジェクト優先度: `.cursor/` > `.claude/`/`.codex/`）:

  | 種別         | 場所                                                                                |
  | ------------ | ----------------------------------------------------------------------------------- |
  | プロジェクト | `.cursor/agents/`, `.claude/agents/`（Claude 互換）, `.codex/agents/`（Codex 互換） |
  | ユーザー     | `~/.cursor/agents/`, `~/.claude/agents/`, `~/.codex/agents/`                        |

- **ファイル形式**: YAML frontmatter 付き Markdown。

  ```markdown
  ---
  name: security-auditor
  description: Security specialist. Use when implementing auth, payments, or handling sensitive data.
  model: inherit
  readonly: true
  ---

  You are a security expert auditing code for vulnerabilities.
  ...
  ```

  | フィールド      | 必須 | デフォルト         | 説明                                                                                                                             |
  | --------------- | ---- | ------------------ | -------------------------------------------------------------------------------------------------------------------------------- |
  | `name`          | No   | ファイル名から導出 | 識別子。小文字とハイフンのみ                                                                                                     |
  | `description`   | No   | —                  | 親がいつ委譲するかを判断する材料。ここに時間をかける価値がある                                                                   |
  | `model`         | No   | `inherit`          | `inherit` か具体モデル ID（ブラケット構文で `effort`/`context` 等も指定可、[01-model-selection.md](01-model-selection.md) 参照） |
  | `readonly`      | No   | `false`            | true ならファイル編集・状態変更コマンド不可                                                                                      |
  | `is_background` | No   | `false`            | true ならバックグラウンド実行（親をブロックしない）                                                                              |

- **呼び出し方**: 自動委譲（description ベース。"use proactively" 等のフレーズで自動化を促せる）、明示呼び出し（`/name ...` またはプレーンテキストで「Use the verifier subagent to ...」）、並列実行（1メッセージ内で複数 Task 呼び出し）。
- **再開**: サブエージェント実行はエージェント ID を返し、後から `Resume agent <id> and ...` で文脈を保ったまま再開できる。バックグラウンドサブエージェントは `~/.cursor/subagents/` に進捗を書き出す。
- **ネスト制限**: サブエージェントが起動できるのは1階層まで（Cursor 2.5〜）。
- **ベストプラクティス**: 単機能に絞る、description に投資する、プロンプトは簡潔に、`.cursor/agents/` は git 管理する、まず Agent に叩き台を作らせてから調整する。
- **アンチパターン**: 曖昧な description の汎用エージェントを大量生産しない（最初は2〜3個の焦点を絞ったものから）、2000語級の長大プロンプトは避ける、単発タスクなら subagent でなく skill にする。
- **コスト**: サブエージェントはそれぞれ独立にトークンを消費する（5並列なら約5倍）。単純なタスクには不向き（起動オーバーヘッドの方が高くつく）。

## Rules（`.cursor/rules/*.mdc`, `AGENTS.md`）— 隣接する仕組み

出典: `docs/rules.md`

- LLM は補完間で記憶を保持しないため、プロンプトレベルで永続的な文脈を与える仕組み。**繰り返し同じ間違いを指摘するようになったら Rule 化のサイン**。
- 4種: Project Rules（`.cursor/rules/*.mdc`, git管理）、User Rules（グローバル、Customize > Rules）、Team Rules（ダッシュボード管理、Enterprise/Team）、`AGENTS.md`（frontmatter なしのシンプル版、ネスト可能）。
- `.mdc` の frontmatter 3種の組み合わせで適用条件が決まる: `alwaysApply: true`（常時）/ `globs` あり（ファイルパターン一致で自動添付）/ `description` あり（Agent が関連性判断）/ どちらもなし（`@rule-name` で手動のみ）。
- 作成: `/create-rule` スラッシュコマンド、または Customize サイドバー。
- ベストプラクティス: 500行以内、具体例を入れる、コードをコピーせず `@file` で参照、スタイルガイド丸ごとコピーは linter に任せる。

## Skills（`.agents/skills/`, `.cursor/skills/`, SKILL.md）— もう一つの隣接する仕組み

出典: `docs/skills.md`, `docs/subagents.md#when-to-use-subagents`

- Subagents と Skills の使い分け表（`docs/subagents.md` より）:

  | Subagent 向き                        | Skill 向き                                    |
  | ------------------------------------ | --------------------------------------------- |
  | 長時間の調査でコンテキスト分離が要る | 単発・単機能（changelog生成、フォーマット等） |
  | 複数ワークストリームを並列実行したい | 素早く繰り返せる一撃タスク                    |
  | 多段階にわたる専門知識が要る         | 1回で完結する                                 |
  | 完了作業の独立検証をしたい           | 別コンテキストウィンドウは不要                |

- Skills は `SKILL.md`（`name`, `description`, 任意で `paths`, `disable-model-invocation`, `metadata`）+ 任意の `scripts/`/`references/`/`assets/`。ネスト配置可（モノレポでアプリ配下に置くとそのディレクトリ配下でのみ有効化）。
- `disable-model-invocation: true` でスラッシュコマンド的な「明示呼び出し専用」にできる。
- Cursor には `/create-skill`, `/create-subagent`, `/create-rule`, `/migrate-to-skills`（既存の動的ルール・スラッシュコマンドを Skill に変換）という組み込みスキルがあり、いずれも Agent に「叩き台を作らせる」導線として使える。

## 別スキル執筆時のToDo

- [ ] 上記3機構（Subagents / Rules / Skills）の決定境界を1枚のフローチャートか判断表に落とす
- [ ] `.claude/agents/` `.codex/agents/` との互換共存時の優先順位（`.cursor/` > `.claude/`/`.codex/`）を明記
- [ ] モデル指定のブラケット構文（[01-model-selection.md](01-model-selection.md)）を subagent 作成の文脈で再掲
- [ ] 実際に `.cursor/agents/*.md` を作って `agent` で動作確認するステップを含める（本メモはドキュメントベースの調査のみで実機検証はしていない）
