# eval-logs

`cursor-cli-use`スキル経由でCursor CLI（`agent`）にタスクを委譲した際、モデルの性能が期待水準に届かなかったと判明した場合に追記する記録。分析・自動集計の仕組みは今回のタスクの範囲外（未整備）。人間が後から`grep`/`jq`等で振り返るための素材として蓄積する。

## フォーマット

`model-eval.jsonl` に1エントリ1行のJSON（[JSON Lines](https://jsonlines.org/)）を追記する。既存内容の読み込み・書き換えは不要で、末尾に1行足すだけでよい。ファイルが無ければ新規作成する。

```json
{
  "timestamp": "2026-07-09T12:34:56Z",
  "model": "composer-2.5",
  "tier": "bulk",
  "task_summary": "Summarize each API controller docstring",
  "problem": "Missed 3 of 12 files, hallucinated a nonexistent function",
  "prompt_excerpt": "Use the bulk-reader subagent to summarize every controller in src/api/**",
  "suggested_model": "grok-4.5"
}
```

| フィールド        | 必須 | 説明                                                                                          |
| ----------------- | ---- | --------------------------------------------------------------------------------------------- |
| `timestamp`       | Yes  | ISO 8601 (UTC)。例: `date -u +%Y-%m-%dT%H:%M:%SZ`の出力                                       |
| `model`           | Yes  | 実際に使ったモデルID（不明ならdisplay nameでも可）                                            |
| `tier`            | Yes  | `SKILL.md`のモデル選択表でどの行を想定していたか。`bulk` / `moderate` / `critical` のいずれか |
| `task_summary`    | Yes  | 何を頼んだかの一文要約                                                                        |
| `problem`         | Yes  | 具体的に何が不十分だったか（見落とし・幻覚・指示不履行・フォーマット崩れなど）                |
| `prompt_excerpt`  | No   | 実際に渡したプロンプトの抜粋                                                                  |
| `suggested_model` | No   | 次回以降に試すべきと考えたモデル                                                              |

## 範囲外

- ログの解析・集計・可視化ツールは今回整備しない。傾向が見えてきたら別途スキル・スクリプトとして追加を検討する
- ログファイルのローテーション・肥大化対策も範囲外
