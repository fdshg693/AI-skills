# web-lookup スキルについて

grep.app / Microsoft Learn / AWS Knowledge MCP / ローカルのページ取得（本文抽出） / Tavily / Context7 を、スキルに同梱した1つの CLI で使うためのスキル。このファイルは人間のメンテナ向け。Claude が実行時に読むのは [SKILL.md](SKILL.md) と、振り分け先の詳細ファイルであり、こちらは参照しない。

## 各ファイルの役割分担

`SKILL.md` 本体は起動・available・6系統の振り分けに集中するルーター。系統ごとの判断フローは同階層の詳細ファイルに分離する（[writing-skill](../../../cc-knowledge/skills/writing-skill/README.md) と同じ「1スキル+ルーター」構成）。

| ファイル   | 役割                                                                           | 読まれるタイミング      |
| ---------- | ------------------------------------------------------------------------------ | ----------------------- |
| `SKILL.md` | 起動プレフィックス、available、6系統の振り分け。手順の本体は持たない           | 常にスキル呼び出し時    |
| `ms.md`    | Microsoft Learn（`ms search` / `ms fetch`）の判断フローとクエリのコツ          | `ms` に振り分けたとき   |
| `aws.md`   | AWS Knowledge MCP（`aws search` / `aws fetch`）の判断フローとトピック選択      | `aws` に振り分けたとき  |
| `ctx.md`   | Context7（`ctx library` / `ctx docs`）の判断フローと候補選択                   | `ctx` に振り分けたとき  |
| `grep.md`  | grep.app（`grep search`）のリテラルクエリ制約と絞り込み                        | `grep` に振り分けたとき |
| `page.md`  | ローカル取得＋本文抽出（`page`）の判断フロー、失敗理由と欠落の目安、既知の弱点 | `page` に振り分けたとき |
| `tav.md`   | Tavily（`tav search` / `tav extract`）の判断フローとドメイン/チャンクの扱い    | `tav` に振り分けたとき  |

## なぜこのスキルがあるか

- [my-tools](../../../../../tools/_plugin/my-tools/) の `grep-app` / `ms-learn` / `aws-docs` / `tav-cli` / `use-context` は、それぞれ `tools/` の汎用 CLI を PATH に入れて使う。プラグインだけをよそへ移しても動かない
- こちらはスキルフォルダに最小 CLI を同梱し、`uv run --project` だけで依存を揃える。グローバル `uv tool install` はしない
- `tools/` の5パッケージ（`awsdocs` を含む）はコピーも import もしない。持ち出し先に `tools/` が無い前提で、日常利用のサブコマンドだけを再実装している

## 前提条件

- `uv` がインストール済みであること。起動は常に `uv run --project <このスキルディレクトリ> web-lookup <subcommand>`
- 任意: スキル直下の `.env` に `TAVILY_API_KEY` / `CONTEXT7_API_KEY` / `WEB_LOOKUP_OUTPUT_DIR`。実 `.env` はコミットしない（[`.env.example`](.env.example) のみ）
- page / grep / ms / aws は API キー不要。tav は `TAVILY_API_KEY`、ctx は `CONTEXT7_API_KEY` が空なら `available` が unavailable を出す

## 汎用 CLI との差分（意図的）

最小再実装なので、元の5 CLI と出力・耐障害性は一致しない。

- ctx は 202 ポーリング / 429 バックオフ / 301 追従を移植していない。失敗したらエラーをそのまま出す（元 `ctx7` より失敗しやすい）
- 出力は `WEB_LOOKUP_OUTPUT_DIR`（未設定時 `temp/web-lookup`）配下の連番フォルダ + `index.md` だけ。Q&A 分離も `--topic` 役割フォルダも `--json` も無い
- aws は `search`（`--limit` 無し、常に10件）と `fetch`（1 URL・追い読み常時オン）だけ。`regions` / `availability` / `skill` / `tools` / `call` / `--json` / `--start-index` / `--max-length` / 複数 URL / 429 の1回再試行は移植していない。検索結果の区分サブフォルダも無く、タイトルの `[Blog]` 等のラベルで代える。終了コードは他系統と同じ 0/1（元 `awsdocs` の 3/4 は使わない）
- `code-search` / `map` / `crawl` / `research` / MCP の `tools`/`call` は作っていない

## `page` 系統（元 CLI に無い追加分）

- `scripts/page.py` が `requests` で HTML を取り、trafilatura（`favor_recall`・表あり・リンクなし）で本文を Markdown にする。表セル内の `li` を `/` 連結にする前処理と、空白の正規化を足している。User-Agent は汎用名 `web-lookup/<パッケージ版>` に `Accept` / `Accept-Language` を付ける（利用者の情報を入れない・ブラウザを偽装しない）
- 失敗（非 2xx・タイムアウト・非 HTML・5MB 超・抽出後 200 字未満）は index に理由を出すだけで、`tav extract` を自動では呼ばない。URL を第三者に送るかはエージェントが判断する
- index の欠落の目安（`excerpt gaps` / `possible gaps` / `cut off` / `body from line N`）は `scripts/hints.py` の純関数で、`page` と `tav` の両方に出す。語を変えたら `page.md` と `tav.md` の表を突き合わせる
- 設計判断と実測の根拠はアンブレラの `plans/web-lookup-tav-feedback/`
- テスト: `uv run --project <このスキルディレクトリ> --group dev pytest`（合成 HTML のみ、ネットワークに出ない）

## 情報源と保守

- サブコマンド面と `available` の出力契約は CLI（`scripts/web_lookup.py` / `scripts/env_check.py`）が正本。オプション表は SKILL.md と各詳細ファイルに転記せず `--help` に任せる
- 5系統の振り分けは SKILL.md 固有。各系統の判断フローは同階層の詳細ファイル固有（元の [ms-learn](../../../../../tools/_plugin/my-tools/skills/ms-learn/SKILL.md) / [aws-docs](../../../../../tools/_plugin/my-tools/skills/aws-docs/SKILL.md) / [use-context](../../../../../tools/_plugin/my-tools/skills/use-context/SKILL.md) / [grep-app](../../../../../tools/_plugin/my-tools/skills/grep-app/SKILL.md) / [tav-cli](../../../../../tools/_plugin/my-tools/skills/tav-cli/SKILL.md) の運用方針を、この CLI のサブセットに合わせて移植したもの）
- CLI のサブコマンド名・`available` の列・env 名を変えたら SKILL.md の起動例と振り分け、および該当する詳細ファイルを突き合わせる
- `tools/web-research/awsdocs` のサーバー実測挙動（`tools/web-research/awsdocs/memo/01-knowledge-mcp-server.md`）が変わったら、`scripts/backends.py` の AWS 判定（`_aws_unwrap` / read 要素の判定 / レート制限判定）と `aws.md` も突き合わせる
- 元 CLI にあるがこちらに無いもの（`code-search` / `regions` / `availability` / `skill` / `map` / `crawl` / `research` / `tools` / `call` / `--topic` / `--detail` / `--json` / `--timeout` 等）を、詳細ファイルへ書き戻さないこと
