# Output styleの仕組み

> 参考文献: [Output styles](https://code.claude.com/docs/en/output-styles)

## 目次

- [基本概要](#基本概要)
- [組み込みoutput style](#組み込みoutput-style)
- [切り替え方](#切り替え方)
- [設定ファイルの書き方](#設定ファイルの書き方)
  - [配置場所](#配置場所)
  - [フロントマターの全フィールド一覧](#フロントマターの全フィールド一覧)
- [動作の仕組み](#動作の仕組み)
- [類似機能との比較](#類似機能との比較)
- [参考文献](#参考文献)

## 基本概要

Output styleは、Claudeが**何を知っているか**ではなく**どう応答するか**を変える機構。システムプロンプトを書き換えて、役割・トーン・出力形式を設定する。

毎ターン同じ口調・フォーマットを頼み直している場合や、Claude Codeにソフトウェアエンジニアリング以外の役割（ライティングアシスタント、データアナリスト等）をさせたい場合に使う。

カスタムoutput styleは、システムプロンプトに独自の指示を追加し、Claude Codeの組み込みソフトウェアエンジニアリング指示を残すかどうかを選べる。

- **残す（`keep-coding-instructions: true`）**: 話し方は変えるが引き続きコーディング作業をする場合（例: 説明の前に必ず図を出す）
- **残さない（省略・`false`）**: そもそもソフトウェアエンジニアリングをしない場合（例: ライティングアシスタント、データアナリスト）

プロジェクトの規約・コードベース知識を伝えたい場合はoutput styleではなく[CLAUDE.md](https://code.claude.com/docs/en/memory)を使う。

## 組み込みoutput style

**Default**が既存のシステムプロンプトそのもの（ソフトウェアエンジニアリングタスクの効率的な遂行を目的とする）。加えて3つの組み込みスタイルがある。

| 名前            | 内容                                                                                                                                                                                |
| :-------------- | :---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **Proactive**   | 即座に実行し、日常的な判断では止まらず妥当な仮定を置いて進める。auto modeより強い自律実行指示だが、権限モード自体は変えないためツール実行前の権限確認プロンプトは引き続き表示される |
| **Explanatory** | ソフトウェアエンジニアリングタスクを進めつつ、合間に教育的な「Insights」を挟む。実装判断やコードベースのパターンの理解を助ける                                                      |
| **Learning**    | Explanatoryに加えて、Claudeが自分でコードを書かず、戦略的に小さな一部をユーザー自身に実装させる。コード中に`TODO(human)`マーカーを挿入する                                          |

## 切り替え方

`/config` → **Output style** から選ぶ。選択内容はプロジェクトローカルの`.claude/settings.local.json`に保存される。

設定ファイルの`outputStyle`フィールドを直接編集してもよい:

```json
{
  "outputStyle": "Explanatory"
}
```

> 独立した`/output-style`コマンドはv2.1.73で非推奨、v2.1.91で削除済み。`/config`か`outputStyle`設定の直接編集を使う。

Output styleはシステムプロンプトの一部であり、**セッション開始時に一度だけ**読み込まれる。変更を反映するには`/clear`か新規セッションが必要。

## 設定ファイルの書き方

カスタムoutput styleはMarkdownファイル1つ。フロントマターでメタデータを、本文でシステムプロンプトに追記する指示を書く。

```markdown
---
name: Diagrams first
description: Lead every explanation with a diagram
keep-coding-instructions: true
---

When explaining code, architecture, or data flow, start with a Mermaid diagram showing the structure, then explain in prose.

## Diagram conventions

Use `flowchart TD` for control flow and `sequenceDiagram` for request paths. Keep diagrams under 15 nodes.
```

### 配置場所

ファイル名（拡張子除く）がそのままスタイル名になる。フロントマターで`name`を指定すればそちらが優先される。

| 配置場所                                                | 適用範囲                   |
| :------------------------------------------------------ | :------------------------- |
| `~/.claude/output-styles`                               | 個人（全プロジェクト横断） |
| `.claude/output-styles`                                 | プロジェクト限定           |
| managed settingsディレクトリ内の`.claude/output-styles` | 組織全体（managed policy） |
| プラグインの`output-styles/`ディレクトリ                | プラグインが有効な範囲     |

プロジェクト用は、作業ディレクトリからリポジトリルートに向かう経路上にある**すべての**`.claude/output-styles/`から読み込まれる。同名スタイルが複数箇所にある場合、v2.1.178以降は作業ディレクトリに近い方が使われる。

### フロントマターの全フィールド一覧

| フィールド                 | 用途                                                                                                                                                                                                            | デフォルト |
| :------------------------- | :-------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | :--------- |
| `name`                     | スタイル名（省略時はファイル名）                                                                                                                                                                                | ファイル名 |
| `description`              | `/config`ピッカーに表示される説明文                                                                                                                                                                             | なし       |
| `keep-coding-instructions` | Claude Codeの組み込みソフトウェアエンジニアリング指示を残すか                                                                                                                                                   | `false`    |
| `force-for-plugin`         | プラグイン提供のoutput style専用。プラグイン有効時に、ユーザーが選ばなくても自動適用する。ユーザーの`outputStyle`設定を上書きする。複数の有効プラグインがこれを設定した場合は最初にロードされたものが優先される | `false`    |

## 動作の仕組み

- すべてのoutput styleは、独自の指示がシステムプロンプトの末尾に追加される
- すべてのoutput styleは、会話中もその指示に従うようリマインダーを発生させる
- `keep-coding-instructions: true`を指定しない限り、カスタムoutput styleは**Claude Codeの組み込みソフトウェアエンジニアリング指示（変更範囲の絞り方・コメントの書き方・作業の検証方法など）を含めない**

Output styleは**メイン会話にのみ**適用される。[サブエージェント](https://code.claude.com/docs/en/sub-agents#what-loads-at-startup)は自分自身のシステムプロンプトで動くため、output styleの影響を受けない。例外は[フォーク](https://code.claude.com/docs/en/sub-agents#fork-the-current-conversation)で、親の会話のシステムプロンプトをそのまま引き継ぐため影響を受ける。

トークン使用量への影響はスタイルによる。システムプロンプトへの追記は入力トークンを増やすが、セッション内2回目以降のリクエストからはprompt cachingが効いてコストが下がる。組み込みのExplanatory・Learningは設計上Defaultより長い応答を生成するため出力トークンが増える。カスタムスタイルの出力トークン量は、書いた指示の内容次第。

## 類似機能との比較

複数の機能がClaude Codeの挙動をカスタマイズできるが、役割が異なる。Output styleはシステムプロンプトを直接書き換えて**毎ターン**適用される。他の機能はデフォルトのシステムプロンプトを変えずに指示を追加するか、特定のタスクにスコープする。

| 機能                                                                     | 仕組み                                                                   | 使いどころ                                                   |
| :----------------------------------------------------------------------- | :----------------------------------------------------------------------- | :----------------------------------------------------------- |
| Output styles                                                            | システムプロンプトを書き換える                                           | 毎ターン、異なる役割・トーン・デフォルトの出力形式にしたい   |
| [CLAUDE.md](https://code.claude.com/docs/en/memory)                      | システムプロンプトの後にユーザーメッセージとして追加される               | プロジェクトの規約・コードベース知識を常に知っておいてほしい |
| `--append-system-prompt`                                                 | 何も削らずシステムプロンプトに追記する                                   | 1回の起動限定で一時的に追加したい                            |
| [Agents（サブエージェント）](https://code.claude.com/docs/en/sub-agents) | 独自のシステムプロンプト・モデル・ツールを持つサブエージェントを起動する | スコープを分離した専用ヘルパーが欲しい                       |
| [Skills](https://code.claude.com/docs/en/skills)                         | 呼び出された時・関連性がある時にタスク固有の指示をロードする             | 再利用可能な作業手順がある                                   |

## 参考文献

- Output styles全般（本記事の主な情報源）: https://code.claude.com/docs/en/output-styles
- 設定ファイルと`outputStyle`フィールド: https://code.claude.com/docs/en/settings
- 権限モードとProactiveスタイルの比較: https://code.claude.com/docs/en/permission-modes
- プラグインでのoutput style配布: https://code.claude.com/docs/en/plugins
- 反映されない場合の切り分け: https://code.claude.com/docs/en/debug-your-config
