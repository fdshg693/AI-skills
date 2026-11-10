# Codex設定ファイル リファレンス

出典: [Config basics](https://developers.openai.com/codex/config-file/config-basic)、[Advanced Configuration](https://developers.openai.com/codex/config-file/config-advanced)、[Configuration Reference](https://developers.openai.com/codex/config-file/config-reference)、[Sample Configuration](https://developers.openai.com/codex/config-file/config-sample)、[Environment variables](https://developers.openai.com/codex/config-file/environment-variables)、[Agent approvals & security](https://developers.openai.com/codex/agent-approvals-security)、[Rules](https://developers.openai.com/codex/agent-configuration/rules)、[Hooks](https://developers.openai.com/codex/hooks)。最新仕様は変わる可能性があるため、キーの有無を最終確認する場合は codex-docsスキルで公式ドキュメントを引くこと。

## 対象ファイル一覧

| ファイル                                                                 | 役割                                                                                                                                                                |
| ------------------------------------------------------------------------ | ------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `~/.codex/config.toml`（`$CODEX_HOME/config.toml`）                      | ユーザーレベルの既定設定                                                                                                                                            |
| `.codex/config.toml`（プロジェクトルートから作業ディレクトリまで複数可） | プロジェクトスコープの上書き。信頼したプロジェクトでのみ読み込まれる                                                                                                |
| `$CODEX_HOME/<profile-name>.config.toml`                                 | `--profile <name>` で選択するプロファイル層。トップレベルキーをそのまま書く（`[profiles.name]` でネストしない）                                                     |
| `/etc/codex/config.toml`（Unix、存在する場合）                           | システムレベル設定                                                                                                                                                  |
| `~/.codex/rules/*.rules`、`<repo>/.codex/rules/*.rules`                  | execpolicy（`prefix_rule`）。サンドボックス外実行コマンドの許可/確認/禁止を制御                                                                                     |
| `hooks.json` または `config.toml` の `[hooks]` テーブル                  | ライフサイクルフック定義（`features.hooks = true` が前提）                                                                                                          |
| `requirements.toml`                                                      | 管理者が強制する制約（ローカルconfigで上書き不可なキーを制限）                                                                                                      |
| `AGENTS.md`                                                              | プロジェクト向け指示（このスキルの対象外。`model_instructions_file` で差し替え可、`project_doc_max_bytes`/`project_doc_fallback_filenames` で読み込み挙動を調整可） |

## スコープと優先順位

Codexは以下の順（上ほど優先）で値を解決する。

1. CLIフラグ・`-c`/`--config` の一時オーバーライド
2. プロジェクトconfig（`.codex/config.toml`。プロジェクトルートから現在の作業ディレクトリに向かって並び、近い方が勝つ。信頼済みプロジェクトのみ）
3. `--profile profile-name` で選んだプロファイルファイル（`~/.codex/profile-name.config.toml`）
4. ユーザーconfig（`~/.codex/config.toml`）
5. システムconfig（`/etc/codex/config.toml`、存在する場合）
6. 組み込みデフォルト

### プロジェクトスコープが上書きできないキー

次のキーは `.codex/config.toml`（プロジェクトローカル）に書いても無視される。マシンローカルなプロバイダ・認証・通知・プロファイル選択・テレメトリ経路に関わるため、ユーザーレベルに置く。

`openai_base_url` / `chatgpt_base_url` / `apps_mcp_product_sku` / `model_provider` / `model_providers` / `notify` / `profile` / `profiles` / `experimental_realtime_ws_base_url` / `otel`

### 信頼レベル

- `projects.<path>.trust_level = "trusted" | "untrusted"` — プロジェクト（またはworktree）の信頼状態を記録する。
- 未信頼のプロジェクトでは `.codex/` 配下のプロジェクトローカルレイヤー（config・hooks・rules）が**まるごとスキップ**される。ユーザー/システムレベルのconfig・hooks・rulesは引き続き読み込まれる。

## sandbox / approval / permissions

Codexのアクセス制御には2系統あり、**同時に設定しない**（`default_permissions` と `sandbox_mode`/`[sandbox_workspace_write]` は併用不可）。

### 従来方式（sandbox_mode + approval_policy）

| キー                                                                   | 値                                                        | 説明                                                                                                        |
| ---------------------------------------------------------------------- | --------------------------------------------------------- | ----------------------------------------------------------------------------------------------------------- |
| `sandbox_mode`                                                         | `read-only` / `workspace-write` / `danger-full-access`    | コマンド実行時のファイルシステム・ネットワークアクセス範囲                                                  |
| `sandbox_workspace_write.writable_roots`                               | `array<string>`                                           | `workspace-write` 時の追加書き込み可能ルート                                                                |
| `sandbox_workspace_write.network_access`                               | `boolean`                                                 | `workspace-write` サンドボックス内での外向きネットワークアクセス許可                                        |
| `sandbox_workspace_write.exclude_tmpdir_env_var` / `exclude_slash_tmp` | `boolean`                                                 | `$TMPDIR` / `/tmp` を書き込み可能ルートから除外                                                             |
| `approval_policy`                                                      | `untrusted` / `on-request` / `never` / `{granular={...}}` | コマンド実行前に承認を求めるタイミング。`on-failure` は非推奨（`on-request`か`never`を使う）                |
| `approval_policy.granular.*`                                           | `boolean`                                                 | `sandbox_approval` / `rules` / `mcp_elicitations` / `request_permissions` / `skill_approval` を個別にON/OFF |
| `approvals_reviewer`                                                   | `user` / `auto_review`                                    | `on-request`/granular時の承認を誰がレビューするか（既定 `user`）                                            |
| `windows.sandbox`                                                      | `unelevated` / `elevated`                                 | Windowsネイティブ実行時のサンドボックスモード（`elevated`推奨）                                             |
| `windows.sandbox_private_desktop`                                      | `boolean`                                                 | サンドボックス化した子プロセスを専用デスクトップで実行するか                                                |

### 新方式（named permission profiles、beta）

| キー                                                         | 値                                                                     | 説明                                                                                                             |
| ------------------------------------------------------------ | ---------------------------------------------------------------------- | ---------------------------------------------------------------------------------------------------------------- |
| `default_permissions`                                        | `":read-only"` / `":workspace"` / `":danger-full-access"` / カスタム名 | 適用する既定プロファイル名。組み込み以外はマッチする `[permissions.<name>]` が必要                               |
| `permissions.<name>.extends`                                 | `string`                                                               | 継承元プロファイル（`:read-only`/`:workspace`/他のカスタム名）。`:danger-full-access`・未定義・循環は不可        |
| `permissions.<name>.filesystem.<path-or-glob>`               | `"read" \| "write" \| "deny" \| table`                                 | パス・globごとのアクセス権                                                                                       |
| `permissions.<name>.filesystem.":workspace_roots".<subpath>` | `"read" \| "write" \| "deny"`                                          | 実行時ワークスペースルートからの相対パスで指定                                                                   |
| `permissions.<name>.network.enabled`                         | `boolean`                                                              | このプロファイルでネットワークを許可するか                                                                       |
| `permissions.<name>.network.domains.<pattern>`               | `allow \| deny`                                                        | ドメイン単位の許可/拒否（`*.example.com`＝サブドメインのみ、`**.example.com`＝apex＋サブドメイン、`deny`が優先） |

## mcp_servers

| キー                                                                          | 説明                                                                        |
| ----------------------------------------------------------------------------- | --------------------------------------------------------------------------- |
| `mcp_servers.<id>.command` / `args` / `env` / `cwd`                           | stdioサーバーの起動コマンド・引数・環境変数・作業ディレクトリ               |
| `mcp_servers.<id>.url` / `bearer_token_env_var` / `http_headers`              | streamable HTTPサーバーのエンドポイント・ベアラートークン参照・静的ヘッダー |
| `mcp_servers.<id>.enabled` / `required`                                       | 設定を残したまま無効化 / 起動失敗時にCodex全体を失敗させるか                |
| `mcp_servers.<id>.enabled_tools` / `disabled_tools`                           | 公開ツールの許可リスト／（許可リスト適用後の）拒否リスト                    |
| `mcp_servers.<id>.default_tools_approval_mode` / `tools.<tool>.approval_mode` | `auto` / `prompt` / `approve` をサーバー単位・ツール単位で設定              |
| `mcp_servers.<id>.startup_timeout_sec` / `tool_timeout_sec`                   | 起動タイムアウト（既定10秒）／ツール呼び出しタイムアウト（既定60秒）        |

秘密情報（トークン等）は `bearer_token_env_var` や `env_vars`（`source = "local" | "remote"`）経由にし、TOMLへ直書きしない。

## hooks

- 前提: `features.hooks = true`（`features.codex_hooks` は非推奨エイリアス）
- 定義場所: `hooks.json`、または `config.toml` 内の `[hooks]` テーブル（同じイベントスキーマ）
- 主なイベント: `PreToolUse` / `PermissionRequest` / `PostToolUse` / `PreCompact` / `PostCompact` / `SessionStart` / `SessionEnd` / `SubagentStart` / `SubagentStop` / `UserPromptSubmit` / `Stop`
- `hooks.<Event>[].hooks[]` にハンドラーを並べる。`command`と`mcp_tool`ハンドラーのみ実行され、prompt/agentハンドラーはパースされるが実行されない
- Windows専用コマンドは `commandWindows`（TOMLキー: `command_windows`）で上書きできる
- イベント別の入出力スキーマ・matcher評価・信頼レビュー（`/hooks`）・非同期hookの詳細は**codex-hooksスキル**を使う
- Claude Code用の`writing-hooks`スキルはイベント名・スキーマが異なるため、そのまま流用しない

## rules（execpolicy）

- 場所: `~/.codex/rules/*.rules`（ユーザー）、`<repo>/.codex/rules/*.rules`（プロジェクト。信頼済みのみ）。Team Config配下のrulesも起動時にスキャンされる
- 構文: Starlarkの `prefix_rule(pattern=[...], decision="allow"|"prompt"|"forbidden", justification="...", match=[...], not_match=[...])`
- `pattern` はコマンドの先頭引数列に対する完全一致プレフィックス（要素はリテラル文字列、または `["view","list"]` のような選択肢の合併も可）
- 複数ルールが一致する場合、最も制限の強い決定が優先される（`forbidden` > `prompt` > `allow`）
- `bash -lc "..."` のような複合コマンドは、安全に分割できる場合（`&&`/`||`/`;`/`|` でつながれた変数展開・リダイレクトなしの単純な単語列）は個別コマンドに分割して評価され、分割できない場合はスクリプト全体を1つのコマンドとして評価する
- 検証: `codex execpolicy check --pretty --rules <file> -- <command...>`
- 管理者は `requirements.toml` から制限的な `prefix_rule` を強制できる

## shell_environment_policy

| キー                                               | 説明                                                             |
| -------------------------------------------------- | ---------------------------------------------------------------- |
| `shell_environment_policy.inherit`                 | `all` / `core` / `none` — サブプロセス起動時の環境変数継承レベル |
| `shell_environment_policy.ignore_default_excludes` | `KEY`/`SECRET`/`TOKEN` を含む変数を既定除外より先に残すか        |
| `shell_environment_policy.exclude`                 | 除外するglobパターンの配列                                       |
| `shell_environment_policy.include_only`            | 設定時はこれにマッチする変数のみ残す                             |
| `shell_environment_policy.set`                     | すべてのサブプロセスへ強制的に注入する環境変数                   |

## よく使う環境変数

| 変数                                     | 用途                                                                                                                                       |
| ---------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------ |
| `CODEX_HOME`                             | Codexの状態（config・auth・logs・sessions・skillsなど）のルート。既定 `~/.codex`。設定する場合はディレクトリが事前に存在している必要がある |
| `CODEX_SQLITE_HOME`                      | SQLiteバックエンド状態の保存先（`sqlite_home` configが優先）                                                                               |
| `CODEX_API_KEY`                          | `codex exec` 単発実行用のAPIキー（ジョブ全体でなく単発実行で使う）                                                                         |
| `CODEX_ACCESS_TOKEN`                     | 信頼された自動化向けアクセストークン（`codex login --with-access-token` に渡す）                                                           |
| `CODEX_CA_CERTIFICATE` / `SSL_CERT_FILE` | 社内TLS/プライベートCA向けのCAバンドル指定                                                                                                 |
| `RUST_LOG`                               | ログ詳細度（`error`/`warn`/`info`/`debug`/`trace`、`codex_core=debug` のような絞り込みも可）                                               |

プロバイダAPIキーは固定の環境変数名ではなく、`model_providers.<id>.env_key` で指定した変数名をCodexが読みに行く。

## 参照リンク

- JSON Schema: https://developers.openai.com/codex/config-schema.json
- Config basics: https://developers.openai.com/codex/config-file/config-basic
- Advanced Configuration: https://developers.openai.com/codex/config-file/config-advanced
- Configuration Reference: https://developers.openai.com/codex/config-file/config-reference
- Sample Configuration: https://developers.openai.com/codex/config-file/config-sample
- Environment variables: https://developers.openai.com/codex/config-file/environment-variables
- Agent approvals & security: https://developers.openai.com/codex/agent-approvals-security
- Rules: https://developers.openai.com/codex/agent-configuration/rules
- Hooks: https://developers.openai.com/codex/hooks
- Managed configuration / `requirements.toml`: https://developers.openai.com/codex/enterprise/managed-configuration
