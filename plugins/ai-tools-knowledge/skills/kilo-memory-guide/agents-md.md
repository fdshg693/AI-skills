# AGENTS.md 詳細

出典: https://kilo.ai/docs/customize/agents-md

## 用途

AGENTS.mdは、プロジェクト固有のコーディング規約、設計知識、テスト方針、安全制約をAI agentへ伝える標準Markdownファイル。Kilo専用に閉じず、対応する他ツールとも共有しやすい。

## 配置

- プロジェクトルートの`AGENTS.md`: プロジェクト全体
- サブディレクトリの`AGENTS.md`: そのディレクトリ向けの補足
- `~/.config/kilo/AGENTS.md`: 全プロジェクト向けのグローバル指示
- `AGENT.md`: `AGENTS.md`のfallbackとして公式ページに記載されている

公式ページはファイル名を大文字として扱うことを推奨している。ケース依存の環境差を避けるため、常に`AGENTS.md`を使う。

## ロードの考え方

ルートの指示はタスク開始時に読み込まれる。サブディレクトリの指示は、agentがそのディレクトリのファイルをReadしたときに動的に発見され、system reminderとして追加される。サブディレクトリの内容はルートを繰り返さず補足にする。

公式ページの優先順位表では、概ねagent prompt、project instructions、project AGENTS.md、global instructionsの順で整理されている。実際の競合はクライアントや設定変更の影響を受け得るため、同じ内容を複数箇所に重複させない。

## 書き方

```markdown
# Project Rules

## Code Style

- Use the repository formatter.
- Keep public APIs backward compatible.

## Validation

- Run the documented test command after code changes.

## Security

- Never read or commit secrets.
```

短く、検証可能で、優先順位が明確な規則にする。曖昧な「良いコードを書く」より、対象・条件・期待動作を明記する。

## 保護

公式ページではAGENTS.mdとAGENT.mdはwrite-protectedと説明されている。AIに編集を任せる場合も、変更内容を確認して明示的に承認する運用にする。
