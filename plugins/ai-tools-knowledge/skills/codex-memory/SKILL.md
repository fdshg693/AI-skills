---
name: codex-memory
description: Use when explaining or designing how OpenAI Codex remembers project context — the `AGENTS.md`/`AGENTS.override.md` project-instructions discovery Codex runs before every turn (precedence order, `project_doc_max_bytes`/`project_doc_fallback_filenames`/`project_root_markers`/`model_instructions_file`), what that discovery does NOT cover (no glob-scoped rule files like Claude Code's `.claude/rules`, no reload mid-session, directories off the root→cwd path are skipped), how to close that gap with a hook, and the separate generated `memories` feature (`features.memories`, `~/.codex/memories/`, `/memories`). Do not use this skill for hook JSON schema/matcher/trust details (use codex-hooks), general config.toml editing beyond memory-related keys (use codex-settings), or CLI flags (use codex-cli-docs).
meta:
  tag: []
  requires_repo_tools: none
  requires_env: none
  dependencies: none
  requires_install: none
  requires_hooks: "任意: AGENTS.md未カバー範囲を補うPreToolUseフック（本文の作成例を参照）"
  requires_skills: codex-docs, codex-settings, codex-hooks
  status: stable
  description: no description
  version: 1.0.3
---

# Codexのメモリ機構（AGENTS.md discovery / 生成メモリ）

Codexが「プロジェクトの文脈」を覚える仕組みは2つあり、混同しやすい。

1. **AGENTS.md discovery** — 静的なテキストファイルを、セッション開始時に1回だけ決定的なルールで集めてプロンプトへ埋め込む仕組み。
2. **memories機能**（`features.memories`） — 過去のチャットからCodexが自動生成する要約を、`~/.codex/memories/` に永続化し、以後のセッションへ注入する仕組み（既定オフ）。

このスキルは両方の挙動と設定キー、そして**AGENTS.md discoveryが自動でカバーしない範囲**（Claude CodeのCLAUDE.mdと比較して事故りやすい点）をまとめる。詳細な設定ファイル一般論は **codex-settingsスキル**、hookのJSON契約は **codex-hooksスキル** を使う。

## 1. AGENTS.mdはいつ・どこまで自動で読まれるか

Codexは**起動ごとに1回**（TUIでは通常セッション開始時に1回。ターンごとの再走査ではない）、以下の優先順位でinstruction chainを構築する。

1. **グローバル層**: Codexホーム（既定 `~/.codex`、`CODEX_HOME`で変更可）直下で `AGENTS.override.md` があればそれを、無ければ `AGENTS.md` を読む。このレイヤーは**空でない最初の1ファイルのみ**採用。
2. **プロジェクト層**: プロジェクトルート（既定は`.git`を含むディレクトリ。`project_root_markers`で変更可、`[]`にするとCWDをルート扱いしてこの探索自体をスキップ）から**CWDまで下方向に歩く**。ルートが見つからない場合はCWDのみを見る。通過する各ディレクトリで `AGENTS.override.md` → `AGENTS.md` → `project_doc_fallback_filenames`（既定`[]`）の順に**1ディレクトリにつき最大1ファイル**を採用。
3. **結合順序**: ルート側から順に空行区切りで連結する。CWDに近いファイルほど後段に置かれるため、モデルに対して実質的に優先される。
4. 空ファイルはスキップ。結合サイズが `project_doc_max_bytes`（既定 `32768` バイト＝32KiB）に達した時点で以降のファイル追加を打ち切る。

```toml
# ~/.codex/config.toml または <repo>/.codex/config.toml
project_root_markers = [".git"]              # 既定。[".git", ".hg", ".sl"] 等に拡張可、[] でルート探索自体を無効化
project_doc_max_bytes = 32768                 # 既定。超えると以降のAGENTS.mdは切り捨て
project_doc_fallback_filenames = []           # 既定。["TEAM_GUIDE.md", ".agents.md"] のように追加可
# model_instructions_file = "/path/to/instructions.txt"  # AGENTS.mdの代わりに丸ごと差し替える場合のみ
```

`model_instructions_file` はAGENTS.mdによる注入そのものを置き換える別レイヤーで、通常は使わない（挙動を統一しづらくなる）。

検証コマンド:

```bash
codex --ask-for-approval never "Summarize the current instructions."
codex --cd services/payments --ask-for-approval never "List the instruction sources you loaded."
codex -c log_dir=./.codex-log   # 起動後 ./.codex-log/codex-tui.log で読み込まれたファイルを監査できる
```

## 2. Claude CodeのCLAUDE.mdと違い、自動でカバーされない範囲

Claude Codeのユーザーは「関連ファイルを触ったら自動でCLAUDE.mdが注入される」「`.claude/rules`のようなglobパスでの絞り込みルールがある」という前提を持ちがちだが、Codexは**どちらも持たない**。

- **セッション開始時の1回きり**: 起動後にモデルが別ディレクトリのファイルを編集しても、そのディレクトリのAGENTS.mdを読みにいく再走査は起きない。`--cd`でCWDを変えて新しいセッションを開始した場合のみ、そのパス上のAGENTS.mdが再収集される。
- **root→CWDの経路上だけ**: 収集対象は「プロジェクトルートから初期CWDまでの経路上の各ディレクトリ」に限られる。初期CWDの**兄弟ディレクトリ**や**子孫ディレクトリ**にあるAGENTS.mdは、モデルがそこのファイルを編集・参照しても自動では読み込まれない。モノレポでCWDをルート直下に置いたまま複数サービスを横断編集する場合、サービスごとのAGENTS.mdが素通りされやすい。
- **globパスでの絞り込みルールが無い**: Claude Codeの`.claude/rules/*.md`（frontmatterのglobパターンでファイル種別ごとに条件付き注入する仕組み）に相当する機能はCodexに存在しない。ファイル名は固定候補（`AGENTS.override.md` → `AGENTS.md` → `project_doc_fallback_filenames`）のみで、拡張子やパスパターンによる出し分けはできない。
- **1ディレクトリ1ファイルまで**: 同じディレクトリに複数の指示ファイルを置いても1つしか採用されない。

これらはバグではなく仕様であり、公式ドキュメント（[Custom instructions with AGENTS.md](https://developers.openai.com/codex/agents-md)）に明記されている。**ただ置くだけ**のベストプラクティスは「初期CWDから見える経路にしかAGENTS.mdを置けない」場合にしか成立しない。経路外のディレクトリを横断編集する運用（モノレポでのマルチサービス作業など）では、以下のいずれかで補う。

## 3. 経路外AGENTS.mdを補うベストプラクティス

優先順で検討する。

1. **作業対象が事前に分かっているなら`--cd`で該当ディレクトリから起動する**（または最初のプロンプトでそのサブディレクトリへ移動してから作業を始める）。追加の仕組みが要らず最も確実。
2. **ルートのAGENTS.mdに「編集前にそのディレクトリ直下のAGENTS.md/READMEを確認せよ」という指示を明記する**。仕組みへの依存を減らせるが、モデルの遵守に依存するため強制力は弱い。
3. **PreToolUse hookで、編集対象パスの祖先ディレクトリのAGENTS.mdをその場で読み込みモデルへ注入する**。強制力があり、モノレポで複数サービスを横断編集するセッションに向く。hookのJSON契約・matcher・trustレビューの詳細は**codex-hooksスキル**を使う。以下は最小構成の例（詳細を作り込む前に必ずcodex-hooksスキルでイベント別出力形を確認する）。

```json
// .codex/hooks.json
{
  "hooks": {
    "PreToolUse": [
      {
        "matcher": "apply_patch",
        "hooks": [
          {
            "type": "command",
            "command": "python3 \"$(git rev-parse --show-toplevel)/agent-tooling/agent_tooling/hooks/generated/codex/nested_agents_md.py\"",
            "statusMessage": "Checking nested AGENTS.md",
            "additionalContextLimit": 4000
          }
        ]
      }
    ]
  }
}
```

スクリプト側の要点:

- stdinのJSONから `tool_input.command`（`apply_patch`のパッチ本文）または対象ファイルパスを取り出し、その祖先ディレクトリを1つずつ遡って `AGENTS.override.md`/`AGENTS.md` を探す（探索ロジックはセクション1のdiscoveryアルゴリズムを模倣する）。
- 既にroot→CWD経路で読み込み済みのディレクトリと重複しないよう、初期CWDを`cwd`フィールドから取得して除外する。
- ブロックはせず、見つかった内容を次の形でstdoutへ返す（`additionalContext`のみ）。

```json
{
  "hookSpecificOutput": {
    "hookEventName": "PreToolUse",
    "additionalContext": "services/payments/AGENTS.md:\n<ファイル内容>"
  }
}
```

- 追加した/変更したhookは `/hooks` で信頼するまで実行されない点、`additionalContext`が既定2,500トークンでspillingされる点は**codex-hooksスキル**のチェックリストを確認する。

この方法は「ファイルタイプごとのglobルール」そのものを再現するものではなく、あくまで**ディレクトリ単位のAGENTS.md探索範囲を広げる**補完策である。過剰な自動注入はコンテキストを圧迫するため、経路外ディレクトリを横断する運用が実際にある場合のみ導入する。

## 4. memories機能（生成された長期メモリ、AGENTS.mdとは別物）

`AGENTS.md`が静的・決定的なのに対し、`memories`機能は**過去のチャットからCodexが自動でメモリを生成し、以後のセッションに注入する**。既定オフ。

```toml
[features]
memories = true

[memories]
# generate_memories = true                    # 既定true。新規チャットをメモリ生成の入力として使うか
# use_memories = true                          # 既定true。既存メモリを以後のセッションへ注入するか
# disable_on_external_context = false          # 既定false。MCP/Web検索等を使ったチャットをメモリ生成対象から除外
# min_rate_limit_remaining_percent = ...       # レート制限残量がこの閾値未満だとメモリ生成をスキップ
# extract_model = "..."                        # チャット単位のメモリ抽出に使うモデルを上書き
# consolidation_model = "..."                  # メモリ統合（複数チャットの集約）に使うモデルを上書き
```

挙動の要点:

- アクティブ/短時間のセッションはメモリ化対象から除外され、チャット終了直後ではなく**アイドルになってからバックグラウンドで**生成される（即時ではない）。
- 生成物は `~/.codex/memories/` 配下（summaries・durable entries・recent inputs・裏付けとなるevidenceなど）に保存される。**手動編集する一次コントロール手段としては想定されていない**（トラブルシュート時の確認・共有前レビュー用途に留める）。
- Codexは生成メモリからシークレットを redact しようとするが保証ではない。Codexホームディレクトリを共有する前は必ず内容を確認する。
- TUI/デスクトップ版では `/memories` でチャット単位に「このチャットで既存メモリを使うか」「このチャットを将来のメモリ生成に使うか」を制御できる（グローバル設定は変わらない）。

AGENTS.mdとの使い分け: **常に守ってほしいルール・手順はAGENTS.md**（決定的・監査可能）、**過去の作業から拾ってほしい文脈はmemories**（生成的・ベストエフォート）と役割分担して考える。

## チェックリスト

- [ ] 「ファイルを触ると自動でAGENTS.mdが再読込される」という誤解をユーザーに広げていないか（起動時1回のみ）
- [ ] 対象ディレクトリがプロジェクトルート→初期CWDの経路上にあるか確認したか（経路外なら`--cd`・明示指示・hookのいずれかで補う）
- [ ] Claude Codeの`.claude/rules`のようなglobベース絞り込みをAGENTS.mdに期待していないか（存在しない機能）
- [ ] `project_doc_max_bytes`（既定32KiB）を超える量のAGENTS.mdを書いていないか。超える場合はネストしたディレクトリへ分割する
- [ ] hookで経路外AGENTS.mdを補う場合、`/hooks`での信頼レビューが必要な点をユーザーに伝えたか
- [ ] `memories`機能とAGENTS.mdを混同していないか（前者は生成的・既定オフ、後者は決定的・常時有効）
- [ ] memories関連ファイルやhook出力にシークレットを含めていないか

## 困ったときは

1. AGENTS.md discoveryの詳細・トラブルシュートは同梱の [references/agents-md-and-memories.md](references/agents-md-and-memories.md)（公式ドキュメントからの抜粋: discoveryアルゴリズム全文、設定キー表、memories設定キー表、トラブルシュート項目）を確認する。
2. 仕様が変わっている可能性がある、または載っていない設定キーを使いたい場合は **codex-docsスキル** で最新の公式ドキュメント（`developers.openai.com/codex/agents-md`、`developers.openai.com/codex/customization/memories`）を確認する。
3. `config.toml`のスコープ・優先順位・置き場所全般は **codex-settingsスキル** を使う。
4. hookの中身（イベント別スキーマ・matcher・trust・非同期制約）を詳しく扱う場合は **codex-hooksスキル** を使う。
