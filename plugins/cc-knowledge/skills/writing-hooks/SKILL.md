---
# 同梱のhooks.mdは参照用のリファレンス、このファイル自体はフックを実際に書く際のベストプラクティス集
name: writing-hooks
description: Use when creating or editing Claude Code hooks (.claude/settings.json hooks, PreToolUse/PostToolUse/Stop/UserPromptSubmit etc.) — choosing events/matchers/types, writing safe commands, setting exit codes correctly, avoiding common pitfalls.
meta:
  tag: []
  requires_repo_tools: none
  requires_env: none
  dependencies: none
  requires_install: none
  requires_hooks: none
  requires_skills: claude-code-docs
  status: stable
  description: no description
  version: 1.0.7
---

# フック作成のベストプラクティス

フックは強力だが事故りやすい（exit codeの誤解、matcherの正規表現罠、Windows特有の落とし穴など）。
ここでは**実際に書く際の手順とチェックリスト**をまとめる。イベント一覧・JSONスキーマ・全落とし穴の詳細は同梱の [hooks.md](hooks.md) を参照。

## 作成手順

1. **イベントを選ぶ** — いつ発火させたいか（`PreToolUse`でブロック／`PostToolUse`で後処理／`Stop`でターン終了時 等）。候補に迷ったら hooks.md のイベント一覧表を確認。
2. **マッチャーを絞る** — ツール名・イベント種別で対象を限定。正規表現扱いになる文字種かどうかに注意（下記チェックリスト）。
3. **typeを選ぶ** — 決定的な処理なら `command`。外部API連携なら `http`。既存MCPツールを叩くなら `mcp_tool`。ルールでは書けない“判断”が要るなら `prompt`/`agent`（実験的、本番非推奨）。
4. **ハンドラーを安全に書く** — 下記チェックリストのクオート・パス・exec/shell formの選択に従う。
5. **exit codeを正しく使う** — ブロックしたいなら`exit 2`一択。
6. **ローカルでテストしてからコミット** — サンプルJSONを標準入力に流して`$?`を確認してから設定に追加する。

## チェックリスト（ベストプラクティス）

- [ ] ブロックしたい処理は **`exit 2`** を使う。`exit 1`は失敗として扱われず処理が継続してしまう（`WorktreeCreate`は0以外全てが中止扱い、`WorktreeRemove`も0以外で削除失敗扱い）
- [ ] `exit 2`とstdoutのJSON出力は**併用しない**（exit 2ではJSONは無視される）。構造化制御は exit 0 + JSON、ブロックのみなら exit 2 + stderr、どちらかに統一
- [ ] シェル変数は必ず `"$VAR"` のようにダブルクォートする（インジェクション・パス中のスペース対策）
- [ ] スクリプトパスは絶対パス（`${CLAUDE_PROJECT_DIR}`等）で指定する
- [ ] パストラバーサル（`..`）や`.env`・`.git/`など機密ファイルへのアクセスを弾く
- [ ] マッチャーは英数字・`_`・`-`・空白・`,`・`|`以外の文字を含むと**正規表現**として評価される。完全一致させたいなら`^Edit$`のようにアンカーで囲む（`Edit.*`は`NotebookEdit`にも意図せずマッチする）
- [ ] パスにスペース・特殊文字・`${CLAUDE_PROJECT_DIR}`等のプレースホルダーを使うなら **exec form**（`args`指定）を推奨
- [ ] Windowsでexec formを使う場合、`command`は実ファイル（`.exe`等）である必要がある。npm/npx等の`.cmd`/`.bat`シムはexec formで起動できないため、直接スクリプトを叩くかshell formを使う
- [ ] `"shell": "powershell"`使用時、`${CLAUDE_PROJECT_DIR}`は`${env:NAME}`形式でダブルクォート文字列内でのみ展開される（シングルクォート内では展開されない）。裸の`$CLAUDE_PROJECT_DIR`は未定義変数として`$null`になるので必ず`$env:`を付ける
- [ ] shell profileに無条件`echo`があると標準出力に混ざりJSONパースが失敗する。プロファイル内のechoは対話シェル判定（`[[ $- == *i* ]]`）でガードする
- [ ] `Stop`フック実装時は入力の`stop_hook_active`をチェックして早期`exit 0`し、tool call を挟まない8回連続ブロックによるターン強制終了（`CLAUDE_CODE_STOP_HOOK_BLOCK_CAP` で変更可）を待たずに無限ループを避ける
- [ ] `async: true`は`command`タイプのみ対応。非同期フックはツール呼び出しをブロックできない点を前提に設計する
- [ ] デプロイ前に `echo '{...}' | ./my-hook.sh` のようにサンプルJSONを標準入力に流し、`$?`とstdout/stderrを手元で確認する
- [ ] **コマンドフックはユーザーの実行権限をフルで持つ**。設定を追加する前に内容を必ずレビューする

## このリポジトリ（fdshg693/ai）でフックを足す・直すとき

`.claude/hooks/` はインストール先であり、ここにスクリプトを置いたり `settings.json` を手で書いたりしない。

1. 正本は `agent-compat/agent-tooling/agent_tooling/hooks/`。`scenarios/<hook-id>/hook.yaml`（登録イベント・matcher・配布可否）と `adapters/<agent>/<hook-id>.py`（本体）を足し、`build/build.py` の `ENTRIES` に登録する。書き方は `agent-compat/agent-tooling/agent_tooling/hooks/AGENTS.md`
2. `just --justfile agent-compat/agent-tooling/justfile generate` で `generated/` と `catalog.json` を再生成する
3. リポジトリ直下で `just hooks-install`（新規）または `just hooks-update`（変更）を実行し、skill-tools に配置・登録させる。他プロジェクトへは `skill-tools hooks install --agent <agent> <hook-id>`

全体の流れと設計判断は `maintenance/docs/hook-distribution.md`。

## 困ったときは

1. まず同梱の [hooks.md](hooks.md)（詳細リファレンス: イベント全種一覧、JSON入出力スキーマ、マッチャー評価ルール、Windows/シェル固有の落とし穴など）を確認する。
2. それでも解決しない・挙動が期待と違う場合:
   - `Ctrl+O`でトランスクリプト表示に切り替え、フックの発火結果（成功/ブロッキングエラー/非ブロッキングエラー）を確認する
   - `claude --debug-file <path>`でデバッグログを出力し`tail -f`で監視する（`CLAUDE_CODE_DEBUG_LOG_LEVEL=verbose`でマッチャー判定など詳細ログも見られる）
3. デバッグしても原因不明、または hooks.md 執筆時点から仕様が変わっている可能性がある場合は、**claude-code-docsスキル**で最新の公式ドキュメント（`code.claude.com`）を参照する。
