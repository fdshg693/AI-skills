# Custom Subagents詳細

出典: https://kilo.ai/docs/customize/custom-subagents （kilo.ai/docs `customize/custom-subagents`）

Kilo Codeの**custom subagents**は、primary agentや`@`メンションから起動される特化アシスタント。独自の分離セッションで、専用プロンプト・モデル・ツール権限を持つ。現在のところUI設定はなく、configファイル（`kilo.jsonc`）かmarkdown agentファイルで設定する。

## Subagentとは

primary agent（Code, Plan, Debug等）はユーザーが直接対話する主体。**subagent**は隔離コンテキストで部分タスクを処理する委譲先:

- **分離コンテキスト**: 独自のセッションと会話履歴を持つ
- **特化挙動**: タスクに合わせたプロンプトとツール権限
- **agent・ユーザーのどちらからでも起動可能**: primary agentはTask toolで呼ぶ。ユーザーは`@agent-name`で直接呼べる
- **結果は親に返る**: 完了すると結果サマリが親agentに返る

### built-in subagent

| 名前        | 説明                                                                                |
| ----------- | ----------------------------------------------------------------------------------- |
| **general** | 複雑な調査と複数ステップのタスクに使える汎用agent。todo以外の全ツールにアクセス可   |
| **explore** | コードベース探索専用の高速read-only agent。ファイル検索・コード検索・質問回答に使う |

## 定義方法

### 方法1: JSON config

`kilo.jsonc`の`agent`セクションに追加。built-in名と一致しないキーは新規custom agentになる:

```json
{
  "$schema": "https://app.kilo.ai/config.json",
  "agent": {
    "code-reviewer": {
      "description": "Reviews code for best practices and potential issues",
      "mode": "subagent",
      "model": "anthropic/claude-sonnet-4-20250514",
      "prompt": "You are a code reviewer. Focus on security, performance, and maintainability.",
      "permission": {
        "edit": "deny",
        "bash": "deny"
      }
    }
  }
}
```

プロンプトの外部ファイル参照も可能（configファイル位置からの相対パス。global/project両configで動く）:

```json
{
  "agent": {
    "code-reviewer": {
      "mode": "subagent",
      "prompt": "{file:./prompts/code-review.txt}"
    }
  }
}
```

### 方法2: markdownファイル

- **global**: `~/.config/kilo/agents/`
- **project**: `.kilo/agents/`

**ファイル名（`.md`を除く）がagent名**。長いプロンプトはmarkdownの方が保守しやすい（bodyがそのままシステムプロンプトになる）。

```markdown
---
description: Reviews code for quality and best practices
mode: subagent
model: anthropic/claude-sonnet-4-20250514
temperature: 0.1
permission:
  edit: deny
  bash: deny
---

You are a code reviewer. Analyze code for:

- Code quality and best practices
- Potential bugs and edge cases
- Performance implications
- Security considerations

Provide constructive feedback without making direct changes.
```

`.kilo/agents/`がプロジェクト外へのsymlinkの場合、global `~/.config/kilo/kilo.jsonc`でそのソースを許可する必要がある:

```jsonc
{
  "permission": {
    "markdown_source": {
      "/path/to/shared/agents/*": "allow",
    },
  },
}
```

project configではこの許可を与えられない。外部agentファイルはuntrusted扱い: `{env:...}`置換は禁止、`{file:...}`置換はプロジェクト内に限定される。

### 方法3: 対話的CLI

```bash
kilo agent create
```

globalかprojectか、description、mode（`all`/`primary`/`subagent`）、ツールを選ぶとAIがシステムプロンプトと識別子を生成して`.md`を書き出す。非対話実行も可:

```bash
kilo agent create \
  --path .kilo \
  --description "Reviews code for security vulnerabilities" \
  --mode subagent \
  --tools "read,grep,glob"
```

## 設定オプション

| オプション    | 型                                 | 説明                                                                                   |
| ------------- | ---------------------------------- | -------------------------------------------------------------------------------------- |
| `description` | `string`                           | 何をするagentでいつ使うか。primary agentがsubagent選択の判断に使う                     |
| `mode`        | `"subagent" \| "primary" \| "all"` | 使われ方。custom agentの既定は`all`                                                    |
| `model`       | `string`                           | `provider/model-id`形式。未設定なら**起動したprimary agentのモデルを継承**             |
| `prompt`      | `string`                           | カスタムシステムプロンプト。JSONは`{file:./path}`可、markdownはbodyがプロンプト        |
| `temperature` | `number`                           | 応答のランダム性（0.0-1.0）。低いほど決定的                                            |
| `top_p`       | `number`                           | temperatureの代替（0.0-1.0）                                                           |
| `permission`  | `object`                           | ツール権限                                                                             |
| `hidden`      | `boolean`                          | `true`なら`@`補完メニューから隠す。Task tool経由の起動は可能。`mode: subagent`のみ有効 |
| `steps`       | `number`                           | 最大反復数。コスト制御に有効                                                           |
| `color`       | `string`                           | hex（`#FF5733`）またはテーマ名（`primary`, `accent`, `error`等）                       |
| `disable`     | `boolean`                          | `true`でagentを無効化                                                                  |

