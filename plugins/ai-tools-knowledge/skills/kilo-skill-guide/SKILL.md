---
# 詳細仕様は同階層の skill-structure.md を必要時だけ読む。
name: kilo-skill-guide
description: Kilo Code（kilo.ai、CLI/TUI/VS Code拡張）のSkillを設計・分割・保守するための実践スキル。SKILL.mdの責務、詳細資料の分離、オンデマンド参照、AGENTS.mdやRulesとの使い分けを判断するときに使う。
meta:
  tag: []
  requires_repo_tools: none
  requires_env: none
  dependencies: none
  requires_install: none
  requires_hooks: none
  requires_skills: none
  status: experimental
  description: Kilo Skillの設計と責務分離ガイド
  version: 1.0.1
---

# Kilo Skill Guide

Kilo CodeのSkillを、必要なときに読み込む再利用可能な手順・専門知識として設計するためのガイド。

## 使う場面

- 反復する作業手順やドメイン知識を再利用したいとき
- 長い仕様や具体例を、起動判断用の本文から分離したいとき
- 常設指示、Rules、agent promptとの責務を整理したいとき

## 基本方針

1. `SKILL.md`には、いつ使うか、何を達成するか、最小ワークフローだけを書く。
2. API仕様、設定一覧、具体例、トラブルシューティングは隣接ファイルへ分離する。
3. 詳細ファイルは必要な場合だけ読むよう、`SKILL.md`から明示的にリンクする。
4. 常時守るプロジェクト規約は`AGENTS.md`、Kilo固有のルール制御は`instructions`、特定agentの役割はagent promptに置く。
5. 機密情報や認証情報をSkillへ保存しない。

詳細は [skill-structure.md](skill-structure.md) を参照する。

## 出典

- https://kilo.ai/docs/customize/skills
- https://kilo.ai/docs/customize/agents-md
- https://kilo.ai/docs/customize/custom-rules

公式ページの確認日: 2026-09-01
