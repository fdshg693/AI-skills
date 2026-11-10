# Cursorのメモリ（Rules / AGENTS.md）詳細

<!-- 2026-07-20 時点の https://cursor.com/docs/rules.md および https://cursor.com/help/customization/rules.md に基づく。更新時は references/ のスナップショットも差し替え、cursor-docs で最新を確認すること -->

LLMは補完間で記憶を持たない。Rules / `AGENTS.md` はプロンプト先頭に注入される**永続・再利用可能なコンテキスト**である。強制力のある設定ではない。

## 機構の対応表

| 機構          | 置き場所                                          | 書く人          | 適用                                         | 向いている内容                           |
| ------------- | ------------------------------------------------- | --------------- | -------------------------------------------- | ---------------------------------------- |
| Project Rules | `.cursor/rules/**/*.mdc`                          | 人間（Git共有） | frontmatterで制御                            | ドメイン知識・パス限定規約・テンプレ参照 |
| AGENTS.md     | プロジェクトルートまたは任意サブディレクトリ      | 人間（Git共有） | 常時（ネスト時は該当ツリー）                 | シンプルなプロジェクト指示               |
| CLAUDE.md     | 同上（Cursorは AGENTS.md と同様に読む）           | 人間            | **常時**（frontmatterの alwaysApply は無視） | Claude Code互換の指示をCursorでも共有    |
| User Rules    | Customize → Rules（ローカル設定。プロジェクト外） | 人間（個人）    | 全プロジェクトの Agent                       | 文体・個人の好み                         |
| Team Rules    | Cursorダッシュボード                              | 管理者          | チーム全体（Enforce可）                      | 組織ポリシー・コンプライアンス           |

優先順位（衝突時）: **Team Rules → Project Rules → User Rules**。適用されるものはマージされ、先のソースが優先される。

CLI（`agent`）もエディタと同じ rules システムを使う。CLIはプロジェクトルートの `AGENTS.md` と `CLAUDE.md` も `.cursor/rules` と併せて読む。

## Project Rules（`.cursor/rules/*.mdc`）

- 拡張子は **`.mdc` 必須**。`.cursor/rules/` 内の素の `.md` は rules システムに無視される（メタデータがないため）
- サブフォルダで整理可能（例: `frontend/components.mdc`）。発見はフォルダ走査。同名ファイルが別フォルダにあってもパス全体で識別され、条件が合えば両方適用される
- UI: `/create-rule`、または Customize → Rules → Add Rule。コマンドパレットの "New Cursor Rule" でも可
- GitHubから Remote Rule を取り込むと `.cursor/rules/imported/<repoName>/` に配置される

### Frontmatter と適用タイプ

UIの type ドロップダウンは次の3フィールドを変える。

| Rule Type               | 挙動                                       |
| ----------------------- | ------------------------------------------ |
| Always Apply            | 毎チャットに含める                         |
| Apply Intelligently     | description を見て Agent が関連時に取る    |
| Apply to Specific Files | マッチするファイルがコンテキストにあるとき |
| Apply Manually          | チャットで `@rule-name` したときだけ       |

| `alwaysApply` | `description` | `globs` | 実挙動                                       |
| ------------- | ------------- | ------- | -------------------------------------------- |
| `true`        | —             | —       | 常時。globs / description は無視             |
| `false`       | —             | あり    | マッチファイルがコンテキストにあると自動添付 |
| `false`       | あり          | なし    | Agentが description で判断して取り込む       |
| `false`       | なし          | なし    | `@` 言及時のみ                               |

```markdown
---
description: TypeScript conventions for this project
globs: "**/*.ts,**/*.tsx"
alwaysApply: false
---

# TypeScript

- Prefer `unknown` over `any` at API boundaries
- ...
```

`globs` はカンマ区切りで複数可（例: `docs/**/*.md, docs/**/*.mdx`）。

### ルール本文の書き方

- 500行未満。大きいルールは関心ごとに分割
- 曖昧語を避け、内部ドキュメントのように具体的に書く
- コード全文や巨大スタイルガイドのコピーは避け、`@filename.ts` で参照する（鮮度とトークンのため）
- Agentが同じミスを繰り返したときに足す。先回りしすぎない
- リンタで強制できることはルールに書かない。よくあるツール知識（npm, git 等）の羅列もしない