一覧にない追加オプションはモデルプロバイダにパススルーされる（OpenAIの`reasoningEffort`等のプロバイダ固有パラメータが使える）。

## permission

各ツール権限は3値:

- `"allow"` — 承認なしで許可
- `"ask"` — 実行前にユーザー承認
- `"deny"` — 完全に無効

bashはコマンド単位でglobパターン指定可。**最後にマッチしたルールが優先**:

```json
{
  "agent": {
    "reviewer": {
      "mode": "subagent",
      "permission": {
        "edit": "deny",
        "bash": {
          "*": "ask",
          "git diff": "allow",
          "git log*": "allow"
        }
      }
    }
  }
}
```

`permission.task`で、そのagentが**呼べるsubagentを制御**できる:

```json
{
  "agent": {
    "orchestrator": {
      "mode": "primary",
      "permission": {
        "task": {
          "*": "deny",
          "code-reviewer": "allow",
          "docs-writer": "allow"
        }
      }
    }
  }
}
```

## Subagentの使い方

### 自動起動

primary agent（特にOrchestrator）は、タスクに`description`がマッチするとTask toolで自動的にsubagentを呼ぶ。**選ばれるためにdescriptionを明確に書くこと**。

### `@`メンションによる手動起動

```
@code-reviewer review the authentication module for security issues
```

subagentの分離コンテキストで、設定されたプロンプトと権限の下でサブタスクが走る。

### agent一覧

```bash
kilo agent list
```

名前・mode・permission設定が表示される。

## VS Codeでの委譲セッション確認

VS Code拡張でsubagentが委譲されたら、タスクカードまたはbackground-agent行からtranscriptを開く。Agent Managerでは**Subagents**インスペクタに読み取り専用タブとして開く。タブストリップで複数の子セッションを切替・並替・クローズできる。タブは現在のprojectと親セッションにスコープされる（別worktree/sessionの子transcriptは混ざらない）。

子セッションは**委譲されたtranscript**であり、直接メッセージを送れる新しいプロンプトではない点に注意。

## 設定の優先順位

後のソースが前を上書き（merge）:

1. **built-in agentの既定**
2. **global config**（`~/.config/kilo/config.json`）
3. **project config**（ルートの`kilo.jsonc`）
4. **global agent markdown**（`~/.config/kilo/agents/*.md`）
5. **project agent markdown**（`.kilo/agents/*.md`）

built-inのoverrideは指定したフィールドのみmerge。新規custom agentの未指定フィールドは既定値（`mode: "all"`、global config由来の権限継承）。

## built-in agentのoverride・無効化

built-in `explore`のモデル変更:

```json
{
  "agent": {
    "explore": {
      "model": "anthropic/claude-haiku-4-20250514"
    }
  }
}
```

built-in `general`の無効化:

```json
{
  "agent": {
    "general": {
      "disable": true
    }
  }
}
```

## 実例

### Documentation Writer（bash禁止）

```markdown
---
description: Writes and maintains project documentation
mode: subagent
permission:
  bash: deny
---

You are a technical writer. Create clear, comprehensive documentation.

Focus on:

- Clear explanations with proper structure
- Code examples where helpful
- User-friendly language
- Consistent formatting
```

### Security Auditor（read-only、コマンド絞り込み）

```markdown
---
description: Performs security audits and identifies vulnerabilities
mode: subagent
permission:
  edit: deny
  bash:
    "*": deny
    "git log*": allow
    "grep *": allow
---

You are a security expert. Focus on identifying potential security issues.

Report findings with severity levels and remediation suggestions.
```

### Test Generator（config定義）

```json
{
  "agent": {
    "test-gen": {
      "description": "Generates comprehensive test suites for existing code",
      "mode": "subagent",
      "prompt": "You are a test engineer. Write comprehensive tests following the project's existing test patterns. Use the project's test framework. Cover edge cases and error paths.",
      "temperature": 0.2,
      "steps": 15
    }
  }
}
```

### Restricted Orchestrator（委譲先を制限）

```json
{
  "agent": {
    "orchestrator": {
      "permission": {
        "task": {
          "*": "deny",
          "code-reviewer": "allow",
          "test-gen": "allow",
          "docs-writer": "allow"
        }
      }
    }
  }
}
```

## 関連

- [Custom Modes](https://kilo.ai/docs/customize/custom-modes) — ツール制限付きの特化primary agent（本スキルの [modes.md](modes.md)）
- [Agent Permissions](https://kilo.ai/docs/customize/agent-permissions) — ルール優先順位・シェルコマンドパターン・パスマッチング・機密ファイル挙動
- [Orchestrator Mode](https://kilo.ai/docs/code-with-ai/agents/orchestrator-mode) — タスク委譲用のlegacy mode（現在は全agentに統合）
- [Task tool](https://kilo.ai/docs/automate/tools) — subagentを起動するツール
