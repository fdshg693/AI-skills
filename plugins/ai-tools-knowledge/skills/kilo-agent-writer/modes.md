# Custom Modes（primary agent）詳細

出典: https://kilo.ai/docs/customize/custom-modes （kilo.ai/docs `customize/custom-modes`）

Kilo Codeの**custom modes**（現行では **agents** とも呼ばれる）は、タスクやワークフローに特化した挙動を作るためのもの。**global**（全プロジェクト共通）・**project固有**・**組織管理**の3スコープがある。

## なぜModeを作るか

- **特化**: 「Documentation Writer」「Test Engineer」「Refactoring Expert」等のタスク最適化
- **安全**: 機密ファイル・コマンドへのアクセス制限（read-onlyのReview Mode等）
- **実験**: 他Modeに影響せずにプロンプト・設定を試せる
- **チーム共有**: ワークフローの標準化
- **組織の一貫性**: 組織管理agentはbuilt-inと同名可（組織定義が優先）。メンバーはローカルから削除できない

## Agentの構成要素

| プロパティ                  | 説明                                                                               |
| --------------------------- | ---------------------------------------------------------------------------------- |
| **name**（ファイル名）      | `.md`のファイル名がagent名になる（`docs-writer.md` → `docs-writer`）               |
| **description**             | picker表示とOrchestratorの委譲判断に使われる短い要約                               |
| **model**                   | `provider/model`形式でモデルをピン留め（例: `anthropic/claude-sonnet-4-20250514`） |
| **prompt**（markdown body） | システムプロンプト。ファイルのmarkdown body                                        |
| **mode**                    | `primary`（ユーザー選択可能）/ `subagent`（他agentからのみ）/ `all`（両方）        |
| **permission**              | agentごとのツール権限override（例: `edit`/`bash`のdeny）                           |
| **color**                   | hex（`#FF5733`）またはテーマキーワード（`primary`, `accent`, `warning`等）         |
| **steps**                   | テキストのみ応答を強制するまでの最大反復回数                                       |
| **temperature** / **top_p** | モデルのサンプリングパラメータ                                                     |
| **variant**                 | 既定のモデルvariant                                                                |
| **hidden**                  | `true`ならUIから隠す（subagentのみ意味を持つ）                                     |
| **disable**                 | `true`ならagent自体を削除                                                          |

## 作成・設定方法

### 1. Kiloに依頼する（推奨）

```
Create a new agent called "docs-writer" that can only read files and edit Markdown files.
```

`.kilo/agent/`配下にagent定義が生成される。

### 2. UI / CLIの対話コマンド

- VS Code拡張: **Settings → Agent Behaviour → Agents**サブタブで表示・作成・編集
- CLI: `kilo agent create`（description・mode・ツールを選択し、LLMがシステムプロンプトを生成して`.md`を書き出す）

### 3. YAML frontmatter付きmarkdown

置き場所:

```
.kilo/agents/my-agent.md
.kilo/agent/my-agent.md
~/.config/kilo/agent/my-agent.md   （global）
```

legacyの`.kilocode/agents/`も後方互換で読む。**ファイル名（`.md`を除く）がagent名**。ネストディレクトリは名前空間（`agents/backend/sql.md` → `backend/sql`）。

例（`.kilo/agents/docs-writer.md`）:

```markdown
---
description: Specialized for writing and editing technical documentation
mode: primary
color: "#10B981"
permission:
  edit:
    "*.md": "allow"
    "*": "deny"
  bash: deny
---

You are a technical documentation specialist. Your expertise includes:

- Writing clear, well-structured documentation
- Following markdown best practices
- Creating helpful code examples

Focus on clarity and completeness. Only edit Markdown files.
```

### 4. configファイル（`kilo.jsonc`）

`agent`キーの下に定義:

```jsonc
{
  "agent": {
    "docs-writer": {
      "description": "Specialized for writing and editing technical documentation",
      "mode": "primary",
      "color": "#10B981",
      "prompt": "You are a technical documentation specialist...",
      "permission": {
        "edit": { "*.md": "allow", "*": "deny" },
        "bash": "deny",
      },
    },
    // built-in agentのoverride
    "code": {
      "model": "anthropic/claude-sonnet-4-20250514",
      "temperature": 0.3,
    },
  },
}
```

## プロパティ詳細

### `mode`

| 値         | 挙動                                                           |
| ---------- | -------------------------------------------------------------- |
| `primary`  | agent pickerに表示され、ユーザーが直接選択                     |
| `subagent` | 他agentの`task`ツールからのみ起動                              |
| `all`      | トップレベル選択とsubagentの両方で利用可（ユーザー定義の既定） |

### `permission`

順序付きルール。`allow` / `deny` / `ask`（ユーザー承認を求める）の3アクション。globでファイル・コマンドに絞れる:

