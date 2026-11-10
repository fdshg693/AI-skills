# ツール・権限の操作方法

出典: `docs/cli/reference/permissions.md`, `docs/cli/reference/configuration.md`, `docs/agent/security.md`, `docs/agent/security/run-modes.md`, `docs/cli/reference/parameters.md`, `docs/cli/github-actions.md`

## CLI フラグでの一発指定

| フラグ                                 | 効果                                                          |
| -------------------------------------- | ------------------------------------------------------------- |
| `-f, --force` / `--yolo`（エイリアス） | 明示的に deny されていない限りコマンドを強制許可              |
| `--sandbox <enabled\|disabled>`        | サンドボックスモードを明示的に上書き                          |
| `--approve-mcps`                       | 全 MCP サーバーを自動承認                                     |
| `--trust`                              | ワークスペース信頼プロンプトを省略（headless モードのみ有効） |

`-p/--print`（非対話）モードは write/shell を含む全ツールにアクセスできるが、**`--force` を付けないと変更は提案されるだけで実際には書き込まれない**（`docs/cli/headless.md`）。

```bash
# 提案のみ（ファイルは変更されない）
agent -p "Add JSDoc comments to this file"

# 実際に書き込む
agent -p --force "Refactor this code to use modern ES6+ syntax"
```

## Run Modes（実行時の承認方針。エディタ設定 > Agents > Approvals & Execution と同じ概念）

出典: `docs/agent/security/run-modes.md`

| モード                            | 無承認で実行される範囲                                                                                                  | サンドボックス                  | クラシファイア |
| --------------------------------- | ----------------------------------------------------------------------------------------------------------------------- | ------------------------------- | -------------- |
| **Auto-review**（推奨デフォルト） | allowlist 済みは即実行。他の shell コマンドは可能ならサンドボックスで実行。サンドボックス不可のものは classifier が判定 | shell コマンドに対し Yes        | Yes            |
| **Allowlist**                     | allowlist 内のアクションのみ無承認実行                                                                                  | サンドボックス有効なら Optional | No             |
| **Run Everything**                | 全ツール呼び出しが自動実行                                                                                              | No                              | No             |

Auto-review はあくまでベストエフォートの安全策で、ハードなセキュリティ境界ではない（判定ミスもあり得る）。

### Auto-review の設定 (`permissions.json`)

Run Modes 用の `permissions.json`（サンドボックスの `sandbox.json` とは別物）は平易な英語の指示文で構成:

```json
{
  "autoRun": {
    "allow_instructions": [],
    "block_instructions": [
      "Every AWS CLI command should go through approval first.",
      "Every command that modifies Kubernetes resources should go through approval first."
    ]
  }
}
```

配置場所: `~/.cursor/permissions.json`（全プロジェクト共通）と `<project>/.cursor/permissions.json`（プロジェクト固有、両方あればマージ）。チームがダッシュボードでグローバル設定を定義していればそちらが最優先（ユーザー/プロジェクトのファイルは無視される）。

## パーミッショントークン（`cli-config.json` の `permissions.allow` / `permissions.deny`）

出典: `docs/cli/reference/permissions.md` — こちらはコマンドライン CLI（`agent`、旧名 `cursor-agent`）固有の設定で、上記 Auto-review の `permissions.json` とは別体系（両方とも "permissions" と呼ばれていて紛らわしいので注意。CLI の許可/拒否リストは `cli-config.json` の `permissions` オブジェクトで管理する）。

| トークン形式                | 意味                                                      | 例                                                 |
| --------------------------- | --------------------------------------------------------- | -------------------------------------------------- |
| `Shell(commandBase)`        | シェルコマンド許可。`command:args` で引数まで glob 指定可 | `Shell(git)`, `Shell(curl:*)`                      |
| `Read(pathOrGlob)`          | ファイル読み取り                                          | `Read(src/**/*.ts)`, deny 例: `Read(.env*)`        |
| `Write(pathOrGlob)`         | ファイル書き込み                                          | `Write(src/**)`, deny 例: `Write(**/*.key)`        |
| `WebFetch(domainOrPattern)` | Web フェッチ先ドメイン                                    | `WebFetch(*.example.com)`, `WebFetch(*)`（要注意） |
| `Mcp(server:tool)`          | MCP ツール                                                | `Mcp(datadog:*)`, `Mcp(*:*)`（要注意）             |

