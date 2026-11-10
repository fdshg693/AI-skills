---
# 同梱のsubagent.mdは参照用のリファレンス、このファイル自体はサブエージェントを実際に書く際のベストプラクティス集
name: writing-subagents
description: Use when creating or editing Claude Code subagents (.claude/agents/*.md, ~/.claude/agents/*.md, or the --agents CLI flag) — choosing scope and frontmatter fields, restricting tools, writing effective descriptions, model/permission settings, and avoiding common pitfalls.
meta:
  tag: []
  requires_repo_tools: none
  requires_env: none
  dependencies: none
  requires_install: none
  requires_hooks: none
  requires_skills: claude-code-docs
  status: stable
  description: no description
  version: 1.0.3
---

# サブエージェント作成のベストプラクティス

サブエージェントは強力だが、範囲を絞らない・descriptionが曖昧・ツールを渡しすぎる、といった事故が起きやすい。
ここでは**実際に書く際の手順とチェックリスト**をまとめる。フロントマター全フィールド・スコープ別の優先順位・呼び出し方・フォーク・入れ子起動などの詳細は同梱の [subagent.md](subagent.md) を参照。

## 作成手順

1. **既存で代用できないか確認する** — `.claude/agents/`（プロジェクト）・`~/.claude/agents/`（個人）に似た役割のサブエージェントが無いか探す。一度きりの作業やこの会話限りの指示ならサブエージェントではなく通常のタスク実行で十分。
2. **スコープを決める** — チームで共有したいなら`.claude/agents/`（バージョン管理にコミット）、自分の全プロジェクトで使うなら`~/.claude/agents/`。セッション限定・スクリプトからの動的生成なら`--agents` CLIフラグ。優先順位や配置場所の詳細は subagent.md の一覧表を参照。
3. **役割を1つに絞る** — 「コードレビューもデバッグも両方やる」のような多目的サブエージェントは避け、1つの専門に特化させる。
4. **`name`を決める** — 小文字英数字とハイフンのみ。ファイル名と一致している必要はないが、揃えておくと迷わない。
5. **`description`を具体的に書く** — Claudeはこの`description`だけを見て自動委譲するかを判断する。「いつ使うべきか」を具体的なトリガー・状況で書く。積極的に使ってほしいなら"use proactively"のような文言を含める。
6. **ツールを絞る** — デフォルトは全ツール継承。読み取り専用にしたいなら`tools: Read, Grep, Glob, Bash`のように許可リストで絞るか、除外したいものだけ`disallowedTools`で拒否する。両方指定時は`disallowedTools`が先に適用される点に注意。
7. **モデルを選ぶ**（必要な場合のみ） — コストを下げたい単純作業は`model: haiku`、複雑な判断が要る作業は`model: sonnet`/`opus`。省略時は`inherit`（メイン会話と同じモデル）。
8. **必要に応じて追加フィールドを設定する** — 権限を締めたい(`permissionMode`)、知識を事前ロードしたい(`skills`)、専用MCPを繋ぎたい(`mcpServers`)、学習を蓄積させたい(`memory`)、ターン数を制限したい(`maxTurns`)等。全フィールドは subagent.md 参照。
9. **本文（システムプロンプト）を書く** — 「呼ばれたら何をするか」の手順、チェックすべき観点、出力フォーマットを具体的に書く。サブエージェントはメイン会話の文脈・CLAUDE.mdの指示を知らない前提（`Explore`/`Plan`以外はCLAUDE.mdをロードするが、明示的に伝えたいルールがあれば委譲時のプロンプトにも書くよう促す）。
10. **保存して試す** — 自然言語で名指しして委譲されるか、`@`メンションで確実に呼び出せるかを確認する。新規に作った`agents`ディレクトリがそのスコープで初めての場合はセッション再起動が必要な点に注意。

## チェックリスト（ベストプラクティス）

- [ ] `name`は英数字・ハイフンのみ、同一スコープ内で他と重複していない
- [ ] `description`はいつ使うべきかが具体的（トリガー・症状・キーワードを含む）で、三人称
- [ ] 1つのサブエージェントは1つの役割に特化している（多目的化していない）
- [ ] 必要最小限のツールだけを許可している（読み取り専用でよい作業に`Write`/`Edit`を渡していないか）
- [ ] `bypassPermissions`を使う場合、何が起きるか（`.git`等の保護ディレクトリへの無確認書き込みを含む）を理解した上で選んでいる
- [ ] チームで共有すべきものは`.claude/agents/`に置きバージョン管理にコミットしている。個人用は`~/.claude/agents/`
- [ ] MCPサーバーをこのサブエージェント専用にしたい場合は`mcpServers`をフロントマターに書く（`.mcp.json`に書くとメイン会話のコンテキストも消費する）
- [ ] 継続作業させたい可能性があるなら、`Explore`/`Plan`ではなく`general-purpose`かカスタムサブエージェントを使っている（`Explore`/`Plan`はone-shotでresume不可）
- [ ] システムプロンプトにメイン会話の暗黙の前提を書き込みすぎていない（サブエージェントは基本的に真っ新なコンテキストで始まる。フォークだけが例外）
- [ ] 本文は簡潔に保ち、詳細なリファレンス（フロントマター全項目・スコープ別優先順位など）は同梱の subagent.md に任せている

## 困ったときは

1. まず同梱の [subagent.md](subagent.md)（詳細リファレンス: フロントマター全フィールド、スコープ別優先順位、明示的な呼び出し方、フォーク、入れ子起動、resume、無効化方法など）を確認する。
2. それでも解決しない・挙動が期待と違う場合:
   - `/doctor`で同一スコープ内の重複エージェント名などの設定エラーを確認する
   - 新規作成した`agents`ディレクトリがそのスコープで最初のものなら、セッションを再起動してから再度試す
3. デバッグしても原因不明、または subagent.md 執筆時点から仕様が変わっている可能性がある場合は、**claude-code-docsスキル**で最新の公式ドキュメント（`code.claude.com`）を参照する。
