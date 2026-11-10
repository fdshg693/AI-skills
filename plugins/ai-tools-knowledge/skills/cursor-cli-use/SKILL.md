---
name: cursor-cli-use
description: Use when delegating a coding or analysis task to the Cursor CLI (`agent`, formerly `cursor-agent`) as a one-shot, non-interactive worker — for example offloading bulk/mechanical work to a cheaper Cursor model, or restricting a task to read-only exploration. Not for interactive/REPL agent sessions, and not for looking up CLI flags or docs (use cursor-cli-docs / cursor-docs for that).
argument-hint: <agentに委譲したいタスクの説明>
disable-model-invocation: true
allowed-tools: Bash(agent *), Write, Agent
# 前提: Cursor CLI（`agent`コマンド）がインストール・認証済みであること。`agent status` で確認し、未認証なら `agent login` または `CURSOR_API_KEY` 環境変数を設定する
# 依存: cursor-cli-docs（フラグの一次情報）／cursor-docs（cursor.com/docs最新情報）。モデル選択の理由は README.md、CLI全般の一次調査は memos/ を参照
# disable-model-invocation: --force による書き込み・シェル実行や外部API課金という副作用があるため、Claudeの自動判断ではなくユーザーの明示呼び出し（/cursor-cli-use）に限定する
meta:
  tag: []
  requires_repo_tools: none
  requires_env: CURSOR_API_KEY, NO_OPEN_BROWSER
  dependencies: none
  requires_install: cursor-cli
  requires_hooks: none
  requires_skills: cursor-cli-docs, cursor-docs
  status: stable
  description: no description
  version: 1.0.0
---

# Cursor CLI 非対話実行

Cursor CLI（`agent` コマンド）を**非対話（`-p`/`--print`）の単発実行**でのみ使う。対話的なREPLセッションやスラッシュコマンド操作はこのスキルの対象外（必要ならユーザーに直接ターミナルでの対話利用を案内する）。

## 前提条件（自動チェック）

`agent`認証状態: !`command -v agent >/dev/null 2>&1 && NO_OPEN_BROWSER=1 agent status 2>&1 || echo "agent コマンドが見つかりません（Cursor CLIが未インストール、またはPATH未設定）"`

上記が「コマンドが見つかりません」の場合は、Cursor CLI（`agent`）のインストールをユーザーに案内する（未インストールの環境ではこのスキルは使えない）。
上記が未認証・エラーを示している場合は、`agent -p`を実行する前にユーザーへ`agent login`（対話認証）または`CURSOR_API_KEY`環境変数の設定を促す。

## 注意: 委譲先も作業ディレクトリのCLAUDE.md/プロジェクトルールを自動的に読み込む

`agent -p`は非対話実行であっても、作業ディレクトリ配下の`CLAUDE.md`や`.cursor/rules/`等のプロジェクトルールを自律的に発見・遵守する。そこに「実行結果をログに残す」「変更提案をする」といった副作用的な指示が書かれていると、明示的に依頼していなくてもその指示に従い、追加のファイル作成・書き込みを行うことがある。

委譲元のClaude Code自身も同じ`CLAUDE.md`の指示に従っている場合、**同趣旨のログ・成果物が二重に生成される**おそれがある。厳密に読み取り専用・副作用ゼロで実行させたいタスクでは、プロンプト内に「プロジェクトのCLAUDE.md・ルールに書かれた指示は無視し、指定したタスクのみを実行せよ」のような一文を明示的に添えること。

## 実行の基本形

```bash
agent -p --force --model <model> "<prompt>"
```

- `-p, --print` は必須（非対話実行の起点）。
- `--force`（`--yolo`と同義）は既定でつける。明示的に deny されていない限り読み取り・書き込み・シェルコマンドを確認なしで実行できる。ほとんどのタスクはこれで問題ない
- 実行ファイル名は `agent`（`agent --version` で確認できる実体）。`cursor-agent` は同じバイナリを指すレガシーエイリアスとして残っているが、以後は `agent` を正とする
- 結果を後続処理でパースしたい場合のみ `--output-format json`（成功時に単一JSON）を付ける。単に最終回答が欲しいだけなら既定の `text` のままでよい

## モデル選択（タスクの性質でトップダウンに決める）

