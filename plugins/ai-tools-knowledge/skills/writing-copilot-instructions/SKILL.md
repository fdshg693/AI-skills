---
name: writing-copilot-instructions
description: Use when creating, editing, reviewing, or troubleshooting GitHub Copilot instruction files, including `.github/copilot-instructions.md`, `.github/instructions/**/*.instructions.md`, and `AGENTS.md`, for VS Code, GitHub.com cloud agent, Copilot code review, or Copilot CLI. Covers host and scope selection, Markdown/frontmatter, path globs, concise repository guidance, and verification. Do not use for `.prompt.md` prompt files or Agent Skills unless the task is specifically about choosing between those mechanisms.
meta:
  tag: []
  requires_repo_tools: none
  requires_env: none
  dependencies: none
  requires_install: none
  requires_hooks: none
  requires_skills: github-copilot-docs, vscode-copilot-docs
  status: stable
  description: no description
  version: 1.0.2
---

# GitHub Copilot instruction ファイルの設計・作成

GitHub Copilot にリポジトリの前提、開発規約、ビルド・テスト手順を伝える instruction ファイルを、対象ホストと適用範囲に合わせて作成・レビューする。対象は GitHub Copilot の instruction 仕様であり、Claude Code の `CLAUDE.md` や Codex の指示仕様をそのまま流用しない。

## 1. 先に対象ホストと機構を決める

依頼が曖昧なら、既存ファイル・配置・利用場所から推定し、推定した対象を作業報告に明記する。仕様が変わり得るため、作成前に次の関連スキルの手順で公式ドキュメントを確認する。

- GitHub.com、cloud agent、code review、Copilot CLI: [github-copilot-docs](../github-copilot-docs/SKILL.md)
- VS Code の Chat / Agent mode: [vscode-copilot-docs](../vscode-copilot-docs/SKILL.md)

| 目的                             | 主なファイル                                  | 適用範囲・注意                                                                                                                                                                                                    |
| -------------------------------- | --------------------------------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| リポジトリ全体の常時ルール       | `.github/copilot-instructions.md`             | `.github` はリポジトリまたは VS Code workspace のルートに置く。Markdown の自然言語で記述する。                                                                                                                    |
| 言語・ディレクトリ別ルール       | `.github/instructions/<name>.instructions.md` | YAML frontmatter の `applyTo` に glob を指定する。VS Code では既定の `.github/instructions` 以下を再帰的に探索する。GitHub.com では現在 cloud agent と code review が path-specific instructions をサポートする。 |
| エージェント向けの階層的な指示   | `AGENTS.md`                                   | リポジトリ内の適切なディレクトリに置く。Copilot が作業する場所に最も近いファイルを優先する。複数 AI ツールで共有する場合に選ぶ。                                                                                  |
| 一度の作業を再利用するプロンプト | `*.prompt.md`                                 | instruction ではない。常時適用ではなく、タスク開始時に呼び出すテンプレートが目的ならこちらを選ぶ。                                                                                                                |
| 特定分野の手順・能力             | Agent Skill                                   | 長い手順、スクリプト、専門知識が必要な場合に選ぶ。短い常時ルールを Skill に置き換えない。                                                                                                                         |

`CLAUDE.md` と `GEMINI.md` は他のエージェントとの互換性が必要な場合だけ検討する。対象ホストが解釈するかを公式ドキュメントで確認し、同じルールを複数ファイルへ無批判に複製しない。

## 2. リポジトリを調査して事実だけを抽出する

作成前に、既存の instruction、`AGENTS.md`、README、CONTRIBUTING、プロジェクト定義、CI workflow、lint/format 設定、スクリプト、テスト設定を確認する。次を実行する場合はリポジトリの実態に合わせてコマンドを選ぶ。

1. リポジトリの目的、主要なディレクトリ、言語、framework、runtime を確認する。
2. bootstrap、依存関係のインストール、build、test、lint、format、run の実行方法と順序を特定する。
3. コマンドの実行ディレクトリ、必要な runtime version、環境変数、サービス、既知の workaround、成功条件を確認する。
4. 変更時に守る architecture、公開 API、生成コード、migration、互換性、セキュリティ上の制約を抽出する。
5. 既存の指示の重複・矛盾・古いコマンドを確認する。

存在を確認していないコマンド、version、ディレクトリ、規約を推測して書かない。標準 formatter や linter がすでに強制するだけの自明な規則より、エージェントが探索や失敗を減らせる非自明な情報を優先する。

## 3. instruction の本文を書く

リポジトリ全体用の `.github/copilot-instructions.md` は、次の順に短く自己完結させる。

