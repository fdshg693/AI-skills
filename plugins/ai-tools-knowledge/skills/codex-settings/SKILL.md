---
name: codex-settings
description: Use when adding or editing OpenAI Codex configuration files — `~/.codex/config.toml`, project-scoped `.codex/config.toml`, profile files (`$CODEX_HOME/<profile>.config.toml`), `rules/*.rules` (execpolicy), hooks (`features.hooks` + `hooks.json` or inline `[hooks]`), `mcp_servers` entries, sandbox/approval-policy/permission-profile settings, or `requirements.toml`. Covers scope precedence, keys project-scoped config can't override, TOML structure, and a pre-flight checklist. Do not use this skill to answer general Codex specification questions (use codex-docs), CLI flags (use codex-cli-docs), or to author or debug AGENTS.md discovery / memories behavior (use codex-memory).
meta:
  tag: []
  requires_repo_tools: none
  requires_env: none
  dependencies: none
  requires_install: none
  requires_hooks: none
  requires_skills: codex-docs, codex-cli-docs, codex-hooks, codex-memory, codex-skill-authoring
  status: stable
  description: no description
  version: 1.0.5
---

# Codex設定ファイルの編集

`config.toml`（および関連する `rules/*.rules`、hooks、環境変数）を編集する際の**手順とチェックリスト**をまとめる。キー一覧・スコープと優先順位・sandbox/approval/permissionsの構造など詳細リファレンスは同梱の [config-reference.md](references/config-reference.md) を参照。

## 対象ファイル

- `~/.codex/config.toml` — ユーザーレベル設定
- `.codex/config.toml` — プロジェクトスコープの上書き（信頼したプロジェクトでのみ読み込まれる）
- `$CODEX_HOME/<profile-name>.config.toml` — `--profile` で選択するプロファイル層（トップレベルキーをそのまま書く。`[profiles.xxx]` でネストしない）
- `~/.codex/rules/*.rules` / `<repo>/.codex/rules/*.rules` — サンドボックス外で実行してよいコマンドを制御する execpolicy ルール（Starlarkの`prefix_rule`）
- `hooks.json`（または `config.toml` の `[hooks]` テーブル）— ライフサイクルフック。`features.hooks = true` が前提
- `requirements.toml` — 管理者が強制する制約（通常は編集対象外。存在に気づいたら触らずユーザーに確認する）

AGENTS.md（プロジェクト向け指示ファイル）の中身を書く作業、およびdiscovery挙動・memories機能の詳細は**codex-memoryスキル**を使う（このスキルの対象外）。

## 編集手順

