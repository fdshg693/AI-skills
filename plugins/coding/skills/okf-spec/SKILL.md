---
# 同梱ファイル: SUMMARY.md（spec要約、通常はここで足りる）/ FINDING.md（OKFバンドルの探し方）/ WRITING_GENERAL.md（OKF概念の一般的な書き方）/ WRITING_REPO.md（このリポジトリ向けの配置・frontmatter推奨案）
# output/SPEC.md は download_okf_spec.py が定期取得する原文（1000行超）。直接Readせず、本文の手順（Grep/サブエージェント）を使う
name: okf-spec
description: Use when finding, reading, authoring, or answering questions about Open Knowledge Format (OKF) bundles or concept documents — a markdown+YAML-frontmatter convention (GoogleCloudPlatform/knowledge-catalog) for knowledge that AI agents write and consume. Grounds answers in a periodically re-fetched snapshot of the official spec instead of training-data memory, which may be stale or predate v0.2's provenance/trust/lifecycle/attestation fields.
allowed-tools: Bash(python ${CLAUDE_SKILL_DIR}/download_okf_spec.py *)
meta:
  tag: []
  requires_repo_tools: none
  requires_env: none
  dependencies: requests
  requires_install: none
  requires_hooks: none
  requires_skills: writing-skill-web
  status: stable
  description: no description
  version: 1.0.1
---

!`python ${CLAUDE_SKILL_DIR}/download_okf_spec.py`

# Open Knowledge Format (OKF)

OKF（現行 v0.2）は、データ・システムを取り巻く「知識」（メタデータ・文脈・キュレーションされた洞察）を表現するための、YAML frontmatter付きmarkdownファイルのディレクトリという最小限のフォーマット。人が書き、エージェントが生成し、組織を超えて交換され、両者が消費することを想定している。中央スキーマレジストリも必須ツールも無い。v0.2では、エージェントが継続的にメンテする知識コーパスを信頼できるものにするため、**provenance（出所）・trust（信頼度）・lifecycle（版状態）・attestation（計算の証明）** が frontmatter の一級フィールドになった。

これ以上の詳細（用語・全フィールド・バンドル構造・conformance規則等）はここには書かない。目的別に以下を参照する。

## どのファイルを読むか

| 目的                                                        | 読むファイル                             |
| ----------------------------------------------------------- | ---------------------------------------- |
| OKF全体像・フィールドの意味を知りたい（通常はここで足りる） | [SUMMARY.md](SUMMARY.md)                 |
| 既存のOKFバンドルから概念を探したい・辿りたい               | [FINDING.md](FINDING.md)                 |
| 新しい概念を書きたい・既存を更新したい（一般的な書き方）    | [WRITING_GENERAL.md](WRITING_GENERAL.md) |
| このリポジトリ向けに書きたい（配置・frontmatterの推奨案）   | [WRITING_REPO.md](WRITING_REPO.md)       |
| 条文の正確な文言・SUMMARY.mdに無い細部が必要                | 下記「原文にあたる場合」                 |

## 原文にあたる場合 — `output/SPEC.md`を直接Readしない

`output/SPEC.md`は起動時に自動取得される原文（約1000行、GoogleCloudPlatform/knowledge-catalogの`okf/SPEC.md`をそのまま保存したもの）。**全文をReadツールで開かない。** SUMMARY.md/FINDING.md/WRITING_GENERAL.md/WRITING_REPO.mdで足りない場合のみ、以下のどちらかを使う。

1. **特定のキーワード・フィールド名を探すだけ** → `output/SPEC.md`をGrepする（例: `stale_after`、`Attested Computation`、`§10.2`など、SUMMARY.mdの「原文の節番号対応」表で節を特定してから該当キーワードを絞り込むと早い）
2. **ある節をまとめて読み込んで要約・引用したい** → Agentツール（Explore、または汎用サブエージェント）に`output/SPEC.md`のパスと知りたい節・疑問点を渡し、そちらに読ませて結果だけを受け取る。メインの会話コンテキストに原文全体を持ち込まない

## 補足

- `output/SPEC.md`のfrontmatter（`source`/`fetched_at`）が鮮度の記録。24時間以内なら再取得をスキップする（`--force`で強制更新）。取得先URLは`download_okf_spec.py`内の`SOURCE_URL`
- SUMMARY.md/FINDING.md/WRITING_GENERAL.md/WRITING_REPO.mdはこのスキル作成時点のv0.2内容を反映した手書きの要約であり、`output/SPEC.md`が更新されても自動追従はしない。spec側に破壊的変更（§12のmajorバンプ）が入ったと分かった場合は、この4ファイルの見直しを検討する