```json
{
  "permissions": {
    "allow": [
      "Shell(ls)",
      "Shell(git)",
      "Read(src/**/*.ts)",
      "Write(package.json)",
      "WebFetch(docs.github.com)"
    ],
    "deny": ["Shell(rm)", "Read(.env*)", "Write(**/*.key)"]
  }
}
```

- deny は allow より優先。
- プロジェクトレベルでは `<project>/.cursor/cli.json` に **permissions のみ** 設定可能（他の CLI 設定はグローバル `cli-config.json` のみ）。

### CI/自動化での推奨パターン（`docs/cli/github-actions.md`）

「フル権限で任せる」より「permissions で厳格に制限し、決定的な操作（git commit/push, PR コメント等）は別ステップで CI 自身に行わせる」構成が本番運用では推奨されている:

```json
{
  "permissions": {
    "allow": [
      "Read(**/*.md)",
      "Write(docs/**/*)",
      "Shell(grep)",
      "Shell(find)"
    ],
    "deny": ["Shell(git)", "Shell(gh)", "Write(.env*)", "Write(package.json)"]
  }
}
```

## サンドボックス（`sandbox.json` とプラットフォーム実装）

- `permissions.json`（Auto-review の可否）と `sandbox.json`（サンドボックス化されたコマンドが到達できる範囲）は役割が別。
- 配置: `~/.cursor/sandbox.json`（全体）/ `<project>/.cursor/sandbox.json`（プロジェクト、優先度高）。チーム管理者ポリシーと Cursor 組み込みルールが最上位でローカル設定では弱められない。
- デフォルトのサンドボックス挙動: ワークスペース内は読み書き可、`.git/config` `.git/hooks` `.vscode` `.cursorignore` 等は保護、ネットワークはデフォルトブロックし `sandbox.json` で開放、`/tmp` 等の一時ディレクトリは書き込み可。
- ネットワークモード: `sandbox.json Only` / `sandbox.json + Defaults`（デフォルト、パッケージマネージャ等の定番ドメインを自動許可） / `Allow All`。
- OS 実装: macOS は Seatbelt (`sandbox-exec`)、Linux は Landlock + seccomp（カーネル 6.2+ と unprivileged user namespaces が必要）。要件未充足時は承認プロンプトにフォールバック。
- CLI/リモート環境では AppArmor プロファイルが同梱されないため、user-namespace 権限エラー時は別途 `.deb`/`.rpm` パッケージのインストールが必要（`docs/agent/security/run-modes.md` にダウンロード URL あり）。
- サンドボックス内注入環境変数: `CURSOR_SANDBOX`（`seatbelt`/`native`）, `CURSOR_ORIG_UID`/`CURSOR_ORIG_GID`（ホスト実ユーザーの UID/GID。Linux では sandbox 内 `id -u` が 0 になるため、Docker 等でホストユーザーに合わせたい場合はこちらを使う）。

```bash
docker run --rm \
  --user "${CURSOR_ORIG_UID:-$(id -u)}:${CURSOR_ORIG_GID:-$(id -g)}" \
  -v "$PWD:/work" -w /work my-image build
```

## Run Mode 以外の常時ガードレール

Run Modes / サンドボックスとは独立して、モードに関係なく承認を要求する保護機能（`docs/agent/security/run-modes.md`）:

- **Browser Protection**: ブラウザツールの自動実行を防止
- **File-Deletion Protection**: ファイル削除（`rm` 含む）の自動実行を防止
- **External-File Protection**: ワークスペース外でのファイル作成・変更・削除の自動実行を防止

## MCP ツール管理

```bash
agent mcp login <identifier>
agent mcp list
agent mcp list-tools <identifier>
agent mcp enable <identifier>
agent mcp disable <identifier>
```

MCP は `.cursor/mcp.json` / `~/.cursor/mcp.json` で設定し、接続そのものと各ツール呼び出しの両方に承認が必要（`Mcp(server:tool)` allowlist で個別に事前承認可能）。デフォルトではネットワークリクエストは GitHub・直接リンク取得・Web 検索プロバイダのみに制限される（`docs/agent/security.md`）。