### 効く範囲・効かない範囲

- **効く**: Agent（Chat）
- **効かない**: Cursor Tab、Inline Edit（Ctrl+K）。User Rules も Inline Edit には使われない

## AGENTS.md

プレーン Markdown。メタデータなし。構造化ルールが不要なシンプルなケース向け。

```text
project/
  AGENTS.md                 # 全体
  frontend/
    AGENTS.md               # frontend 配下で追加適用
  backend/
    AGENTS.md
```

- ルートとサブディレクトリの両方をサポート
- ネスト分は親と**結合**され、より具体的な（深い）指示が優先される
- 条件付き適用が必要なら `.cursor/rules/*.mdc` を使う

## CLAUDE.md（Cursorでの扱い）

Cursorは `CLAUDE.md` を `AGENTS.md` と同じように読む。ルートに置けば自動で拾われる。

- **常時適用**。`alwaysApply` frontmatter があっても無視される（Claude Code互換のため）
- 条件付きにしたい内容は `.cursor/rules/*.mdc` へ

このリポジトリのように `CLAUDE.md` が `@./AGENTS.md` インポートだけの場合、Cursor側は両方読まれる点に注意（重複しうる）。ツール横断で1ソースにしたいなら `AGENTS.md` に実体を置き、Claude Code側は `@AGENTS.md`、Cursorは `AGENTS.md` を正とする運用が分かりやすい。

## User Rules

- Customize → Rules（または Settings → Rules）に書くグローバル好み
- プロファイルエクスポートに含まれない。マシン移行時は再入力か Project Rules へ移す
- 例: 「簡潔に返す。不要な繰り返しを避ける」

## Team Rules

- Team / Enterprise。ダッシュボード（https://cursor.com/dashboard/team-content）で管理
- 自由形式テキスト（Project Rulesのフォルダ構造は使わない）。glob でファイルスコープ可
- **Enforce** するとメンバーが Customize でオフにできない
- AIガイダンスだけを唯一のセキュリティコントロールにしない

## レガシー `.cursorrules`

ルートの `.cursorrules` はレガシーで非推奨予定。移行:

1. New Cursor Rule で `.mdc` を作る
2. 内容をコピーし **Always Apply** にする
3. `.cursorrules` を削除する

## Skills との境界

|      | Rules / AGENTS.md                                                                  | Skills                                     |
| ---- | ---------------------------------------------------------------------------------- | ------------------------------------------ |
| 役割 | 常時〜条件付きの**指示・規約**                                                     | 手順・スクリプト付きの**専門ワークフロー** |
| 発動 | alwaysApply / globs / description / `@`                                            | description による自動、または `/skill`    |
| 移行 | Apply Intelligently（`alwaysApply: false`・globsなし）は `/migrate-to-skills` 候補 | —                                          |

Skillsの作成・配置は **cursor-skill-use**。Rules に長い手順やスクリプトを詰めない。

## トラブルシューティング

| 症状                              | 確認すること                                                                                     |
| --------------------------------- | ------------------------------------------------------------------------------------------------ |
| ルールが効かない                  | 適用タイプ。Intelligent なら description。Specific Files なら globs が参照ファイルにマッチするか |
| `.md` を `.cursor/rules` に置いた | 無視される。`.mdc` にするか `AGENTS.md` を使う                                                   |
| Tab / Ctrl+K で効かない           | 仕様。Rulesは Agent のみ                                                                         |
| 同名ルールが複数                  | フルパスで別物。条件が合えば両方適用                                                             |
| TeamとProjectが矛盾               | Teamが優先                                                                                       |

## 作成時の最小手順（エージェント向け）

1. スコープ（User / Project / nested AGENTS / Team案内）を確認。未指定なら「常時かファイル限定か」を聞く
2. Project かつ条件付き → `.cursor/rules/<topic>.mdc` を作成し frontmatter を埋める
3. Project かつ常時・単純 → ルート `AGENTS.md` を新規または追記（既存方針を壊さない）
4. 保存後、必要なら Customize → Rules で表示・タイプを確認するようユーザーに伝える

## 一次情報

- [references/rules.md](references/rules.md) — https://cursor.com/docs/rules.md
- [references/help-rules.md](references/help-rules.md) — https://cursor.com/help/customization/rules.md
- 最新確認は **cursor-docs** スキル経由で同URLを再取得
