---
name: github-agentic-workflows
description: Create, update, review, compile, and debug GitHub Agentic Workflows (gh-aw) markdown workflows. Use when a task mentions GAW, gh-aw, agentic workflows, .github/workflows/*.md, safe outputs, workflow frontmatter, or agentic workflow run failures.
disable-model-invocation: true
meta:
  tag: []
  requires_repo_tools: none
  requires_env: CLAUDE_SKILL_DIR
  dependencies: none
  requires_install: gh-aw CLI
  requires_hooks: none
  requires_skills: none
  status: stable
  description: no description
  version: 1.0.3
# 依存関係:
#   - GitHub Agentic Workflows (gh-aw) CLI for compilation and execution checks
#   - Official GAW reference snapshots downloaded by download_gaw_reference.py
#   - Claude Code skill conventions from writing-skill
---

!`python "${CLAUDE_SKILL_DIR}/download_gaw_reference.py"`

# GitHub Agentic Workflows (gh-aw)

GitHub Agentic Workflows は、YAML frontmatter と Markdown prompt body から GitHub Actions workflow を生成する仕組み。対象は通常 `.github/workflows/<workflow-id>.md` で、生成物は対応する `.lock.yml`。

## 最初の判断

1. **対象を確認する**: `.github/workflows/*.md` の gh-aw workflow か、通常の GitHub Actions YAML かを区別する。通常の YAML の複数ジョブ構成やデプロイ制御を無理に gh-aw へ移さない。
2. **依頼の種類を判定する**:
   - 新規作成: `references/gaw-reference-map.md` の作成ガイド、trigger、syntax、safe outputs を読む。
   - 既存編集: まず対象 workflow と `.lock.yml`、`@.github/aw/instructions.md`（存在する場合）を読み、変更範囲を最小化する。
   - デバッグ: `debug-agentic-workflow` と `workflow-editing` の該当セクションを読み、compile → logs/audit の順に調べる。
   - シナリオ評価だけ: ファイルを作らず、trigger・scope・tools・permissions・safe outputs・noop 条件だけを提案する。
3. **必要な公式資料だけを読む**: まず `output/llms.txt` または `output/gaw-excerpt.md` で URL を特定し、詳細は `output/llms-full.txt` から URL 単位で抽出する。全文を毎回コンテキストへ読み込まない。

## 作成・編集の安全規約

- 主エージェント job は read-only に保つ。GitHub への書き込みは `safe-outputs:` にルーティングし、`issues: write`、`pull-requests: write`、`contents: write` を主 job に付与しない。
- trigger は最小限にする。PR では必要に応じて `paths:` を絞り、fork を許可する場合は `forks:` を明示する。`workflow_run` は対象 workflow 名、`types: [completed]`、結論の `if:` を明示する。
- `strict: true` を既定にし、tools・network・bash allowlist は必要最小限にする。GitHub の読み取りは通常 `tools.github.mode: gh-proxy` と `toolsets` を優先する。
- PR/Issue/comment など信頼できない入力を shell に直接埋め込まない。値は環境変数またはサニタイズ済み step output 経由で渡す。
- 可視の変更が不要な成功ケースは `noop` を使う。未取得データ・認証失敗・必要ツール欠落など、意味のある処理を完了できない場合は `report_incomplete` を使う。
- `create-pull-request` を使う場合は必ず `allowed-files` を目的のパスに制限する。専用 safe output で実現できる GitHub mutation を `gh` や bash で直接実行しない。
- gh-aw は単一の agent job が基本。複数段階のデプロイ、fan-out/fan-in、外部イベント待ち、job 間の AI 状態共有、rollback が必要なら通常の GitHub Actions を推奨する。

## 新規 workflow の手順

1. 依頼から一意な kebab-case の workflow ID を決め、既存の `.github/workflows/<id>.md` と lock file を確認する。
2. trigger、対象範囲、読み取り tools、必要な safe output、明示的な noop 条件を決める。定期レポートは期間、グルーピング軸、重複排除キーも先に固定する。
3. frontmatter は最小構成で書く。`permissions` は read-only、`strict: true`、必要な `network.allowed`、`tools`、`safe-outputs` のみを設定する。
4. Markdown body は短い命令形にし、trigger context・許可された出力・成功時の noop 条件・出力形式を明記する。
5. `gh aw compile <workflow-id> --strict` を実行し、エラーをすべて直す。frontmatter を変えたら必ず再コンパイルし、lock file の差分を確認する。

## 既存 workflow の変更

- frontmatter（`on`、`permissions`、`tools`、`network`、`imports`、`safe-outputs`、engine 等）を変えた場合は `gh aw compile <workflow-id> --strict` を実行する。
- body だけの変更も、lock file のメタデータを同期するため最終的に compile を実行する。
- 既存の安全制約、出力契約、`noop` 条件を壊さず、関係のない整形や設定変更を加えない。

## 実行確認・デバッグ

- ローカルで構文を確認: `gh aw compile <workflow-id> --strict`。
- 一覧と実行状態: `gh aw status`。
- 手動起動: `gh aw run <workflow-id>`（`gh workflow run` より優先）。
- 実行ログ: `gh aw logs <workflow-id> --json`。
- 特定 run の調査: `gh aw audit <run-id> --json`、必要なら `gh aw checks <run-id>`。
- 失敗時は permissions/auth、missing tools、safe output の未設定、network allowlist、入力の曖昧さ、timeout、不要な token 消費の順に確認する。修正後に compile が通ってから再実行を提案する。

## 公式参照の使い方

- 起動時に `download_gaw_reference.py` が `llms.txt` と `llms-full.txt` を 24 時間キャッシュで更新する。強制更新は `python "${CLAUDE_SKILL_DIR}/download_gaw_reference.py" --force`。
- `output/gaw-excerpt.md` が存在する場合は最初に読む。詳細が必要なときだけ `extract_doc_section.py` で `output/llms-full.txt` から該当 URL を抽出する。
- 索引にない質問や最新の個別ページが必要な場合は、公式 `github.github.com/gh-aw` または索引に列挙された `raw.githubusercontent.com/github/gh-aw` URL を WebFetch で取得し、取得内容を推測で補わない。
- 公式資料とリポジトリ内の `.github/aw/instructions.md` が衝突する場合は、リポジトリ固有指示を優先する。
