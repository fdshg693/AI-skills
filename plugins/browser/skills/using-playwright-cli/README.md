# using-playwright-cli（メンテナ向け）

`playwright-cli` でブラウザを操作するための一次情報を、microsoft/playwright の upstream からミラーするスキル。
実行時の判断・手順は [SKILL.md](SKILL.md) と `output/playwright-cli/playwright-cli-skill.md`。ここは設計意図のみ。

## 何をミラーしているか

`playwright-cli install --skills claude` / `npx playwright init-skills` が `.claude/skills/` に配る
skill そのもの。実体は upstream の
`packages/playwright-core/src/tools/skills/`（コピー処理は `packages/playwright-core/src/tools/utils/installSkills.ts`）。

現状ミラーしているのは `playwright-cli` のみ。upstream には他に `playwright-component-testing` と
`playwright-trace` があるが、まずは CLI 利用に絞っている。

## なぜ SKILL.md を薄いルーターにしているか

本体を `output/playwright-cli/` と一段深く置き、`SKILL.md` は索引だけにしてある。
後から `playwright-component-testing` / `playwright-trace`、あるいは自前の運用メモを
同じスキルに足すときに、`output/<skill-name>/` を増やして `SKILL.md` の表に行を足すだけで済むため。
本体を `SKILL.md` に直接展開してしまうと、2 つ目の内容を入れた時点で作り直しになる。

## なぜ upstream `main` を根拠にするのか

手元にインストールされた Playwright や、どこかにある playwright のチェックアウトは upstream `main` より古いことがある。
判断の根拠は常に `output/`（`main` のスナップショット）に置き、手元と差がある場合は差として報告させる。

このスキルはもともと microsoft/playwright のクローンの中で育てたもので、fdshg693/AI に移すときに
クローンの `.claude/` への依存（ルール・ツールのパス）を外した。

## ファイル構成

| パス                                            | 位置づけ                                                                                      |
| ----------------------------------------------- | --------------------------------------------------------------------------------------------- |
| `SKILL.md`                                      | 実行時のルーター。状況別の入口（旧クローンの `ROLE.md` にあったルーティング）と参照先の対応表 |
| `download_playwright_cli_skill.py`              | スナップショット取得。`SKILL.md` の `` !`...` `` で起動時に必ず走る                           |
| `output/playwright-cli/playwright-cli-skill.md` | upstream の `SKILL.md`（リネーム保存）                                                        |
| `output/playwright-cli/references/*.md`         | upstream の参照ドキュメント                                                                   |
| `output/summary.md`, `output/_meta.json`        | スクリプトが生成する索引とメタ（取得日時・元パス対応）                                        |
| `references/*.md`                               | **自前**の運用手順。upstream ではなく実測が根拠。`output/` と混ぜない                         |

現在の自前リファレンスは 3 本。

- `site-recon.md` — ブラウザを開く前のサイト偵察（`curl` で robots/sitemap、リンクグラフ、外部サイトを叩くときの規則 R1〜R7）
- `script-cli-roundtrip.md` — スクリプト ⇄ CLI の往復でスクリプトを育てる
- `test-sites.md` — 実験用サイトの入口。fdshg693/AI の中なら `tools/browser/test-sites/`、無ければ最小 HTML

実測の根拠（測定条件・生の数値）はアンブレラの `docs/topics/browser-automation/`（`site-recon.md`・`script-cli-roundtrip.md`）。
スキル本文（エージェントが読む側）からは張らず、この README からだけ参照する。スキルの読み込み量を増やさないため。

`pwq`（snapshot を縮めるラッパー）・`pwdo`（一区間を安いモデルへ委譲）を前提にした手順は、
`tools/` の CLI のインストールが必須になるので my-tools プラグインの `browser-context-tools` スキルに分けた。
このスキルからは「入っていれば」の任意の参照にとどめる（配布先で `pwq` が無くても全手順が動く）。

### なぜ SKILL.md をリネームするのか

スキルのディレクトリ配下に `SKILL.md` という名前のファイルがもう 1 つあると、
スキル探索が別スキルとして拾いかねない。`playwright-cli-skill.md` に改名して回避している。
`references/` の相対リンクはディレクトリ構造を保っているのでそのまま通る。
リネームは `download_playwright_cli_skill.py` の `RENAMES` に定義。

### なぜ `references/` を `output/` の外に置くのか

`output/` は `download_playwright_cli_skill.py` の生成物で、列挙から外れたファイルは次回取得時に
自動削除される（`remove_stale_outputs`）。自前の文書をそこへ置くと消える。
根拠の出所（upstream / 自前の実測）を混ぜないためでもある。

## 取得対象を増やすとき

`download_playwright_cli_skill.py` の定数を編集する。

- `DIR_SOURCES` — `(repo ディレクトリ, output サブディレクトリ, 拾う拡張子)`。再帰的に列挙する
  - 例: `playwright-trace` を足すなら `(SKILLS_ROOT + "/playwright-trace", "playwright-trace", (".md",))`
- `FILE_SOURCES` — `(repo ファイルパス, output 相対パス)`。単発ファイル用
- `RENAMES` — `output` 相対パスの置換。新しいスキルを足したらその `SKILL.md` も登録する
- テンプレート（`playwright-component-testing/templates/**`）を拾うなら拡張子に `.ts` / `.tsx` を足す

追加後は `--force` で取得し、`output/summary.md` に出ることと、`SKILL.md` の対応表に行を足したかを確認する。
`output/` 内で列挙から外れたファイルは次回取得時に自動削除される（`remove_stale_outputs`）。

## 運用上の注意

- 鮮度は 7 日（`FRESHNESS`）。同梱スキルは Playwright のリリース単位で動くので、これ以上短くしても `gh` API を無駄に叩くだけ
- `gh api` は Contents API を 1 ファイル 1 回呼ぶ。取得対象を大きく増やすとレート制限に当たりやすい（未認証は 60 req/h）
- スクリプトは標準ライブラリのみ。`uv run` で起動する（PEP 723 の空の依存宣言を付けてあるので、uv ワークスペースの中でも同期を走らせない）
- `playwright-cli` 本体の導入有無はスキル側では面倒を見ない。未導入時の手順は upstream 本文の Installation 節にある

## 実測メモ（fdshg693/AI のアンブレラ）

- `docs/topics/browser-automation/site-recon.md` — `references/site-recon.md` §8 の数字の原データ
- `docs/topics/browser-automation/script-cli-roundtrip.md` — `references/script-cli-roundtrip.md` の根拠・生の数値・チャンクの全文
