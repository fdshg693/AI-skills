---
# 機構選択の意思決定フレームワーク。
# 各機構（CLAUDE.md/rules/auto memory・SKILLS・subagent・hooks）自体の書き方は専用スキルに委譲し、
# このスキルは「今から実現したいことにどれを使うべきか」の判断だけに特化する。
name: claude-mechanisms
description: Use when deciding which Claude Code mechanism to reach for — CLAUDE.md/rules/auto memory, a SKILL, a subagent, or a hook — before persisting knowledge, automating a workflow, or delegating a task. Also covers the anti-pattern of hoarding static prompt files instead of using SKILLS. For how to actually write each mechanism, defer to the dedicated skill it points to.
meta:
  tag: []
  requires_repo_tools: none
  requires_env: none
  dependencies: none
  requires_install: none
  requires_hooks: none
  requires_skills: none
  status: experimental
  description: no description
  version: 1.0.0
---

# Claude Codeの機構選択ベストプラクティス

Claude Codeには知識・処理を持たせる方法が複数ある（CLAUDE.md／`.claude/rules/`／auto memory／SKILLS／subagent／hooks）。
**どれを使うべきか**を最初に間違えると後で書き直しになるため、実装に入る前にこのスキルで選択を確定させる。
各機構の実際の書き方（frontmatter仕様・チェックリスト等）は本文中でリンクする専用スキルを使うこと。

## 判断フロー

以下の問いに上から順に答え、最初にYESになった機構を使う。

1. **「毎回」「必ず」実行・ブロックしたい処理か？**（コミット前チェック、特定ツール呼び出しの拒否など）
   → **hooks**。メモリ系もSKILLSも強制力のないコンテキスト注入に過ぎず、Claudeが従わない可能性がある点に注意。**writing-hooksスキル**へ。
2. **静的な知識・ルール・方針をClaudeに伝えたいだけか？**（コーディング規約、アーキテクチャ、ワークフロー、個人の好み）
   → **メモリ系**（CLAUDE.md / `.claude/rules/*.md` / auto memory）。3機構のうちどれかは**claude-code-memoryスキル**の判断手順に従う。
3. **動的な処理が要る、または特定タスク実行時だけ必要な手順か？**（コマンド実行結果の注入、スクリプトによる強力な処理、正解が一意でない複数正解ありうる手順）
   → **SKILLS**。**writing-skillスキル**（または重要・破壊的操作を伴うなら**writing-skill-complexスキル**）へ。
4. **専用のツール・モデル・コンテキストで切り離して作業させたい、または並列に処理させたいか？**
   → **subagent**。**writing-subagentsスキル**へ。

どれにも当てはまらない（単発の作業指示・その場限りの調査）なら、機構を作らず通常のタスク実行で済ませる。

## 境界ケースの判断基準

- **CLAUDE.md vs `.claude/rules/`**: ほぼ毎回必要な内容はCLAUDE.md、特定ディレクトリ・言語限定ならrules。詳細はclaude-code-memoryスキル参照。
- **SKILLS vs subagent**: 「何をやるか」の手順・知識が主眼ならSKILLS、「誰が（どんな権限・コンテキストで）やるか」の分離が主眼ならsubagent。両者は組み合わせられる（特定subagentに特定SKILLSの知識を事前ロードする等）。
- **subagentは積極的に使ってよい**: 並列subagentは応答時間の実質的なデメリットがほぼない。精度・コンテキスト分離が重要な場面では、使わない理由がない限り使う方針でよい。

## アンチパターン

- **プロンプトファイルをあれこれ手元に保存して、そのままcat等で渡す運用は避ける** — SKILLSに置き換えることで、`!`によるコマンド結果の動的注入など柔軟な機能が使える。元になるベースプロンプト自体を保管しておくのは悪くないが、静的にそのまま流用せず、SKILLSの動的組み立て機能を活用する工夫を忘れないこと。
- **メモリ（CLAUDE.md/rules/auto memory）に強制力を期待しない** — 従わせたい場合は必ずhooksを検討する。
- **1つの機構に複数の役割を詰め込まない** — 「このSKILLは知識も手順も強制もぜんぶやる」のような多目的化は、判断フローに従って機構ごとに分割する。

## 困ったときは

1. 選んだ機構の実装ディテール（frontmatter全項目・チェックリスト・具体的な手順）は、上記でリンクした専用スキル（claude-code-memory / writing-rules / writing-skill / writing-skill-complex / writing-subagents / writing-hooks）を使う。
2. Claude Code自体の仕様確認が必要な場合、または上記の判断が現行仕様とズレている可能性がある場合は**claude-code-docsスキル**で公式ドキュメント（`code.claude.com`）を参照する（本リポジトリのCLAUDE.mdのルールで必須）。
