---
# 同梱のoutput-styles.mdは参照用のリファレンス、このファイル自体はOutput Styleを実際に書く際のベストプラクティス集
name: writing-output-styles
description: Use when creating or editing a Claude Code output style (.claude/output-styles/*.md, ~/.claude/output-styles/*.md, or a plugin's output-styles/ directory) — choosing keep-coding-instructions, writing frontmatter, distinguishing output styles from CLAUDE.md/subagents/skills/--append-system-prompt, and switching styles via /config.
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
  version: 1.0.3
---

# Output Style作成のベストプラクティス

Output styleはシステムプロンプトを恒久的に書き換える機構で、CLAUDE.md・`--append-system-prompt`・サブエージェント・Skillとも役割が被りやすく、選ぶべき機構を間違えやすい。
ここでは**実際に書く際の手順とチェックリスト**をまとめる。組み込みスタイルの詳細・フロントマター全フィールド・類似機能との比較表は同梱の [output-styles.md](output-styles.md) を参照。

## 作成手順

1. **本当にoutput styleが適切か確認する** — 「プロジェクトの規約やコードベース知識を常に知っておいてほしい」なら[CLAUDE.md](https://code.claude.com/docs/en/memory)、「今回の起動1回だけ追加したい」なら`--append-system-prompt`、「スコープを分離した専用ヘルパーが欲しい」ならサブエージェント、「再利用可能な作業手順を持たせたい」ならSkill。**毎ターン恒常的に役割・トーン・出力形式を変えたい**場合だけoutput styleを選ぶ。判断に迷ったら output-styles.md の比較表を参照。
2. **既存で代用できないか確認する** — 組み込みの Proactive / Explanatory / Learning で足りないか、`~/.claude/output-styles/`・`.claude/output-styles/`に似た用途のスタイルが無いか確認する。
3. **配置場所を決める** — 個人用途なら`~/.claude/output-styles/`、このプロジェクト限定なら`.claude/output-styles/`、プラグイン配布なら`output-styles/`ディレクトリ。
4. **ファイル名（＝スタイル名）を決める** — フロントマターで`name`を指定しない限り、ファイル名（拡張子除く）がそのままスタイル名になる。
5. **`keep-coding-instructions`を判断する** — コーディング作業は続けつつ話し方・出力形式だけ変える（例: 説明の前に必ず図を出す）なら`true`にする。ライティングアシスタントやデータアナリストなど、そもそもソフトウェアエンジニアリングをしない用途なら省略する（`false`）。**ここを付け忘れると、変更範囲の絞り方・コメントの書き方・作業の検証方法といった組み込み指示が丸ごと失われる**。
6. **frontmatterと本文を書く** — `name`/`description`（`/config`ピッカーに表示される説明文）/`keep-coding-instructions`/（プラグイン配布限定の）`force-for-plugin`。本文はシステムプロンプトの末尾にそのまま追記される指示そのものなので、曖昧な希望ではなく具体的な指示として書く。
7. **保存して切り替える** — `/config` → **Output style** から選択する。反映は`/clear`か新規セッションから（システムプロンプトはセッション開始時に一度だけ読まれるため）。

## チェックリスト（ベストプラクティス）

- [ ] CLAUDE.mdとの役割分担ができている — プロジェクト規約・コードベース知識はCLAUDE.md、口調・役割・出力フォーマットの恒久的な変更はoutput style
- [ ] `--append-system-prompt`との役割分担ができている — 単発の追加ならこちら、毎ターン恒常的に効かせたいならoutput style
- [ ] サブエージェントとの役割分担ができている — 独自のシステムプロンプト・モデル・ツールを持つ別スコープのヘルパーが要るならサブエージェント。Output styleは**メイン会話にのみ**適用され、通常のサブエージェントには適用されない（[フォーク](https://code.claude.com/docs/en/sub-agents#fork-the-current-conversation)は親の会話をそのまま引き継ぐため例外）
- [ ] Skillとの役割分担ができている — 再利用可能な「作業手順」はSkill、話し方・出力形式そのものの変更はoutput style
- [ ] コーディング作業を続けるスタイルなのに`keep-coding-instructions: true`を書き忘れていないか
- [ ] `description`は`/config`ピッカーに表示される説明文として簡潔に書けているか
- [ ] `/output-style`コマンド（v2.1.73で非推奨・v2.1.91で削除済み）を前提にした案内をしていないか。`/config`または`outputStyle`設定の直接編集を案内する
- [ ] プラグイン配布で`force-for-plugin: true`を使う場合、それがユーザーの`outputStyle`設定を上書きする挙動だと理解した上で使っているか
- [ ] 変更後すぐに反映されないという相談には、`/clear`か新規セッションが必要（セッション開始時に一度だけ読まれる）と案内できているか

## 困ったときは

1. まず同梱の [output-styles.md](output-styles.md)（組み込み3スタイルの詳細、配置場所ごとの優先順位、フロントマター全フィールド、類似機能との比較表）を確認する。
2. それでも解決しない・挙動が期待と違う場合:
   - 変更が反映されない場合は`/clear`か新規セッションを試す（システムプロンプトはセッション開始時に一度だけ読まれる）
   - [Debug your configuration](https://code.claude.com/docs/en/debug-your-config)の手順で設定の優先順位や読み込み状況を確認する
3. デバッグしても原因不明、または output-styles.md 執筆時点から仕様が変わっている可能性がある場合は、**claude-code-docsスキル**で最新の公式ドキュメント（`code.claude.com`）を参照する。
