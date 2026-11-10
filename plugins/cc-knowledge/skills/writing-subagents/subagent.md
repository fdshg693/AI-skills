# claudeコマンドでの、サブエージェントの利用方法

> 参考文献: [Create custom subagents](https://code.claude.com/docs/en/sub-agents) / [CLI reference](https://code.claude.com/docs/en/cli-reference)

## 目次

- [基本概要](#基本概要)
- [似ているが2種類のコマンドがある](#似ているが2種類のコマンドがある)
- [組み込み（built-in）サブエージェント](#組み込みbuilt-inサブエージェント)
- [サブエージェントの設定ファイルの書き方](#サブエージェントの設定ファイルの書き方)
  - [フロントマターの全フィールド一覧](#フロントマターの全フィールド一覧)
  - [モデルの選び方](#モデルの選び方)
  - [ツールアクセスの制御](#ツールアクセスの制御)
  - [永続メモリ（memory）](#永続メモリmemory)
  - [補足（フックによる細かい制御）](#補足フックによる細かい制御)
- [明示的な呼び出し方](#明示的な呼び出し方)
- [フォアグラウンド／バックグラウンド実行](#フォアグラウンドバックグラウンド実行)
- [入れ子のサブエージェント](#入れ子のサブエージェント)
- [サブエージェントの再開（resume）](#サブエージェントの再開resume)
- [会話をフォークする（fork）](#会話をフォークするfork)
- [コンテキストに何がロードされるか](#コンテキストに何がロードされるか)
- [API エラー時の挙動](#api-エラー時の挙動)
- [無効化する方法](#無効化する方法)
- [サンプル](#サンプル)
- [参考文献](#参考文献)

## 基本概要

サブエージェントは、特定の種類のタスクを専門に処理するAIアシスタント。検索結果・ログ・ファイル内容など、後で参照しないが大量になるものをメイン会話に持ち込みたくない場合に使う。サブエージェントは自分専用のコンテキストウィンドウで作業し、要約だけをメイン会話に返す。

サブエージェントの定義ファイルは配置場所によって適用範囲（誰が使えるか）が変わる。優先順位は上から高い順（同名の場合、優先順位が高い方が使われる）。

Source: [sub-agents.md#choose-the-subagent-scope](https://code.claude.com/docs/en/sub-agents#choose-the-subagent-scope)

| 配置場所                          | 適用範囲               | 優先順位  | 作り方                         |
| :-------------------------------- | :--------------------- | :-------- | :----------------------------- |
| Managed settings                  | 組織全体               | 1（最高） | managed settingsとして配布     |
| `--agents` CLIフラグ              | 現在のセッションのみ   | 2         | 起動時にJSONで渡す             |
| `.claude/agents/`                 | 現在のプロジェクト     | 3         | Claudeに頼む、または手動作成   |
| `~/.claude/agents/`               | 自分の全プロジェクト   | 4         | Claudeに頼む、または手動作成   |
| プラグインの`agents/`ディレクトリ | プラグインが有効な範囲 | 5（最低） | プラグインのインストールで導入 |

補足:

- `.md`でも`.agent.md`でも構わない
- プロジェクト用・ユーザー用ともに`agents/`配下は再帰的にスキャンされるため、`agents/review/`のようにサブフォルダに整理してもよい。識別は`name`フロントマターのみで行われ、サブフォルダのパス自体は識別に影響しない
- プロジェクト用サブエージェントは、カレントディレクトリからリポジトリルームに向かって遡る途中にある全ての`.claude/agents/`が対象になる。同名定義が複数ある場合は、作業ディレクトリに近い方が優先される（v2.1.178以降）
- `--add-dir`で追加したディレクトリの`.claude/agents/`もあわせて読み込まれる
- プラグインの場合のみ、サブフォルダがスコープ付き識別子の一部になる（例: `agents/review/security.md`が`my-plugin:review:security`として登録される）
- 同一スコープ内で`name`が重複すると片方しか読み込まれない。`/doctor`実行で同スコープの重複エージェント名を検出できる（v2.1.196以降）
- v2.1.198以降、`/agents`は対話式作成ウィザードを開かなくなり、Claudeに頼むか`.claude/agents/`を直接編集するよう促すメッセージを表示するだけになった（v2.1.197以前は「Running」「Library」タブを持つウィザードが開く）
- ディスク上のファイルを追加・編集すると数秒以内に検知され、次回委譲時から反映される（再起動不要）。ただし「セッション開始時に存在しなかった、そのスコープ最初のagentsディレクトリ」を新規作成した場合と、`--disable-slash-commands`で起動したセッションは、いずれも監視対象外なので再起動が必要

## 似ているが2種類のコマンドがある

```shell
# subagentを指定
--agent <agent>  Specify an agent for the current session (overrides the 'agent' setting)
# subagentを動的に定義
--agents <json>  Define custom subagents dynamically via JSON. Uses the same field names as
                 subagent frontmatter, plus a 'prompt' field for the agent's instructions
```

```shell
claude --agent <agent-name>
claude --agents '{
  "translator": {
    "description": "テスト",
    "prompt": "あなたは、プロの翻訳家で、英語を日本語に、日本語を英語に翻訳します。",
    "tools": ["Read", "Grep", "Glob", "Bash"],
    "model": "haiku"
  }
}'
```

- `--agents`は、ファイルベースのサブエージェントと同じフロントマターフィールド（`description`, `tools`, `disallowedTools`, `model`, `permissionMode`, `mcpServers`, `hooks`, `maxTurns`, `skills`, `initialPrompt`, `memory`, `effort`, `background`, `isolation`, `color`）に加えて、システムプロンプトに相当する`prompt`フィールドを受け付ける
- `--agent`をプロジェクトの`.claude/settings.json`の`agent`設定として恒久化することも可能。CLIフラグは設定より優先される
- セッション全体を特定のサブエージェント定義で走らせたい場合（メインスレッド自体をそのサブエージェントにする）に`--agent`を使う。詳細は後述の「明示的な呼び出し方」を参照

## 組み込み（built-in）サブエージェント

Claude Codeには、自分で定義しなくても最初から使える組み込みサブエージェントが存在する。Claudeが状況に応じて自動的に委譲（delegate）する。各サブエージェントは、メイン会話の権限を継承しつつ追加のツール制限を持つ。

参考: https://code.claude.com/docs/en/sub-agents （「Built-in subagents」セクション）

| 名前                | モデル                                                               | 利用ツール                       | 役割                                                                 |
| :------------------ | :------------------------------------------------------------------- | :------------------------------- | :------------------------------------------------------------------- |
| `Explore`           | メインの会話から継承（Claude API上ではOpus上限）。v2.1.198以降の挙動 | 読み取り専用（Write/Editは不可） | コードベースの検索・調査に特化した高速な読み取り専用エージェント     |
| `Plan`              | メインの会話から継承                                                 | 読み取り専用（Write/Editは不可） | Plan Mode中に、計画提示前の下調べを行う調査エージェント              |
| `general-purpose`   | メインの会話から継承                                                 | 全ツール                         | 調査と実際の変更（編集など）の両方が必要な、複雑・多段階のタスク向け |
| `statusline-setup`  | Sonnet                                                               | -                                | `/statusline` 実行時にステータスラインを設定するために使われる       |
| `claude-code-guide` | Haiku                                                                | -                                | Claude Codeの機能についての質問をしたときに使われる                  |

### 補足

- `Explore`と`Plan`は、CLAUDE.mdファイルやメイン会話のgitステータスを読み込まない（調査を高速・低コストに保つため）。それ以外の組み込み・カスタムサブエージェントは両方を読み込む（[フォーク](#会話をフォークする-fork)を除く）。
- `Explore`という名前で自分のプロジェクト/ユーザー用サブエージェントを定義すると、組み込みの`Explore`を上書きできる（例: `model: haiku`を指定して低コストに固定するなど）。
- `Explore`・`Plan`は一度きり（one-shot）の実行で、エージェントIDを返さないため、後から`SendMessage`で再開（resume）することはできない。継続して作業させたい場合は`general-purpose`かカスタムサブエージェントを使う。
- 特定の組み込みサブエージェントを無効化したい場合は、`settings.json`の`permissions.deny`に`Agent(Explore)`のような形式で追加する。`--disallowedTools`CLIフラグでも同様のことができる（例: `claude --disallowedTools "Agent(Explore)"`）。
- `Explore`・`Plan`のみをまとめて無効化したい場合は環境変数`CLAUDE_CODE_DISABLE_EXPLORE_PLAN_AGENTS=1`を設定する（Claude Codeが直接ファイルを読み書き・調査するようになる。v2.1.198以降）。
- 非対話モード（headless）やAgent SDKで、組み込みサブエージェント自体をすべて取り除いて自前のものだけを使いたい場合は`CLAUDE_AGENT_SDK_DISABLE_BUILTIN_AGENTS=1`を設定する。
- サブエージェント自体を一切使わせたくない場合は、`Agent`ツール自体を`permissions.deny`で拒否する。

## サブエージェントの設定ファイルの書き方

```markdown
---
name: サブエージェントの名前
description: サブエージェントが呼ばれるべき状況の説明
tools: tool1, tool2, tool3 # Optional - 特に指定されない場合は全てのツールが利用されます
model: sonnet # Optional - モデルのエイリアスまたは 'inherit' を指定して親エージェントと同じモデルを使うことも可能です
---

サブエージェントへのプロンプトをここに記述します。
```

フロントマター（YAML）がサブエージェントのメタデータ・設定を定義し、本文（Markdown）がそのままシステムプロンプトになる。サブエージェントが受け取るのは、このシステムプロンプトと作業ディレクトリなどの基本的な環境情報のみで、Claude Codeのフル版システムプロンプトは受け取らない。

### フロントマターの全フィールド一覧

Source: [sub-agents.md#supported-frontmatter-fields](https://code.claude.com/docs/en/sub-agents#supported-frontmatter-fields)

必須なのは`name`と`description`のみ。

| フィールド        | 必須 | 説明                                                                                                                                                                                                                                                                                                      |
| :---------------- | :--- | :-------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `name`            | 必須 | 小文字英数字とハイフンで構成される一意な識別子。[フック](#補足-2)は`agent_type`としてこの値を受け取る。ファイル名と一致している必要はない                                                                                                                                                                 |
| `description`     | 必須 | Claudeがこのサブエージェントに委譲すべき状況の説明                                                                                                                                                                                                                                                        |
| `tools`           | 任意 | 利用可能な[ツール](#ツールアクセスの制御)。省略時は全ツールを継承。スキルを事前ロードしたい場合は`Skill`を並べるのではなく`skills`フィールドを使う                                                                                                                                                        |
| `disallowedTools` | 任意 | 継承・指定されたリストから除外するツール                                                                                                                                                                                                                                                                  |
| `model`           | 任意 | 使用モデル: `sonnet`, `opus`, `haiku`, `fable`、または`claude-opus-4-8`のようなフルモデルID、`inherit`。省略時は`inherit`                                                                                                                                                                                 |
| `permissionMode`  | 任意 | `default`, `acceptEdits`, `auto`, `dontAsk`, `bypassPermissions`, `plan`, `manual`（`default`のエイリアス、v2.1.200以降）。プラグイン提供のサブエージェントでは無視される                                                                                                                                 |
| `maxTurns`        | 任意 | サブエージェントが停止するまでの最大ターン数                                                                                                                                                                                                                                                              |
| `skills`          | 任意 | 起動時にこのサブエージェントのコンテキストへ事前ロードするスキル（説明文だけでなく本体全文が注入される）。ここに列挙しなくても、プロジェクト/ユーザー/プラグインのスキルは`Skill`ツール経由で実行時に呼び出せる                                                                                           |
| `mcpServers`      | 任意 | このサブエージェントで使える[MCPサーバー](https://code.claude.com/docs/en/mcp)。既存サーバー名の参照、またはインライン定義。プラグイン提供のサブエージェントでは無視される                                                                                                                                |
| `hooks`           | 任意 | このサブエージェントに紐づく[ライフサイクルフック](#補足-2)。プラグイン提供のサブエージェントでは無視される                                                                                                                                                                                               |
| `memory`          | 任意 | [永続メモリ](#永続メモリ-memory)のスコープ: `user`, `project`, `local`                                                                                                                                                                                                                                    |
| `background`      | 任意 | `true`にすると、Claudeが結果をすぐ必要とする場合でも常に[バックグラウンドタスク](#フォアグラウンドバックグラウンド実行)として実行する。省略時はClaudeが判断（v2.1.198以降はデフォルトでバックグラウンド実行）                                                                                             |
| `effort`          | 任意 | このサブエージェント有効時のeffortレベル(`low`/`medium`/`high`/`xhigh`/`max`)。省略時はセッションの設定を継承                                                                                                                                                                                             |
| `isolation`       | 任意 | `worktree`を指定すると、一時的な[git worktree](https://code.claude.com/docs/en/worktrees)（既定では親セッションのHEADではなく[デフォルトブランチ](https://code.claude.com/docs/en/worktrees#choose-the-base-branch)から分岐）で実行される。サブエージェントが変更を加えなければ自動でクリーンアップされる |
| `color`           | 任意 | タスク一覧・トランスクリプト上の表示色: `red`, `blue`, `green`, `yellow`, `purple`, `orange`, `pink`, `cyan`                                                                                                                                                                                              |
| `initialPrompt`   | 任意 | このエージェントが`--agent`や`agent`設定でメインセッションとして実行された場合に、最初のユーザーターンとして自動送信される内容。[コマンド](https://code.claude.com/docs/en/commands)・[スキル](https://code.claude.com/docs/en/skills)呼び出しも処理され、ユーザー入力があればその前に付加される          |

### モデルの選び方

`model`フィールドの解決順序（優先度が高い順）:

1. 環境変数`CLAUDE_CODE_SUBAGENT_MODEL`（エイリアスまたはモデルID指定時）
2. Claudeが委譲時に渡す、呼び出しごとの`model`パラメータ
3. サブエージェント定義の`model`フロントマター
4. メイン会話のモデル

v2.1.196以降、`CLAUDE_CODE_SUBAGENT_MODEL=inherit`は未設定時と同じ扱いになり、以降の解決（呼び出しごとのパラメータ→フロントマター）が続行される（それ以前のバージョンでは`inherit`が強制的にメイン会話のモデルへ固定していた）。
組織の[`availableModels`](https://code.claude.com/docs/en/model-config#restrict-model-selection)許可リストに反する値は、その値だけスキップされ継承モデルにフォールバックする。
v2.1.198以降、サブエージェントはメイン会話の拡張思考（extended thinking）設定もそのまま継承する（サブエージェント個別のON/OFF設定はない）。

### ツールアクセスの制御

`tools`（許可リスト）または`disallowedTools`（拒否リスト）でツールを制限する。両方指定した場合は`disallowedTools`が先に適用され、残ったプールに対して`tools`が解決される（両方に同じツールがあれば除外される）。

```yaml
---
name: safe-researcher
description: Research agent with restricted capabilities
tools: Read, Grep, Glob, Bash
---
```

```yaml
---
name: no-writes
description: Inherits every tool except file writes
disallowedTools: Write, Edit
---
```

MCPサーバー単位のパターンも使える: `mcp__<server>`または`mcp__<server>__*`でそのサーバーの全ツールを許可/除外。`disallowedTools`では`mcp__*`で全MCPツールを除外できる。

以下は、メイン会話のUI・セッション状態に依存するため、`tools`に書いても常にサブエージェントからは使えないツール:

- `AskUserQuestion`
- `EnterPlanMode`
- `ExitPlanMode`（`permissionMode: plan`の場合を除く）
- `ScheduleWakeup`
- `WaitForMcpServers`

サブエージェントが**さらに他のサブエージェントを起動できるか**は`tools`に`Agent`を含めるかどうかで決まる（[入れ子のサブエージェント](#入れ子のサブエージェント)を参照）。`claude --agent`でメインスレッドとして動く場合に限り、`Agent(worker, researcher)`のように括弧内で起動できるサブエージェント種別を許可リスト化できる（サブエージェント定義内での`tools: Agent(...)`は括弧内が無視される）。

### 永続メモリ（memory）

`memory`フィールドを設定すると、会話をまたいで保持されるディレクトリがサブエージェントに与えられ、コードベースのパターンやデバッグの知見などを蓄積できる。

| スコープ  | 保存先                                         | 用途                                                                 |
| :-------- | :--------------------------------------------- | :------------------------------------------------------------------- |
| `user`    | `~/.claude/agent-memory/<エージェント名>/`     | 全プロジェクト横断で記憶したい場合                                   |
| `project` | `.claude/agent-memory/<エージェント名>/`       | プロジェクト固有かつバージョン管理で共有したい場合（推奨デフォルト） |
| `local`   | `.claude/agent-memory-local/<エージェント名>/` | プロジェクト固有だがバージョン管理には含めたくない場合               |

有効化すると、システムプロンプトにメモリ運用の指示と、`MEMORY.md`の先頭200行（または25KBのいずれか小さい方）が自動的に含まれ、Read/Write/Editツールも自動で有効になる。

### 補足（フックによる細かい制御）

`PreToolUse`等の[フック](https://code.claude.com/docs/en/hooks)をサブエージェントのフロントマターに直接定義すると、そのサブエージェントが有効な間だけ動作し、終了時に自動的にクリーンアップされる。よく使うイベント: `PreToolUse`（ツール使用前）, `PostToolUse`（ツール使用後）, `Stop`（サブエージェント終了時。実行時には`SubagentStop`に変換される）。

```yaml
---
name: db-reader
description: Execute read-only database queries
tools: Bash
hooks:
  PreToolUse:
    - matcher: "Bash"
      hooks:
        - type: command
          command: "./scripts/validate-readonly-query.sh"
---
```

逆に、メインセッション側の`settings.json`で`SubagentStart`/`SubagentStop`イベントを使うと、サブエージェントのライフサイクルに応じた処理をプロジェクト共通で定義できる（マッチャーはエージェント種別名）。

## 明示的な呼び出し方

自動委譲では不十分な場合、以下の3パターンで明示的に呼び出せる（一回限りの提案→セッション全体のデフォルトへとエスカレートする）。

Source: [sub-agents.md#invoke-subagents-explicitly](https://code.claude.com/docs/en/sub-agents#invoke-subagents-explicitly)

| 方法           | 効果                                                                                                                                                                   |
| :------------- | :--------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| 自然言語       | プロンプト中でサブエージェント名を挙げる。委譲するかはClaude次第                                                                                                       |
| `@`メンション  | `@`を打って候補から選ぶ（ファイルの@メンションと同様）。その1タスクは確実にそのサブエージェントで実行される                                                            |
| セッション全体 | `--agent <name>`フラグ、または`.claude/settings.json`の`agent`設定で、メインスレッド自体をそのサブエージェント定義（システムプロンプト・ツール制限・モデル）で走らせる |

- `@`メンションは`@agent-<name>`と手打ちでも指定できる。プラグイン提供のサブエージェントは`@agent-my-plugin:code-reviewer`のようにスコープ付き名になる
- `--agent`で起動すると、サブエージェントのシステムプロンプトが既定のClaude Codeシステムプロンプトを完全に置き換える（`--system-prompt`と同様）。CLAUDE.mdやプロジェクトメモリは通常通りロードされる
- `--agent`はCLIフラグが`settings.json`の`agent`設定より優先される

## フォアグラウンド／バックグラウンド実行

- **フォアグラウンド**: 完了するまでメイン会話をブロックする。権限確認プロンプトはそのままユーザーに渡される
- **バックグラウンド**: メイン会話と並行して動く。v2.1.186以降、権限確認が必要な場面ではメインセッションにプロンプトが表示され（サブエージェント名付き）、承認すれば続行、Escでその1回だけ拒否できる（それ以前は自動拒否だった）
- v2.1.198以降、サブエージェントはデフォルトでバックグラウンド実行になる（結果がすぐ必要な場合はClaudeがフォアグラウンドを選ぶ）
- バックグラウンドのサブエージェントはフォアグラウンドより組み込みツールセットが狭い（フォーク実行は例外）。`AskUserQuestion`・`EnterPlanMode`・`ExitPlanMode`（`permissionMode: plan`のサブエージェントを除く）・`ScheduleWakeup`・`TaskOutput`などが使えない。`tools`にこれらを列挙すると、そのエージェントがバックグラウンド実行される限り「サブエージェントで利用不可」として弾かれる
- `Ctrl+B`で実行中のタスクをバックグラウンドに送れる
- `CLAUDE_CODE_DISABLE_BACKGROUND_TASKS=1`でバックグラウンド機能自体を無効化できる

## 入れ子のサブエージェント

v2.1.172以降、サブエージェントはさらに自分のサブエージェントを起動できる（例: レビュー担当のサブエージェントが、指摘事項ごとに検証用サブエージェントを分岐させる）。中間の出力はメイン会話に届かず、最上位のサブエージェントの要約だけが返る。

- 深さ（depth）はメイン会話から数えたサブエージェント段数。デフォルトはメイン会話から3層まで（v2.1.219以降）。上限に達したエージェントには`Agent`ツールが渡されず、それ以上は起動できない。`CLAUDE_CODE_MAX_SUBAGENT_SPAWN_DEPTH`で層数を変更でき、`1`を指定するとネスト自体を無効化できる
  - デフォルト値の変遷: v2.1.172〜v2.1.216は5層固定（変更不可）、v2.1.217〜v2.1.218は1層（ネスト不可）、v2.1.219で3層に変更
- v2.1.187以降、バックグラウンドのサブエージェントのdepthは最初に起動された時点で固定され、後から`resume`しても変わらない
- v2.1.217以降、セッション内で同時に走っているサブエージェントが既定20に達すると、それ以上の起動は`Concurrent subagent limit reached`で失敗する（`CLAUDE_CODE_MAX_CONCURRENT_SUBAGENTS`で変更可）。ultracode有効時はこの上限は適用されない
- 特定のサブエージェントに入れ子起動をさせたくない場合は、`tools`から`Agent`を外すか`disallowedTools`に追加する
- [フォーク](#会話をフォークする-fork)はさらに別のフォークを起動できない（他の種別のサブエージェントは起動可能で、depth上限には通常通りカウントされる）

## サブエージェントの再開（resume）

サブエージェントの各呼び出しは常に新しいインスタンス・新しいコンテキストで開始される。作業を継続したい場合は、Claudeに「再開して」と頼む。

- 完了時にClaudeはエージェントIDを受け取る。組み込みの`Explore`・`Plan`はone-shotでエージェントIDを返さないため再開不可（`general-purpose`かカスタムサブエージェントを使う）
- 再開には`SendMessage`ツールを使い、`to`フィールドにエージェントのIDまたは名前を指定する（`SendMessage`自体はagent teams機能を必要としない）
- v2.1.199以降、`SendMessage`は名前が「会話内で以前に到達したのと同じエージェントを指しているか」をチェックする。名前が再利用（再起動されたバックグラウンドエージェント等）されていた場合は送信を拒否し、現在その名前が指す先を報告する。このチェックは会話単位で、`/clear`でリセットされる
- トランスクリプトは`~/.claude/projects/{project}/{sessionId}/subagents/agent-{agentId}.jsonl`に保存され、メイン会話の圧縮（compaction）とは独立して保持される。クリーンアップは`cleanupPeriodDays`設定（デフォルト30日）に従う

## 会話をフォークする（fork）

フォークは、新規に始まるのではなく**会話全体をそのまま引き継ぐ**特殊なサブエージェント。システムプロンプト・ツール・モデル・メッセージ履歴がメインセッションと同一のため、背景説明なしに横道のタスクを任せられる。ツール呼び出し自体はメイン会話に出てこず、最終結果だけが返る点は通常のサブエージェントと同じ。

- v2.1.117以降が必要。v2.1.161以降は`/fork`コマンドがデフォルトで有効（それ以前は環境変数`CLAUDE_CODE_FORK_SUBAGENT=1`が必要）。Claude自身にフォークを起動させる機能は実験的
- `CLAUDE_CODE_FORK_SUBAGENT=1`で明示的に有効化、`0`で無効化（サーバー側の段階的ロールアウトより優先される）
- `/fork <指示>`で自分から開始できる。バックグラウンドで動き、完了するとメイン会話にメッセージとして結果が届く
- フォークはシステムプロンプト・ツール定義がメインと同一なため、最初のリクエストが親のプロンプトキャッシュを再利用でき、通常のサブエージェント起動よりコストが安くなりやすい
- Claudeが`Agent`ツール経由でフォークを起動する際、`isolation: "worktree"`を指定すればファイル変更を別のgit worktreeに書き込める
- フォークはさらに別のフォークを起動できない

| 比較項目                   | フォーク                 | 名前付きサブエージェント                       |
| :------------------------- | :----------------------- | :--------------------------------------------- |
| コンテキスト               | 会話履歴全体             | 渡されたプロンプトのみの新規コンテキスト       |
| システムプロンプト・ツール | メインセッションと同一   | サブエージェント定義ファイルに基づく           |
| モデル                     | メインセッションと同一   | 定義の`model`フィールドに基づく                |
| 権限                       | ターミナルにそのまま表示 | バックグラウンド実行中はメインセッションに表示 |
| プロンプトキャッシュ       | メインセッションと共有   | 別キャッシュ                                   |

## コンテキストに何がロードされるか

各サブエージェント（フォークを除く）は、以下を初期コンテキストとして開始する:

- **システムプロンプト**: エージェント自身のプロンプト＋Claude Codeが付加する環境情報（フル版システムプロンプトではない）
- **タスクメッセージ**: Claudeが委譲時に書く指示文
- **CLAUDE.mdとメモリ**: メイン会話がロードする[メモリ階層](https://code.claude.com/docs/en/memory)（`~/.claude/CLAUDE.md`、プロジェクトルール、`CLAUDE.local.md`、managedポリシー等）を全レベル分。`Explore`・`Plan`はこれをスキップする
- **Gitステータス**: 親セッション開始時点のスナップショット。Gitリポジトリでない場合や`includeGitInstructions: false`の場合は含まれない。`Explore`・`Plan`は常にスキップ
- **事前ロードされたスキル**: フロントマターの`skills`で指定したスキルの全文。組み込みエージェントはスキルを事前ロードしない

`Explore`・`Plan`だけがCLAUDE.mdとGitステータスを省略する。この挙動を変えるフロントマターや個別設定は存在しない。

## API エラー時の挙動

v2.1.199以降、使用量上限や繰り返しのサーバーエラーなどAPIエラーでサブエージェントの実行が終了した場合、その失敗はサブエージェントの成果物としてではなく失敗としてClaudeに報告される。

- **フォアグラウンド**: 一部テキスト出力済みで打ち切られた場合は、その部分出力と「打ち切られた」旨の注記が返る。何も出力していない（ツール呼び出しのみだった）場合は`Agent terminated early due to an API error`で失敗する
- **バックグラウンド**: サブエージェントは失敗としてマークされ、Claudeに届くメッセージにAPIエラー内容と最後の出力が含まれる（部分的な作業が失われない）

## 無効化する方法

`settings.json`の`permissions.deny`に`Agent(サブエージェント名)`形式で追加すると、組み込み・カスタム問わず特定のサブエージェントを禁止できる。

```json
{
  "permissions": {
    "deny": ["Agent(Explore)", "Agent(my-custom-agent)"]
  }
}
```

`--disallowedTools`CLIフラグでも同様のことができる:

```bash
claude --disallowedTools "Agent(Explore)"
```

## サンプル

コードレビュー担当（読み取り専用、Write/Editなし）:

```markdown
---
name: code-reviewer
description: Expert code review specialist. Proactively reviews code for quality, security, and maintainability. Use immediately after writing or modifying code.
tools: Read, Grep, Glob, Bash
model: inherit
---

You are a senior code reviewer ensuring high standards of code quality and security.

When invoked:

1. Run git diff to see recent changes
2. Focus on modified files
3. Begin review immediately

Provide feedback organized by priority: critical issues, warnings, suggestions.
```

デバッガー（修正まで行うためEditを含む）:

```markdown
---
name: debugger
description: Debugging specialist for errors, test failures, and unexpected behavior. Use proactively when encountering any issues.
tools: Read, Edit, Bash, Grep, Glob
---

You are an expert debugger specializing in root cause analysis.

When invoked:

1. Capture error message and stack trace
2. Identify reproduction steps
3. Isolate the failure location
4. Implement minimal fix
5. Verify solution works

Focus on fixing the underlying issue, not the symptoms.
```

ベストプラクティス（公式ドキュメントより）:

- 各サブエージェントは1つの役割に特化させる
- `description`は具体的に書く（Claudeの自動委譲判断に直結する）
- 必要最小限のツールだけを許可する
- プロジェクトサブエージェントはバージョン管理にコミットし、チームで共有・改善する

## 参考文献

- サブエージェントの作成・設定・呼び出し方全般（本記事の主な情報源）: https://code.claude.com/docs/en/sub-agents
- `--agent`/`--agents`を含むCLIフラグ一覧: https://code.claude.com/docs/en/cli-reference
- 環境変数（`CLAUDE_CODE_DISABLE_EXPLORE_PLAN_AGENTS`等）: https://code.claude.com/docs/en/env-vars
- フック全般: https://code.claude.com/docs/en/hooks
- 権限設定（`permissions.deny`等）: https://code.claude.com/docs/en/permissions
