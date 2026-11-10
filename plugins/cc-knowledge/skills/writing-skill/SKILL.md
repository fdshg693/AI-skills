---
# 同梱ファイル: writing.md（新規作成・編集手順）/ evaluating.md（既存スキルの評価手順）/ bestpractices.md（両者が参照する共通チェックリスト）/ skills-reference.md（スキル機構自体のリファレンス）
# ファイル分割の設計意図・writing-skill-complexとの使い分けの詳細は同階層のREADME.md参照（人間のメンテナ向け）
name: writing-skill
# TDD的なサブエージェント検証は行わない低コスト・日常用途版。高コストなwriting-skill-complexとは棲み分け、モデルの自動起動はこちらに任せる
description: Use when creating, editing, or evaluating a SKILL.md against best practices — lightweight, everyday guidance covering both writing and reviewing skills. For high-cost subagent-verified TDD testing before deploying critical or widely-shared skills, use writing-skill-complex instead.
meta:
  tag: []
  requires_repo_tools: none
  requires_env: none
  dependencies: none
  requires_install: none
  requires_hooks: none
  requires_skills: claude-code-docs,writing-skill-complex
  status: stable
  description: no description
  version: 2.0.0
---

# スキル作成・評価

新しいスキルの作成・既存`SKILL.md`の編集、および既存スキルがベストプラクティスに沿っているかの評価を扱うエントリポイント。目的に応じて参照先を切り替える。

このスキルはサブエージェントによる負荷テストを行わない軽量版。バグを埋め込めない共有スキルや、破壊的操作を伴うスキルを厳密に検証したい場合は**writing-skill-complexスキル**（明示呼び出し専用、TDDベースで高コスト）を使う。

## 手順

1. **新規作成・既存の編集**なら [writing.md](writing.md) を読み、その手順に従う
2. **既存スキルの評価**（ベストプラクティスへの準拠を確認したい）なら [evaluating.md](evaluating.md) を読み、その手順に従う
3. 両者が参照する共通チェックリストは [bestpractices.md](bestpractices.md)
4. スキル機構そのもの（配置場所・フロントマター全フィールド・引数展開・動的コンテキスト注入など）の詳細は [skills-reference.md](skills-reference.md)

## 困ったときは

- Claude Codeの仕様そのものについて最新の公式ドキュメントに基づく回答が必要な場合は**claude-code-docsスキル**
- 共有スキル・破壊的操作を伴うスキルなど、サブエージェントによる厳密なTDD検証が必要な場合は**writing-skill-complexスキル**（明示呼び出し専用、高コスト）