```yaml
permission:
  edit:
    "*.md": "allow"
    "*": "deny"
  bash: deny
  read: allow
```

既知のpermissionタイプ: `read`, `edit`, `bash`, `glob`, `grep`, `task`, `webfetch`, `websearch`, `todowrite`, `todoread` 等。

### `model`

`provider/model`形式でピン留め。UI/TUIは**agentごとに最後に選んだモデルを記憶**する。configのピンは手動選択がない場合の既定になる。リセットはmodel picker（CLI: `Ctrl+X m`、または`~/.local/state/kilo/model.json`から削除）。

### `steps`

tool呼び出しラウンドの最大反復数。超えるとテキストのみの応答を強制。暴走防止:

```yaml
steps: 25
```

## 設定の優先順位

低い→高い順でmerge（丸ごと置換ではなくプロパティ単位のmerge）:

1. built-in agentの既定
2. global config（`~/.config/kilo/kilo.jsonc`）
3. project config（ルートの`kilo.jsonc`）
4. `.kilo/` / legacy `.kilocode/` 配下のconfigとagent `.md`（subagentsページの記載では global md → project md の順）
5. 環境変数override（`KILO_CONFIG_CONTENT`）

## built-in agentのoverride

built-in（**code**, **plan**, **debug**, **ask**, **orchestrator**, **explore**, **general**）と同名で定義するとoverride（merge）される:

```markdown
# .kilo/agents/code.md

---

model: openai/gpt-4o
temperature: 0.2
permission:
edit:
"_.py": "allow"
"_": "deny"
---

You are a Python specialist. Only edit Python files.
```

## legacy Modeからのマイグレーション

`.kilocodemodes` / `custom_modes.yaml`は起動時に自動マイグレーションされる:

- `slug` → agent名
- `roleDefinition` + `customInstructions` → `prompt`
- `groups`（`["read", "edit", "browser"]`等） → `permission`ルール
- `whenToUse` / `description` → `description`
- modeは`primary`に設定

既定のlegacy slug（`code`, `build`, `architect`, `ask`, `debug`, `orchestrator`）はbuilt-inに対応するためスキップ（`build` → `code`、`architect` → `plan`）。

CLIのlegacy読み込みパス（最後に読んだものが優先）:

| 順  | パス                                                      | スコープ                |
| --- | --------------------------------------------------------- | ----------------------- |
| 1   | VS Code拡張globalストレージ `/settings/custom_modes.yaml` | global                  |
| 2   | `~/.kilocode/cli/global/settings/custom_modes.yaml`       | global                  |
| 3   | `~/.kilocodemodes`                                        | global                  |
| 4   | `<project>/.kilocodemodes`                                | project（競合時に優先） |

`~/.config/kilo/`に置いたlegacy `custom_modes.yaml`は**読み込まれない**。新形式は`~/.config/kilo/agent/*.md`か`~/.config/kilo/kilo.jsonc`を使う。

## ファイルアクセスの制限

順序付きglobルール。**最後にマッチしたルールが優先**なので、広い既定を先・具体な例外を後に置く:

```jsonc
{
  "permission": {
    "edit": {
      "*": "deny",
      "*.md": "allow",
      "docs/**": "allow",
    },
  },
}
```

## 実例

### Test Engineer（`.kilo/agents/test-engineer.md`）

```markdown
---
description: Focused on writing and maintaining test suites
mode: primary
color: "#F59E0B"
permission:
  edit:
    "*.{test,spec}.{js,ts}": "allow"
    "*": "deny"
---

You are a test engineer focused on code quality.
Use for writing tests, debugging test failures, and improving test coverage.
```

### Security Reviewer（read-only）

```markdown
---
description: Read-only security analysis and vulnerability assessment
mode: primary
color: "#EF4444"
permission:
  edit: deny
  bash: deny
---

You are a security specialist reviewing code for vulnerabilities.
```

## Troubleshooting

- **agentが出ない**: `.md`が認識ディレクトリ（`.kilo/agents/`, `.kilo/agent/`, `.kilocode/agents/`）にあるか。pickerに出すには`mode`が`primary`か`all`か
- **permissionエラー**: last-match-wins。期待したツールが使えないなら`deny`より後に`allow`があるか
- **frontmatterのパースエラー**: `---`で挟む、キー名は`top_p`等の正しい名前
- **overrideが効かない**: global→projectの順でmerge。同名であることが必須

## ヒント

- bodyはシステムプロンプト。同僚へのブリーフィングとして焦点を絞って書く
- ユーザーに直接選ばせたくないhelperは`mode: subagent`
- legacyファイルは自動マイグレーションされるので手動移行は不要。新しいmodeは新形式側で追加する
- コミュニティ例はGitHubのShow and Tellカテゴリ参照
