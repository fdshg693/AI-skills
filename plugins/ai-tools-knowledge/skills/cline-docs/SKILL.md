---
name: cline-docs
description: Answer questions about Cline using the latest official documentation at docs.cline.bot. Use for Cline IDE/CLI/SDK features, skills, rules, workflows, configuration, API, providers, MCP, plugins, enterprise features, or troubleshooting when current documented behavior matters.
meta:
  tag: []
  requires_repo_tools: none
  requires_env: none
  dependencies: python
  requires_install: none
  requires_hooks: none
  requires_skills: none
  status: stable
  description: no description
  version: 1.0.4
---

# Cline 公式ドキュメント参照

Cline に関する質問では、学習データの記憶だけで回答せず、`docs.cline.bot` のローカルスナップショットを一次情報として使う。料金、対応機能、CLI/APIの仕様、配置場所、設定項目など変更されやすい内容は、必ず今回取得した資料で確認する。

## 取得

スキルを使い始めたら、まずスキルディレクトリを基準に次を実行する。

```bash
python scripts/download_cline_reference.py
```

このスクリプトは `llms.txt`（索引）と `llms-full.txt`（全文）を `output/` に保存し、各ファイルの取得時刻を記録する。24時間以内のスナップショットは再利用される。最新化が必要な場合だけ `--force` を付ける。

## 調査手順

1. `output/llms.txt` を先に読み、質問に関係するページの完全なパスと `Source` URL を特定する。
2. 詳細が必要なら、全文を毎回読み込まず、該当ページだけを抽出する。

   ```bash
   python scripts/extract_doc_section.py customization/skills
   python scripts/extract_doc_section.py cli/cli-reference sdk/guides/creating-custom-tools
   ```

   抽出結果は `output/temp/` に書き出されるので、そのファイルを読んで回答する。末尾セグメントだけでなく、`api/authentication` のようなパス全体を指定する。

3. 索引や全文に該当ページがない、または内容が古い可能性がある場合は、`https://docs.cline.bot/` 配下の該当ページを直接取得して確認する。
4. 回答では、根拠にした公式ページの URL を明示する。確認できない仕様は断定せず、スナップショットの取得時刻または未確認であることを伝える。

## 判断の境界

- **Skills** は特定の作業で必要な手順・知識をオンデマンドで読み込むもの。`.cline/skills/` または `~/.cline/skills/` に配置する。
- **Rules** はコーディング規約やプロジェクト固有の制約など、会話をまたいで常に適用するもの。`.clinerules/` に置く。
- **Plugins** はCLI・SDK・Kanban向けにツールやHooksなどを拡張する仕組みで、IDE拡張のSkillsとは区別する。

Skillsの仕様を説明する場合は `customization/skills`、Rulesとの違いは `customization/cline-rules`、設定場所は `getting-started/config` を優先して参照する。Clineの機能全般、CLI、API、SDK、プロバイダー、MCP、エンタープライズについても、索引から対応するページを選び、必要な全文セクションだけを読む。

## 注意

- `SKILL.md` の `name` はディレクトリ名 `cline-docs` と一致している。
- 公式ドキュメントにない挙動を、Claude Codeや他のエージェントの仕様から類推しない。
- 秘密情報、APIキー、ローカル設定値を回答やスナップショットに書き込まない。
