# authoring-playwright-agents（メンテナ向け）

Playwright 特化エージェントを書くための一次情報を、microsoft/playwright の upstream からミラーするスキル。
実行時の判断・手順は [SKILL.md](SKILL.md) と [agent-definition-format.md](agent-definition-format.md)。ここは設計意図のみ。

## なぜ upstream `main` を根拠にするのか

手元にインストールされた Playwright や、どこかにある playwright のチェックアウトは upstream `main` より古いことがある。
判断の根拠は常に `output/`（`main` のスナップショット）に置き、手元と差がある場合は差として報告させる。

このスキルはもともと microsoft/playwright のクローンの中で育てたもので、fdshg693/AI に移すときに
クローンの `.claude/` への依存を外した。

## ファイル構成

| パス                                     | 位置づけ                                                            |
| ---------------------------------------- | ------------------------------------------------------------------- |
| `SKILL.md`                               | 実行時のルーター。参照先の対応表のみ                                |
| `agent-definition-format.md`             | 定義の書き方・ツール変換・作成手順                                  |
| `download_playwright_agents.py`          | スナップショット取得。`SKILL.md` の `` !`...` `` で起動時に必ず走る |
| `output/`                                | 生成物。手で編集しない。`--force` で作り直せる                      |
| `output/summary.md`, `output/_meta.json` | スクリプトが生成する索引とメタ（取得日時・元パス一覧）              |

## 取得対象を増やすとき

`download_playwright_agents.py` の定数を編集する。

- `DIR_SOURCES` — `(repo ディレクトリ, output サブディレクトリ, 拾う拡張子)`。再帰的に列挙する
- `FILE_SOURCES` — `(repo ファイルパス, output 相対パス)`。単発ファイル用

追加後は `--force` で取得し、`output/summary.md` に出ることと、`SKILL.md` の対応表に行を足したかを確認する。
`output/` 内で列挙から外れたファイルは次回取得時に自動削除される（`remove_stale_outputs`）。

## 運用上の注意

- 鮮度は 7 日（`FRESHNESS`）。公式定義は Playwright のリリース単位で動くので、これ以上短くしても `gh` API を無駄に叩くだけ
- `gh api` は Contents API を 1 ファイル 1 回呼ぶ。取得対象を大きく増やすとレート制限に当たりやすい（未認証は 60 req/h）
- スクリプトは標準ライブラリのみ。`uv run` で起動する（PEP 723 の空の依存宣言付き）
