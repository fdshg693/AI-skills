# OKF概念の書き方 — このリポジトリ向け（推奨案）

**このリポジトリはまだOKFに対応していない。** 以下は「もし導入するなら」の推奨案であり、現時点でこれに従って書かれた概念ドキュメントは存在しない。フィールドの意味・一般的な書き方（`sources`/`generated`/`verified`/`status`等の使い方、本文構造、Attested Computation等）は[WRITING_GENERAL.md](WRITING_GENERAL.md)に完全に委ねる。ここではこのリポジトリ特有の**バンドル配置**と**frontmatterキーのサンプル**のみを書く。

## バンドルの配置（推奨案）

バンドルルートはリポジトリ直下に新設する `docs/` とする。`.claude/`配下（Claude Code固有）ではなく、AIツールを問わずリポジトリ全体で参照する知識として独立させる。

```
docs/
  index.md                      # okf_version: "0.2" を持つバンドルルート一覧
  log.md                        # バンドル自体の更新履歴（リポジトリ全体のgit logではない）
  tools/                        # tools/配下の各ツールに対応する概念
    index.md
    aim.md
    sandbox.md
  claude-code/                  # AIツールごとの設定・プラグインに関する概念
    index.md
    plugins.md
  decisions/                    # このリポジトリ運用上の設計判断
    ai-tools-yaml-ssot.md
```

- サブディレクトリの切り方は[README.md](../../../../../README.md)の「AIツールごとの設定・プラグインルート」の分類（Claude Code / Cline / Codex / Copilot / Cursor / Antigravity / tools / maintenance/plugin）に揃えるのが最も迷いが少ない
- `decisions/` は、AGENTS.mdやSKILL.mdのようなSSOT・手順書には書ききれない「なぜその設計にしたか」を残す置き場として想定する

## frontmatterキーのサンプル（このリポジトリでの値の付け方）

`type`はOKF側で中央登録されない自由文字列。このリポジトリでは以下のような値を想定する。

| `type`の値        | 使う場面                                                   |
| ----------------- | ---------------------------------------------------------- |
| `AI Tool`         | Claude Code / Cline / Codex 等、AIツール本体についての知識 |
| `Plugin`          | `*-plugins/`配下の個別プラグインについての知識             |
| `Skill`           | `SKILL.md`単体では書ききれない運用知識・落とし穴           |
| `Wrapper Tool`    | `tools/`配下のラッパーCLI（`aim`、`claude-wrapper`等）     |
| `Design Decision` | SSOT化・命名規則など、このリポジトリ固有の設計判断         |
| `Known Issue`     | 既知の不具合・回避策                                       |

`generated.by` / `verified[].by`のactor記法（`<producer>/<version>` / `human:<id>` / `process:<id>`）は、このリポジトリでは実務上こう対応させる。

| actor例                           | 意味                                         |
| --------------------------------- | -------------------------------------------- |
| `human:fdshg693`                  | リポジトリオーナー本人が直接書いた・確認した |
| `reference_agent/claude-sonnet-5` | Claude Codeセッションが自律生成した          |
| `process:lefthook-pre-commit`     | `lefthook.yml`の自動フックが機械的に確認した |

`tags`は[README.md](../../../../../README.md)のフォルダ分類に揃える: `claude-code` / `cline` / `codex` / `copilot` / `cursor` / `antigravity` / `tools` / `repo-wide` / `maintenance` / `skills-site`。

`resource`および`sources[].resource`は、このリポジトリ内のファイルを指す場合はリポジトリルートからの相対パス（例: `tools/aim/README.md`）をそのまま使う。外部ツールの公式ドキュメント等を指す場合は通常のURLを使う。

以下は主要フィールドを一通り使ったサンプル（`docs/tools/aim.md`を想定）。

```markdown
---
type: Wrapper Tool
title: aim CLI
description: モデル呼び出しをラップするCLIツール。
resource: tools/aim/
tags: [tools, cli]
generated: { by: human:fdshg693, at: 2026-07-10T09:00:00Z }
verified:
  - { by: human:fdshg693, at: 2026-07-10T09:00:00Z }
  - { by: process:lefthook-pre-commit, at: 2026-08-01T03:00:00Z }
status: stable
stale_after: 2026-12-31
sources:
  - id: aim-readme
    resource: tools/aim/README.md
    title: aim README
    author: human:fdshg693
    last_modified: 2026-07-10
---

# Schema

（コマンド一覧・オプション）

# Examples

（実行例）
```

- `index.md`/`log.md`の書式自体（見出し・予約名・`okf_version`の置き場所）はこのリポジトリ固有の変更はなく、[WRITING_GENERAL.md](WRITING_GENERAL.md)の通り
