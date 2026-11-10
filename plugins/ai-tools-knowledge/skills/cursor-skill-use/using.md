# スキルを使う

Cursorでスキルを**利用する側**の知識。作り方は [authoring.md](authoring.md)、機構の詳細仕様は [reference.md](reference.md) を参照。

## 呼び出し方

スキルの発動は2通り。

- **自動発動**: Cursor起動時にスキルが発見・登録され、Agentがコンテキストから関連性を判断して適用する。判断材料は各スキルの `description`
- **手動発動**: Agentチャットで `/` を入力し、スキル名を検索して選択する（`/skill-name`）

`disable-model-invocation: true` が設定されたスキルは自動発動せず、`/skill-name` で明示呼び出ししたときだけコンテキストに含まれる（従来のスラッシュコマンド相当の挙動）。

## 組み込みスキル

Cursor標準搭載のスキル（Cursorが管理し、自作スキルと並んで表示される）:

| スキル                    | 概要                                                                                |
| ------------------------- | ----------------------------------------------------------------------------------- |
| `/automate`               | スケジュール・Slackメッセージ・GitHubイベント等をトリガーにCursor Automationsを作成 |
| `/babysit`                | PRを監視し、フィードバック・コンフリクト・失敗したチェック・フォローアップに対応    |
| `/canvas`                 | 会話の横にレンダリングされる対話的Reactアーティファクトを作成                       |
| `/create-hook`            | Cursor hooksを作成し `hooks.json` を更新                                            |
| `/create-rule`            | 適切なスコープと指示を持つCursorルールを作成                                        |
| `/create-skill`           | Agent Skills（構造と `SKILL.md`）を作成                                             |
| `/create-subagent`        | 役割を絞ったカスタムsubagentと委譲指示を作成                                        |
| `/cursor-blame`           | AIが書いた変更とその元プロンプトを調査                                              |
| `/loop`                   | プロンプトやスキルを指定間隔で繰り返し実行                                          |
| `/migrate-to-skills`      | 対象となる動的ルールとスラッシュコマンドをAgent Skillsに変換                        |
| `/review`                 | 適切なコードレビューagentを選択して実行                                             |
| `/review-bugbot`          | Bugbotでバグ・リグレッションの可能性をレビュー                                      |
| `/review-security`        | Security Reviewでセキュリティ脆弱性をレビュー                                       |
| `/sdk`                    | Cursor SDKでアプリケーション・統合を構築                                            |
| `/shell`                  | 与えたテキストをリテラルなシェルコマンドとして実行                                  |
| `/split-to-prs`           | 大きな変更を小さなPRに分割                                                          |
| `/statusline`             | Cursor CLIのステータスラインを設定                                                  |
| `/update-cli-config`      | `~/.cursor/cli-config.json` のCursor CLI設定を更新                                  |
| `/update-cursor-settings` | 適切なCursor/VS Code設定を特定して更新                                              |

`/` で名前を選べばどれでも実行できる。リクエストが明確に一致する場合はAgentが自動で使うものもある。

## 確認・管理（Customize画面）

- サイドバーの **Customize** → **Skills** で、発見されたスキルを一覧できる
- プラグインやプロジェクトからインストールされたスキルは、ルールと並んで **Agent Decides** セクションに表示される
- ルールは **Always** / **Agent Decides** / **Manual** を切り替えられる。スキルは `/skill-name` で手動呼び出しも可能

## GitHubからインストール

1. サイドバーの **Customize** を開く
2. **Rules** に移動し **Add Rule** をクリック
3. **Remote Rule (GitHub)** を選択
4. GitHubリポジトリのURLを入力

## ルール・スラッシュコマンドからの移行（`/migrate-to-skills`）

組み込みの `/migrate-to-skills`（Cursor 2.4〜）が、既存の動的ルールとスラッシュコマンドをスキルに変換する。

変換されるもの:

- **動的ルール**: 「Apply Intelligently」設定のルール（`alwaysApply: false` または未指定、かつ `globs` パターンなし）→ 通常のスキルへ
- **スラッシュコマンド**: ユーザーレベル・ワークスペースレベル両方 → `disable-model-invocation: true` 付きのスキルへ（明示呼び出しの挙動を維持）

変換されないもの:

- `alwaysApply: true` や `globs` 指定のあるルール（発動条件が明示的でスキルの挙動と異なるため）
- ユーザールール（ファイルシステム上に存在しないため）

手順: Agentチャットで `/migrate-to-skills` を実行 → Agentが対象を特定して変換 → `.cursor/skills/` に生成されたスキルをレビューする。