1. **スコープを決める** — 個人の既定値は `~/.codex/config.toml`、このプロジェクトだけに効かせたいなら `.codex/config.toml`（信頼済みプロジェクトのみ有効）、コマンドごとに切り替えたい設定はプロファイルファイルへ。優先順位は「CLIフラグ/`--config` > プロジェクトconfig（ルートから近い方が勝つ）> プロファイル > ユーザーconfig > システムconfig > 組み込みデフォルト」。判断に迷ったら config-reference.md の「スコープと優先順位」を確認する。
2. **プロジェクトスコープで書けないキーを確認する** — `openai_base_url` / `chatgpt_base_url` / `apps_mcp_product_sku` / `model_provider` / `model_providers` / `notify` / `profile` / `profiles` / `experimental_realtime_ws_base_url` / `otel` はプロジェクトの `.codex/config.toml` に書いても無視される。これらはユーザーレベルに置く。
3. **既存ファイルを読んでからTOMLとして壊さないように編集する** — 新規なら作成、既存なら該当テーブル（`[mcp_servers.<id>]`、`[sandbox_workspace_write]`、`[shell_environment_policy]` など）をマージする形で編集する。
4. **キーを確認する** — config-reference.md の表に無いキーを使う場合、学習データが古い可能性があるため **codex-docsスキル** で公式ドキュメント（Configuration Referenceページ）または `https://developers.openai.com/codex/config-schema.json` を確認してから使う。
5. **サンドボックス・承認ポリシーを変更する場合** — `sandbox_mode`（`read-only` / `workspace-write` / `danger-full-access`）と `approval_policy`（`untrusted` / `on-request` / `never` / `{granular=...}`）の組み合わせ、または `default_permissions`（`:read-only` / `:workspace` / `:danger-full-access` / カスタム `[permissions.<name>]`）のどちらの仕組みを使うか決める。**両方を同時に設定しない**（`default_permissions` と `sandbox_mode`/`[sandbox_workspace_write]` は併用不可）。`danger-full-access` や `approval_policy = "never"` への変更は、意図をユーザーに確認する。
6. **mcp_serversを追加する場合** — stdio（`command`/`args`/`env`/`cwd`）か HTTP（`url`/`bearer_token_env_var`/`http_headers`）かを決め、必要なら `enabled_tools`/`disabled_tools` で公開ツールを絞る。トークンは `bearer_token_env_var` 経由にし、値を直書きしない。
7. **hooksを追加する場合** — `features.hooks = true` を確認し、イベント名（`PreToolUse` / `PermissionRequest` / `PostToolUse` / `PreCompact` / `PostCompact` / `SessionStart` / `SessionEnd` / `SubagentStart` / `SubagentStop` / `UserPromptSubmit` / `Stop`）ごとにマッチャーとコマンドを定義する。Windows専用コマンドは `commandWindows`（TOMLキーは `command_windows`）を使う。イベントごとの入出力コントラクト・matcherの評価対象・信頼レビュー（`/hooks`）・非同期hookの制約など、hooksの中身を詳しく書く／レビューする場合は**codex-hooksスキル**を使う。**Claude Code用のwriting-hooksスキルの構文をそのまま流用しない**（イベント名・スキーマが異なる）。
8. **コマンド実行ルールを追加・変更する場合** — `~/.codex/rules/default.rules` またはプロジェクトの `.codex/rules/*.rules` に `prefix_rule(pattern=..., decision="allow"|"prompt"|"forbidden", justification=..., match=..., not_match=...)` を書く。複数ルールが一致する場合は最も制限の強い決定（`forbidden` > `prompt` > `allow`）が優先される。編集後は `codex execpolicy check --pretty --rules <file> -- <command...>` で検証する。
9. **秘密情報を扱う場合** — APIキー・トークンはTOMLに直書きせず、`env_key`（プロバイダ）、`bearer_token_env_var`（MCP）、`model_providers.<id>.auth.command`（コマンド経由取得）などの環境変数/コマンド参照を使う。
10. **TOMLとして妥当か確認する** — 構文エラーがあると該当ファイルの読み込みに失敗する。可能なら `#:schema https://developers.openai.com/codex/config-schema.json` を先頭に置いてエディタ補完・診断を効かせる。
11. **反映タイミングを伝える** — 多くの設定はセッション開始時に読み込まれるため、実行中セッションでの編集は次回起動（またはプロファイル指定など該当コマンドの再実行）まで反映されないことが多い。ユーザーに再起動が必要か伝える。

## チェックリスト

- [ ] 個人設定かチーム/プロジェクト共有設定かを区別し、正しいスコープ（user/project/profile）に書いているか確認する
- [ ] プロジェクトスコープで無視されるキー一覧に該当していないか確認する
- [ ] 信頼していないプロジェクトでは `.codex/` 配下のconfig・hooks・rulesがまるごとスキップされることを踏まえて説明する（`projects.<path>.trust_level`）
- [ ] `default_permissions` と `sandbox_mode`/`[sandbox_workspace_write]` を同時に設定していないか確認する
- [ ] サンドボックス・承認ポリシー・hooks・rulesなどセキュリティに関わる設定は、変更前にユーザーに意図を確認する
- [ ] 秘密情報を`config.toml`や`hooks.json`に直書きしていないか確認する
- [ ] Windows環境（このマシン）向けにhooksやコマンドを書く場合、`commandWindows`やパス区切り・クオートに注意する
- [ ] `requirements.toml`（管理者強制設定）に触れる場合は、管理者権限の範囲であることをユーザーに確認する

## 困ったときは

1. まず同梱の [config-reference.md](references/config-reference.md)（対象ファイル一覧・スコープと優先順位・sandbox/approval/permissionsの構造・hooksイベント一覧・mcp_serversキー・rules/execpolicy・環境変数の抜粋）を確認する。
2. それでも解決しない、載っていないキーを使いたい、または仕様が変わっている可能性がある場合は **codex-docsスキル** で最新の公式ドキュメント（`developers.openai.com/codex`）を参照する。
3. CLIフラグ（`--config`、`--profile`、`codex execpolicy check` など）の詳細は **codex-cli-docsスキル** を使う。
4. hooksの中身（イベント別スキーマ・matcher・trust・非同期制約など）を詳しく扱う場合は **codex-hooksスキル** を使う。
5. Codex用スキル自体の作成・編集は **codex-skill-authoringスキル** を使う。
