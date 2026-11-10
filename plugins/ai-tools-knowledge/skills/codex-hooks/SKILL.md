---
name: codex-hooks
description: Use when creating, editing, reviewing, or debugging OpenAI Codex hooks (hooks.json, or inline [hooks] tables in config.toml) — choosing events (PreToolUse, PermissionRequest, PostToolUse, SessionStart, SessionEnd, UserPromptSubmit, Stop, SubagentStart/SubagentStop, PreCompact/PostCompact), writing matcher regexes, command vs mcp_tool handlers, the JSON input/output contract (permissionDecision, decision/reason, continue, additionalContext, hookSpecificOutput), exit codes, async/background hooks, hook trust review via `/hooks`, plugin-bundled hooks, and managed hooks in requirements.toml. Do not use this skill for general config.toml/mcp_servers/sandbox/rules settings beyond hooks (use codex-settings), CLI flags (use codex-cli-docs), general Codex specification questions (use codex-docs), or Claude Code hooks (use writing-hooks — event names and schema differ).
meta:
  tag: []
  requires_repo_tools: none
  requires_env: none
  dependencies: none
  requires_install: none
  requires_hooks: none
  requires_skills: codex-docs, codex-settings
  status: stable
  description: no description
  version: 1.0.1
---

# Codex Hooks作成のベストプラクティス

Codex Hooksは強力だが、信頼レビュー・イベントごとに異なる出力コントラクト・非同期hookの制約など事故りやすい点が多い。ここでは**実際に書く／レビューする際の手順とチェックリスト**をまとめる。イベント全種の詳細スキーマ・マッチャー評価ルール・全フィールド定義は同梱の [references/hooks.md](references/hooks.md) を参照。

設定ファイル自体の置き場所・スコープ優先順位（`~/.codex/config.toml` vs `.codex/config.toml`等）は **codex-settingsスキル** の管轄。このスキルはhooksの中身（イベント選定・入出力・matcher・trust）に特化する。

## 作成手順

