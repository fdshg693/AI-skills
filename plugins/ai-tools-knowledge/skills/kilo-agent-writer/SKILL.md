---
# 詳細仕様は同階層の modes.md / subagents.md を必要時だけ読む。仕様変更が疑わしい場合の最終フォールバックは kilo-code-docs スキルで customize/custom-modes と customize/custom-subagents を確認する。
name: kilo-agent-writer
description: Kilo Code（kilo.ai、CLI/TUI/VS Code拡張）のMode/Agent（primary agent＝Custom Mode、subagent＝Custom Subagent）を新規作成・編集するためのメタスキル。Use when creating, updating, or choosing between Kilo custom modes (primary agents) and custom subagents — agent markdown files (.kilo/agent(s)/*.md), kilo.jsonc `agent` entries, mode/permission/model/steps/hidden settings, built-in agent overrides, or deciding mode vs subagent vs skill vs plugin.
meta:
  tag: []
  requires_repo_tools: none
  requires_env: none
  dependencies: none
  requires_install: none
  requires_hooks: none
  requires_skills: kilo-code-docs
  status: experimental
  description: no description
  version: 1.0.0
---

# Kilo Mode/Agent Writer

Kilo Code（CLI/TUI/VS Code拡張）用の**Mode（primary agent）とSubagent**を作る・直すときの実践ガイド。

現行のKiloでは、かつての「Mode」は**Agent**に統合されている。Custom ModeとCustom Subagentは別機能ではなく**同一の仕組み**（agent定義）であり、frontmatterの`mode`フィールドで区別される:

| `mode`値   | 呼び方                       | 挙動                                                                                                                   |
| ---------- | ---------------------------- | ---------------------------------------------------------------------------------------------------------------------- |
| `primary`  | Custom Mode（primary agent） | agent pickerに表示され、ユーザーが直接選択（Tabで切替）                                                                |
| `subagent` | Custom Subagent              | 他agentの`task`ツールまたは`@agent-name`メンション経由でのみ起動。分離されたセッションで実行され、結果サマリが親に返る |
| `all`      | 両方                         | 両方で使える。**ユーザー定義agentの既定値**                                                                            |

定義方法は共通で、YAML frontmatter付きmarkdownファイル（`.kilo/agents/`, `.kilo/agent/`, globalは`~/.config/kilo/agent/`。legacy `.kilocode/agents/`も読む）か、`kilo.jsonc`の`agent`キー。**ファイル名（`.md`を除く）がagent名**（ネストしたディレクトリは`backend/sql`のような名前空間名になる）。

各機能の詳細は必要になった時だけ [modes.md](modes.md)（primary agent）と [subagents.md](subagents.md)（subagent）を読む。

## 対象と非対象

- **対象**: primary agent（Mode）とsubagentの新規作成・編集・built-in agentのoverride、`permission`/`model`/`steps`等の調整、ModeとSubagentの使い分け判断。
- **非対象**: 手順・ドメイン知識の再配布 → Skill（`.kilo/skills/`）で足りる場合はagentにしない（agentは分離コンテキスト・モデル・権限の制御が目的）。
- **非対象**: コードによる拡張（カスタムツール、tool呼び出しの介入、chat/providerフック） → Plugin（`@kilocode/plugin`）。kilo-plugin-writerスキル参照。
- **非対象**: 常時適用したい指示 → Custom Rules / AGENTS.md / Custom Instructions。

## まず判断すること（使い分け）

1. **Mode（primary）にすべきかSubagentにすべきか**
   - **ユーザーが会話の主導権を持つワークフロー**（自分がModeを切り替えて使う） → `mode: primary`
   - **他のagent（特にOrchestrator）への委譲用**・隔離コンテキストで走らせたい部分タスク → `mode: subagent`。`description`はprimary agentの選択判断に使われるので「何をいつ使うか」を明確に書く
   - 迷うなら既定の`mode: all`のままにするか、`subagent`から始めて必要になったら`primary`/`all`に緩める
2. **agentですら必要か**
   - 権限・モデル・分離コンテキストの制御が不要な手順知識 → Skillで十分
   - 常時効かせたい指示 → Rules/AGENTS.md
   - コード拡張が必要 → Plugin
3. **built-inで足りるか**
   - built-in agentは`code`, `plan`, `debug`, `ask`, `orchestrator`, `explore`, `general`。同名定義でプロパティ単位のoverride（model/temperatureだけ変える等）ができる。新規作成前にまずoverrideで済まないか確認する
4. **mdファイルかconfigか**
   - 長いプロンプト・git管理したい → `.kilo/agents/*.md`（bodyがシステムプロンプトになり、読みやすい）
   - 既存configにまとめたい・`{file:./path}`で外部プロンプトを参照したい → `kilo.jsonc`の`agent`キー

## 作成フロー

1. **`mode`を決める**（`primary` / `subagent` / `all`。省略時`all`）
2. **`description`を書く** — picker表示・Orchestratorの委譲判断の両方に使われる
3. **body（システムプロンプト）を書く** — 同僚へのブリーフィングとして書く。聚焦させる
4. **`permission`を最小化する** — `allow` / `ask` / `deny`、globでパス・コマンドを絞れる、**最後にマッチしたルールが優先**なので広いdenyを先に、例外のallowを後に置く
5. **必要なら`model`（`provider/model`）・`steps`（暴走/コスト対策）・`temperature`/`top_p`を設定**
6. **`kilo agent list`で反映を確認**（CLI）/ Settings → Agent Behaviour → Agentsで確認（VS Code拡張）

## 最小例

```markdown
# .kilo/agents/docs-writer.md — primary agent（Custom Mode）

---

description: Specialized for writing and editing technical documentation
mode: primary
color: "#10B981"
permission:
edit:
"_.md": "allow"
"_": "deny"
bash: deny
---

You are a technical documentation specialist. Only edit Markdown files.
```

```markdown
# .kilo/agents/code-reviewer.md — subagent

---

description: Reviews code for best practices and potential issues
mode: subagent
permission:
edit: deny
bash:
"_": ask
"git diff": allow
"git log_": allow
---

You are a code reviewer. Focus on security, performance, and maintainability.
Provide constructive feedback without making direct changes.
```

## ベストプラクティス

- **subagentの`description`は自動選出の要**: primary agent（Orchestrator含む）はdescriptionのマッチで`task`ツール経由でsubagentを呼ぶ。曖昧なdescriptionは委譲されない
- **`permission`はlast-match-wins**: `edit: { "*": "deny", "docs/**": "allow" }`のように広いルールを先、例外を後に
- **読み取り専用agentは明示する**: `edit: deny` + `bash: deny`（built-in `explore`相当の使い方）
- **委譲先を絞る**: `permission.task`（`{ "*": "deny", "code-reviewer": "allow" }`）でorchestratorが呼べるsubagentを制限できる
- **`steps`でコスト制御**: 反復上限を超えるとテキストのみの応答を強制される
- **`hidden: true`**（subagentのみ有効）で`@`補完から隠しつつTask tool経由は維持できる
- **promptの外部化**: configなら`"prompt": "{file:./prompts/code-review.txt}"`（configファイル位置からの相対パス）
- **`model`ピン留めのリセット**: UIでagentごとの最終選択モデルが記憶される。config指定に戻すにはmodel pickerでリセット

## よくある落とし穴

- **モダンな場所にlegacyファイルを置く**: `~/.config/kilo/`にはlegacy `custom_modes.yaml`は**読み込まれない**。新形式は`~/.config/kilo/agent/*.md`か`kilo.jsonc`
- **agent pickerに出ない**: ファイルの場所（`.kilo/agents/`, `.kilo/agent/`, `.kilocode/agents/`）と`mode`が`primary`/`all`かを確認
- **権限が効かない**: last-match-winsの順序、`allow`が`deny`より後に来ているか確認。frontmatterのキー名は`top_p`（`topP`ではない）
- **overrideが効かない**: 同一agent名でglobal→projectの順でmergeされる。名前が一致していないと別agentとして新規作成される
- **symlinkの`.kilo/agents/`**: プロジェクト外を指す場合はglobal configの`permission.markdown_source`で許可が必要。外部agentファイルはuntrusted（`{env:...}`禁止、`{file:...}`はプロジェクト内に限定）
- **`.kilocodemodes`手動編集**: 自動マイグレーション（`slug`→agent名、`roleDefinition`+`customInstructions`→`prompt`、`groups`→`permission`）があるので、起動後に新形式側を編集する

## 出力時のチェックリスト

- [ ] `mode`が意図通り（primary=Mode、subagent=委譲専用、all=両方・既定）
- [ ] `description`が「何をいつ使うか」をagent選択に十分伝えている
- [ ] `permission`が最小権限で、ルール順序がlast-match-winsに従っている
- [ ] ファイル名（=agent名）が組み込みagentと意図せず衝突していない（衝突はoverrideになる）
- [ ] 暴走防止の`steps`・必要な`model`ピンを検討済み
- [ ] `kilo agent list`（またはSettings UI）で反映を確認済み（可能な場合）

## 困ったとき

1. primary agent（Mode）の詳細は [modes.md](modes.md)（プロパティ全表、Settings UI、built-in override、legacyマイグレーション、troubleshooting）。
2. subagentの詳細は [subagents.md](subagents.md)（設定オプション全表、`permission.task`、`@`メンション、`kilo agent create`、VS CodeのSubagentsインスペクタ、実例）。
3. 仕様が変わっていそうなら、最終フォールバックとして **kilo-code-docs スキル**で `customize/custom-modes` と `customize/custom-subagents`（必要なら `customize/agent-permissions`）を確認する。
