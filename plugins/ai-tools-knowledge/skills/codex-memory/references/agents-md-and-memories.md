# AGENTS.md discovery / memories 詳細リファレンス

出典: `developers.openai.com/codex` 配下（[Custom instructions with AGENTS.md](https://developers.openai.com/codex/agents-md)、[Project instructions discovery](https://developers.openai.com/codex/config-file/config-advanced#project-instructions-discovery)、[Memories](https://developers.openai.com/codex/customization/memories)、Configuration Reference）。2026-08時点の内容。最新版は本ページまたは`codex-docs`スキルで確認する。

## 目次

- [AGENTS.md discoveryアルゴリズム全文](#agentsmd-discoveryアルゴリズム全文)
- [設定キー一覧（discovery関連）](#設定キー一覧discovery関連)
- [config.toml記述例](#configtoml記述例)
- [検証・トラブルシュート](#検証トラブルシュート)
- [memories機能の詳細](#memories機能の詳細)
- [memories関連の設定キー一覧](#memories関連の設定キー一覧)

---

## AGENTS.md discoveryアルゴリズム全文

> Codex builds an instruction chain when it starts (once per run; in the TUI this usually means once per launched session). Discovery follows this precedence order:
>
> 1. **Global scope:** In your Codex home directory (defaults to `~/.codex`, unless you set `CODEX_HOME`), Codex reads `AGENTS.override.md` if it exists. Otherwise, Codex reads `AGENTS.md`. Codex uses only the first non-empty file at this level.
> 2. **Project scope:** Starting at the project root (typically the Git root), Codex walks down to your current working directory. If Codex cannot find a project root, it only checks the current directory. In each directory along the path, it checks for `AGENTS.override.md`, then `AGENTS.md`, then any fallback names in `project_doc_fallback_filenames`. Codex includes at most one file per directory.
> 3. **Merge order:** Codex concatenates files from the root down, joining them with blank lines. Files closer to your current directory override earlier guidance because they appear later in the combined prompt.
>
> Codex skips empty files and stops adding files once the combined size reaches the limit defined by `project_doc_max_bytes` (32 KiB by default).

補足（config-advanced節より）:

> By default, Codex treats a directory containing `.git` as the project root. To customize this behavior, set `project_root_markers` in `config.toml`:
>
> ```toml
> project_root_markers = [".git", ".hg", ".sl"]
> ```
>
> Set `project_root_markers = []` to skip searching parent directories and treat the current working directory as the project root.

> Codex reads `AGENTS.md` (and related files) and includes a limited amount of project guidance in the first turn of a session.

この「first turn of a session」という記述と「once per run」という記述から、discoveryはセッション開始（TUIなら起動時、`codex exec`なら実行開始時）に**一度だけ**走ることが確認できる。ターン単位・ファイル編集単位での再走査は行われない。`--cd`で新しいセッションを開始した場合、その新しいCWDを基準にdiscoveryが再実行される。

## 設定キー一覧（discovery関連）

| キー                             | 型              | 既定値            | 説明                                                                                                                                             |
| -------------------------------- | --------------- | ----------------- | ------------------------------------------------------------------------------------------------------------------------------------------------ |
| `project_root_markers`           | `array<string>` | `[".git"]`        | プロジェクトルート探索に使うマーカーファイル名の配列。`[]`にすると親ディレクトリ探索自体をスキップしCWDをルート扱いする                          |
| `project_doc_max_bytes`          | `number`        | `32768`（32 KiB） | 各`AGENTS.md`から読み取り、結合するプロジェクト指示の最大バイト数。超過分は以降のファイルごと打ち切られる                                        |
| `project_doc_fallback_filenames` | `array<string>` | `[]`              | あるディレクトリに`AGENTS.md`（および`AGENTS.override.md`）が無い場合に代わりに探すファイル名の配列。順序どおりに試行される                      |
| `model_instructions_file`        | `string (path)` | 未設定            | `AGENTS.md`ベースの指示を丸ごと置き換える差し替えファイル。プロジェクトconfig内の相対パスは、そのconfigが属する`.codex/`フォルダ基準で解決される |
| `instructions`                   | `string`        | 未設定            | 将来用に予約。`model_instructions_file`または`AGENTS.md`を優先すること                                                                           |
| `developer_instructions`         | `string`        | 未設定            | セッションへ注入する追加のdeveloper instructions（任意）                                                                                         |
| `CODEX_HOME`                     | 環境変数        | `~/.codex`        | Codexホームディレクトリ（グローバル層の`AGENTS.md`/`AGENTS.override.md`の置き場所、memoriesの保存先もここ配下）                                  |

## config.toml記述例

```toml
################################################################################
# Project Documentation Controls
################################################################################

# Max bytes from AGENTS.md to embed into first-turn instructions. Default: 32768
project_doc_max_bytes = 32768

# Ordered fallbacks when AGENTS.md is missing at a directory level. Default: []
project_doc_fallback_filenames = []

# Project root marker filenames used when searching parent directories. Default: [".git"]
# project_root_markers = [".git"]
```

`model_instructions_file`の相対パス解決について:

> Relative paths inside a project config (for example, `model_instructions_file`) are resolved relative to the `.codex/` folder that contains the `config.toml`.

## 検証・トラブルシュート

公式ドキュメントの「Verify your setup」節:

- `codex --ask-for-approval never "Summarize the current instructions."` をリポジトリルートから実行する。グローバル→プロジェクトの優先順位でガイダンスが返答に含まれるはず。
- `codex --cd subdir --ask-for-approval never "Show which instruction files are active."` でネストしたoverrideが広い範囲のルールを置き換えているか確認する。
- どの指示ファイルが読み込まれたか監査したい場合、`codex -c log_dir=./.codex-log` でプレーンテキストのTUIログを有効化し `./.codex-log/codex-tui.log` を確認する。あるいはセッションログを有効にしている場合、直近の `session-*.jsonl` を確認する。
- 指示が古く見える場合はCodexを対象ディレクトリで再起動する。Codexは実行のたびに（TUIならセッション開始のたびに）instruction chainを再構築するため、手動でクリアすべきキャッシュは無い。

「Troubleshoot discovery issues」節:

- **何も読み込まれない**: 意図したリポジトリにいるか、`codex status`が期待するworkspace rootを報告しているかを確認する。Codexは空ファイルを無視するため、指示ファイルに内容があるか確認する。
- **意図しないガイダンスが出る**: ディレクトリツリーの上位、またはCodexホーム配下に`AGENTS.override.md`が無いか探す。通常のファイルに戻したい場合はoverrideをリネームまたは削除する。
- **fallback名が無視される**: `project_doc_fallback_filenames`に列挙した名前にタイポが無いか確認し、設定変更後はCodexを再起動して反映させる。
- **指示が切り詰められる**: `project_doc_max_bytes`を上げるか、大きなファイルをネストしたディレクトリへ分割して重要な指示を守る。
- **プロファイルの混同**: Codex起動前に`echo $CODEX_HOME`を確認する。既定と異なる値は、編集したものとは別のCodexホームディレクトリを指している可能性がある。

## memories機能の詳細

> After you enable memories, Codex can turn useful context from eligible prior chats into local memory files. Codex skips active or short-lived sessions, redacts secrets from generated memory fields, and updates memories in the background instead of immediately at the end of every chat.
>
> Memories may not update right away when a chat ends. Codex waits until a chat has been idle long enough to avoid summarizing work that's still in progress.
>
> Memory generation can also skip a background pass when your Codex rate-limit remaining percentage is below the configured threshold, so Codex doesn't spend quota when you're near a limit.

保存先:

> Codex stores memories under your Codex home directory. By default, that's `~/.codex`. ... The main memory files live under `~/.codex/memories/` and include summaries, durable entries, recent inputs, and supporting evidence from prior chats.
>
> Treat these files as generated state. You can inspect them when troubleshooting or before sharing your Codex home directory, but don't rely on editing them by hand as your primary control surface.

チャット単位の制御:

> In the ChatGPT desktop app and Codex TUI, use `/memories` to control memory behavior for the current chat. Chat-level choices let you decide whether the current chat can use existing memories and whether Codex can use the chat to generate future memories.
>
> Chat-level choices don't change your global memory settings.

プライバシー:

> Don't store secrets in memories. Codex redacts secrets from generated memory fields, but you should still review memory files before sharing your Codex home directory or generated memory artifacts.

有効化:

> Local Codex memories are off by default. In the ChatGPT desktop app, open **Settings > Personalization** and turn on **Enable memories**.
>
> For config-based setup, add the feature flag to `config.toml`:
>
> ```toml
> [features]
> memories = true
> ```

## memories関連の設定キー一覧

| キー                                        | 型        | 既定値                           | 説明                                                                                                                                                                                                         |
| ------------------------------------------- | --------- | -------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| `features.memories`                         | `boolean` | `false`                          | memories機能自体の有効/無効                                                                                                                                                                                  |
| `memories.generate_memories`                | `boolean` | `true`                           | `false`にすると、新規スレッドをメモリ生成の入力として使わない                                                                                                                                                |
| `memories.use_memories`                     | `boolean` | `true`                           | `false`にすると、既存メモリを以後のセッションへ注入しない                                                                                                                                                    |
| `memories.disable_on_external_context`      | `boolean` | `false`                          | `true`にすると、MCPツール呼び出し・Web検索・tool searchなど外部コンテキストを使ったスレッドをメモリ生成対象から除外する。旧キー`memories.no_memories_if_mcp_or_web_search`は互換エイリアスとして引き続き有効 |
| `memories.min_rate_limit_remaining_percent` | `number`  | 未文書化（要`codex-docs`で確認） | メモリ生成を開始するために必要な、残レート制限の最小パーセンテージ                                                                                                                                           |
| `memories.extract_model`                    | `string`  | 未文書化                         | チャット単位のメモリ抽出に使うモデルの上書き                                                                                                                                                                 |
| `memories.consolidation_model`              | `string`  | 未文書化                         | 複数チャットにまたがるメモリ統合（グローバル集約）に使うモデルの上書き                                                                                                                                       |

`config.toml`の記述例:

```toml
[features]
memories = true

[memories]
# generate_memories = true
# use_memories = true
# disable_on_external_context = false # legacy alias: no_memories_if_mcp_or_web_search
```

---

## 参考文献

- Custom instructions with AGENTS.md: https://developers.openai.com/codex/agents-md
- Project instructions discovery（config-advanced内）: https://developers.openai.com/codex/config-file/config-advanced#project-instructions-discovery
- Memories: https://developers.openai.com/codex/customization/memories
- Configuration Reference: https://developers.openai.com/codex/config-file/config-reference
- 公式AGENTS.mdフォーマットの解説サイト: https://agents.md