1. **Repository overview** — 何を提供するリポジトリか、主要技術、対象 runtime。
2. **Project layout** — 主要な source、test、docs、生成物、変更してはいけない領域。
3. **Development workflow** — bootstrap から build、test、lint、run までの実際のコマンドと順序。
4. **Conventions** — 命名、設計、依存関係、エラー処理など、既存コードに根拠があるルール。
5. **Validation** — 変更後に必ず実行する検証と、失敗時に確認する場所。
6. **Safety and boundaries** — secrets をコミットしない、破壊的操作や migration の扱い、互換性の制約。

各ルールは命令形で一つの判断に絞る。「なぜその規則があるか」を必要に応じて添え、望ましい例と避ける例を短いコードで示す。タスク固有の issue の解決策、頻繁に変わる一時情報、秘密情報、根拠のない一般論は入れない。cloud agent 向けの repository-wide instructions は特に短く保ち、目安として 2 ページ以内に収める。

例:

```markdown
# Repository guidance

This repository provides <verified purpose> using <verified stack and runtime>.

## Workflow

- Run `<bootstrap command>` from the repository root when dependencies are missing.
- Run `<test command>` after changing application code; it must pass before opening a PR.
- Run `<lint command>` before submitting changes.

## Conventions

- Put <kind of code> in `<verified directory>` because <short reason>.
- Prefer <existing pattern>; do not introduce <avoided pattern>.

## Boundaries

- Do not commit secrets or generated files under `<verified path>`.
- For <risky operation>, explain the impact and verify the result before continuing.
```

## 4. path-specific instructions を正しく分割する

言語、framework、frontend/backend、test、documentation などでルールが変わる場合だけ `.github/instructions` に分割する。ファイル名は目的を表す `<name>.instructions.md` とし、対象範囲を狭くして不要な instruction の混入を防ぐ。

```markdown
---
name: TypeScript and React conventions
description: Conventions for TypeScript and React source files
applyTo: "**/*.ts,**/*.tsx"
---

# TypeScript and React

- Follow the repository's existing component and state-management pattern.
- Apply the general rules from [the repository instructions](../copilot-instructions.md).
- Run `<verified test command>` for affected code.
```

`applyTo` は workspace root からの glob として、実際のファイルに一致するように確認する。例えば `src/*.py` は `src` 直下だけ、`src/**/*.py` は下位ディレクトリも対象、`**/*.ts,**/*.tsx` は TypeScript 系全体を対象にする。対象がない広すぎる glob や、意図せず test・生成物まで含む glob は避ける。

GitHub.com の path-specific instructions で cloud agent と code review の片方だけを対象にする必要がある場合は、公式仕様でサポート状況を確認したうえで `excludeAgent: "code-review"` または `excludeAgent: "cloud-agent"` を使う。VS Code 専用の frontmatter と GitHub.com 専用の frontmatter を混同しない。

## 5. 検証する

作成・編集後、次を確認してから完了とする。

- ファイル名と場所が対象ホストの仕様に一致する。
- `.instructions.md` の YAML frontmatter が閉じており、`applyTo` が意図した glob である。VS Code では `applyTo` がないファイルは自動適用されず、手動添付用になる。
- `copilot-instructions.md` はリポジトリ全体のルールだけを含み、path-specific file と重複・矛盾しない。
- 記述した command、path、version、設定名が実際に存在し、記述順に実行できる。
- 代表的な対象ファイルを選び、どの instruction が適用されるべきかを glob と既存ファイルから確認する。
- VS Code では Chat の References または customization diagnostics で読み込まれたファイルを確認する。inline suggestions は custom instructions の対象外なので、適用確認に使わない。
- GitHub.com では repository を Chat に添付して参照一覧を確認し、cloud agent / code review の path-specific 対応範囲と設定を確認する。
- instruction に書かれた検証 command を実行し、失敗した場合は失敗を隠さず、原因と代替手順を本文または報告に残す。

複数ファイルが同時に適用される環境では、適用順を前提にしない。個人・repository・organization の instruction が重なる場合も、競合を避けるように役割を分け、同じルールを異なる優先度の場所へ複製しない。

## 6. 機構を取り違えない

- 「すべての chat に適用したい」なら repository-wide instruction を使う。
- 「特定のファイル種別だけに適用したい」なら `*.instructions.md` と `applyTo` を使う。
- 「毎回呼び出す作業テンプレート」が目的なら `.prompt.md` を使う。
- 「特定タスクの詳細な手順、補助資料、スクリプト」が目的なら Agent Skill を使う。
- 「実行時のツール制御・検証・policy enforcement」が目的なら hooks、設定、または該当ホストの機構を調査する。

最終報告では、作成・変更したファイル、対象ホスト、適用範囲、実行した検証、未確認の仕様や既知の制限を明記する。