1. **イベントを選ぶ** — いつ発火させたいか（`PreToolUse`でブロック／`PermissionRequest`で承認を肩代わり／`PostToolUse`で事後レビュー／`SessionStart`でコンテキスト注入／`Stop`でターン継続 等）。候補に迷ったら [references/hooks.md](references/hooks.md#イベント別の詳細) のイベント一覧を確認する。
2. **配置場所を決める** — 個人の全プロジェクト共通なら`~/.codex/hooks.json`か`~/.codex/config.toml`、このリポジトリだけなら`<repo>/.codex/hooks.json`か`<repo>/.codex/config.toml`。プロジェクトローカルなhookは**そのプロジェクトが信頼済みの場合のみ**読み込まれる点に注意。`hooks.json`とインライン`[hooks]`を同一レイヤーに混在させない（マージされ起動時警告になる）。
3. **matcherを絞る** — `matcher`が意味を持つイベントかどうかをまず確認する（`UserPromptSubmit`と`Stop`は非対応で、指定しても無視される）。対象は正規表現なので、完全一致させたいなら`^Bash$`のようにアンカーで囲む。
4. **ハンドラーのtypeを選ぶ** — 決定的な処理・スクリプトなら`command`。既に接続済みのMCPサーバーのツールを叩きたいなら`mcp_tool`（`${tool_input.xxx}`で引数展開できる）。`prompt`/`agent`は**現状パースされるだけで実行されない**ので使わない。
5. **入出力コントラクトをイベントに合わせて書く** — イベントによって「plain textが有効か」「JSONのどのフィールドに対応するか」「exit code 2が使えるか」が異なる（下記チェックリスト）。他イベント用の出力形式を流用しない。
6. **ローカルでテストしてからコミットする** — サンプルJSONを標準入力に流し、期待通りのexit code・stdout・stderrになるか手元で確認する。
7. **信頼レビューを通す** — CLIで`/hooks`を開き、追加・変更したhook定義をレビューして信頼する。信頼するまでそのhookはスキップされ続ける（警告は出るが実行はされない）。

## チェックリスト（ベストプラクティス）

- [ ] `matcher`が対応していないイベント（`UserPromptSubmit`・`Stop`）には書かない。無視されるだけで害はないが、絞り込めていると誤解しない
- [ ] `PreToolUse`/`PermissionRequest`は**そのイベント専用の出力形**（`hookSpecificOutput.permissionDecision`や`hookSpecificOutput.decision.behavior`）を使う。`continue`/`stopReason`/`suppressOutput`をこの2イベントで返すとhook実行が失敗扱いになり、ツール呼び出し自体は素通しされる
- [ ] `PostToolUse`の`decision: "block"`は**既に実行済みのBashコマンドを取り消さない**。ツール結果を差し替えてフィードバックするだけ。副作用を防ぎたいなら`PreToolUse`側でブロックする
- [ ] `SubagentStop`と`Stop`はexit `0`のとき**JSON出力が必須**（プレーンテキストは無効）。他イベント（`SessionStart`/`UserPromptSubmit`等）はプレーンテキストがそのままdeveloper contextとして採用されるので混同しない
- [ ] ブロック/継続したい場合、JSON出力の代わりに**exit code 2 + stderr**でも同等に実現できる（`PreToolUse`のdeny、`PostToolUse`のblock、`UserPromptSubmit`のblock、`Stop`/`SubagentStop`のcontinue等）。イベントごとの対応可否は[references/hooks.md](references/hooks.md)で確認する
- [ ] `PermissionRequest`では`updatedInput`・`updatedPermissions`・`interrupt`を返さない（予約フィールドで現状フェイルクローズ）。許可/拒否は`hookSpecificOutput.decision.behavior`のみで表現する
- [ ] 複数の`PreToolUse`/`PermissionRequest`が判断を返した場合、**`deny`が最優先**される。競合を狙って複数hookに判断を分散させない
- [ ] `async: true`は`command`ハンドラーのみ対応。バックグラウンドhookは**ブロック・承認・書き換えができない**ため、ツールポリシーや承認判断には使わない（ロギング・通知・後追いスキャンなど非制御用途に限定する）
- [ ] `SessionEnd`は`async`指定の有無にかかわらず常に同期実行され、MCP tool hookには対応しない。既定タイムアウトも他イベント（600秒）と異なり1秒（最大3秒）と短い
- [ ] hook出力（特に`additionalContext`）にシークレットや機微情報を含めない。閾値超過分はディスク（`<temp_dir>/hook_outputs/...`）にそのまま保存される（spilling）
- [ ] リポジトリローカルなscriptパスは`.codex/hooks/...`のような相対パスではなく、`$(git rev-parse --show-toplevel)`等でgitルートから解決する（Codexがサブディレクトリから起動されることがあるため）
- [ ] Windows向けコマンドは`commandWindows`（TOMLキー: `command_windows`）で上書きする。このマシン（Windows）向けにhookを書く場合は必ず動作確認する
- [ ] **Claude Code用の`writing-hooks`スキルの構文をそのまま流用しない**（イベント名・matcherの意味・出力フィールドの構造がCodexとは異なる）
- [ ] 追加・変更したhookは`/hooks`で信頼するまで実行されない。CI等の一度きりの自動化で信頼の永続化をスキップしたい場合のみ`--dangerously-bypass-hook-trust`を使う（ユーザーに意図を確認してから使う）
- [ ] managed hooks（`requirements.toml`由来）はユーザーが無効化できない。管理者権限の範囲であることを踏まえて扱う

## 困ったときは

1. まず同梱の [references/hooks.md](references/hooks.md)（イベント全種の詳細スキーマ・matcherパターン表・ツールカバレッジ・spilling・バックグラウンドhookの制約・managed/plugin hooksなど）を確認する。
2. `/hooks`でhookソースの一覧・信頼状態・レビュー待ちの有無を確認する。起動時の警告が消えない場合は、変更したhook定義が信頼済みになっているか確認する。
3. それでも解決しない、または仕様が変わっている可能性がある場合は **codex-docsスキル** で最新の公式ドキュメント（`developers.openai.com/codex/hooks`）を確認する。
4. `hooks.json`/`config.toml`の置き場所やスコープ優先順位で迷ったら **codex-settingsスキル** を使う。