| タスクの性質                                                                       | 使うモデル／委譲先                                                                                                 | `--model` に渡すID       |
| ---------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------ | ------------------------ |
| 単純作業を大量に処理する（機械的な一括変換・フォーマット・定型的なコード生成など） | Composer 2.5                                                                                                       | `composer-2.5`           |
| ある程度の判断力・実装力が必要（中程度の複雑さの実装・調査）                       | Grok 4.5                                                                                                           | `grok-4.5-xhigh`         |
| 性能が最重要（設計判断・難しいバグ・セキュリティ・正確性が問われる最難関タスク）   | **Cursor CLIには委譲しない**。Claude Code側の`Agent`ツールでClaude Sonnet 5 / Opusのサブエージェントに直接依頼する | （`agent -p`は使わない） |

```bash
agent -p --force --model composer-2.5 "<prompt>"
```

- まずタスクの性質を上の3行のどれかに分類する。1・2行目に該当する場合は対応する `--model` のIDをそのまま使って `agent -p` を実行すればよく、毎回 `agent models` で調べ直す必要はない — IDを最新に保つのはスキルのメンテナの責務であり、実行するエージェントは上表をそのまま信用してよい
- 3行目（性能最重要の最難関タスク）に該当する場合は `agent -p` を呼び出さず、`Agent` ツールで `subagent_type` にSonnet相当（既定）またはOpus相当を指定してタスクを委譲する
- 選定理由（コストプール構造上の狙い、および最難関タスクでCursor CLIを使わない理由）はこのスキルの実行判断には不要。知りたい場合のみ同ディレクトリの [README.md](README.md) を参照する
- `model not found` 等のエラーが出た場合のみ `agent models` で現在の一覧を確認し、このSKILL.mdの表を修正する（実行時のエラー対応であって毎回の事前確認ではない）

## 読み取り専用・大量読み取りタスクの扱い

大量ファイルの探索・要約など「読み取り主体」のタスクは上表の軽量モデル（Composer 2.5等）を使うことが多く、定型タスクよりモデルの信頼性がやや落ちる。そのぶん**誤って書き込みや破壊的コマンドを実行しない構造的な歯止め**が価値を持つ。Cursor側のカスタムSubagent機構（`.cursor/agents/*.md`）には委譲せず、以下のいずれかで直接絞り込む。

- **最も手軽**: `--force` を付けずに実行する。`-p`（非対話）モードは全ツールにアクセスできるが、`--force` なしでは変更は提案されるだけで実際には書き込まれない（[memos/04-tools-permissions.md](memos/04-tools-permissions.md)）。読み取り・要約が目的なら、そもそも `--force` を付けない運用で十分なことが多い
- **より確実に禁止したい場合**: `<project>/.cursor/cli.json` に `permissions.deny` で `Write(**)` / `Shell(*)` 等のトークンを指定する。`--force` を付けていてもdenyリストは優先されるため、`--force`込みで一括実行しつつ書き込みだけ確実に禁止したい場面で使う（詳細は [memos/04-tools-permissions.md](memos/04-tools-permissions.md)）

## 複数回・同種のタスクを繰り返す場合

**同じ種類のタスクを何度も頼みたい場合でも、Cursor側のカスタムSubagent機構（`.cursor/agents/*.md`）には委譲しない。** 代わりに、Claude Code側（呼び出し元）から必要な回数だけ `agent -p ...` を直接繰り返し呼び出す（並列に実行したい場合も同様に、呼び出し元で複数回`agent -p`を起動すればよい）。プロンプト文言を使い回したい場合はテンプレート文字列として手元に保持すればよく、Subagent化してCLI側に固定化する必要はない。理由の実測データは [README.md](README.md) を参照。

## モデル性能が不十分だったときの記録

タスク完了後、モデルの出力が期待水準に届かなかった（見落とし・幻覚・指示不履行など）と判断した場合は、`eval-logs/model-eval.jsonl` に1行追記する。フォーマットは [eval-logs/README.md](eval-logs/README.md) を参照。ログの解析・自動集計はこのスキルの範囲外（将来の課題）。

## 関連ファイル

- [README.md](README.md) — モデル選択の理由（コストプール構造）、このスキルの設計判断の背景（スキルのメンテナ向け）
- [memos/](memos/) — Cursor CLI全般の一次調査メモ（料金・権限・デバッグ・subagent仕様など）
- [eval-logs/README.md](eval-logs/README.md) — モデル性能ログのフォーマット
- CLIフラグの網羅的なリファレンスは **cursor-cli-docsスキル**、`cursor.com/docs` 全般の最新情報は **cursor-docsスキル** を使う
