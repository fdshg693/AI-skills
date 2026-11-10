# tav-lit — 1 URL のテキストだけを取りたい人向けの軽量ラッパー

`tav-cli` スキルは、`--detail` プリセット・`--topic` トピックフォルダへの役割別出力
(discovery/content/report)・自己記述 `ResultEnvelope`/`ExitCode`/`ResultKind` の型契約など、
複数 URL/複数タスクを跨いで結果を再利用することを前提にした仕組みを持つ。**「対象 URL が 1 つ
だけ分かっていて、その本文が欲しいだけ」「その 1 ページの中でクエリに関連する部分だけ抜き出し
たい」** というその場限りの用途に対しては、この仕組みは過剰でノイズになる。`tav-lit` は
この 1 ユースケースだけを切り出した、単一ファイルの軽量スキル。結果 `.md` と(トグル可能な)
監査ログは書くが、`--topic` のような複数タスクを跨いだ蓄積レイアウトや型契約は持たない。

AI に読ませる判断フロー・引数・出力形式は [SKILL.md](SKILL.md) を参照。このファイルは
**セットアップ前提と設計意図** に責務を絞る。

## 前提条件(重要: このスキル自体はインストール手順を提供しない)

このスキルは **`tavily` / `python-dotenv` が既にグローバルインストール済みであること** を
前提にしている。これは [`../tav-cli/README.md`](../../../../../tools/_plugin/my-tools/skills/tav-cli/README.md) の「前提条件」と
**全く同じ前提** であり、`tav-cli` を導入済みであればそのまま流用できる。

- Python / pip が使える環境
- Tavily API キー: `TAVILY_API_KEY` 環境変数、またはこのスキルのフォルダ
  (`extract_page.py` と同階層)の `.env` に設定済み(カレントディレクトリからの
  上方探索はしない)
- `pip install tavily python-dotenv` 済み

未セットアップの場合は、先に `tav-cli/README.md` の前提条件を済ませること。`tav-lit`
はライブラリのインストール手順は `tav-cli` を再利用する設計だが、`TAVILY_API_KEY` は
`tav-cli/.env` を共有せず、このスキル自身のフォルダに `.env` を個別に置く。

## なぜ `tav-cli` を直接使わないのか

`tools/tav-cli/extract_url_content.py` を薄いオプションで呼べば同じことはできるが、以下が
「1 URL だけ」の用途には見合わないコストになる:

- `--topic` を付けなければ `ResultEnvelope`(投影済みとはいえ JSON 構造)を経由する、付ければ
  トピックフォルダ配下に discovery/content/report のレイアウト管理(`pages/index.json` の
  追記など)が付いてくる
- `DETAIL_PRESETS` や `ExitCode`/`ResultKind` など、複数スクリプト間で一貫性を保つための
  型契約は 1 回きりの呼び出しには必要ない

`tav-lit` はこれらの型契約・トピックレイアウトを持たず、`extract_page.py` 1 ファイルが
Tavily extract API を叩いてタイトルと本文を Markdown ファイルに書き出すだけ(`TAVILY_OUTPUT_DIR`
配下に連番ファイル、詳細は [SKILL.md](SKILL.md))。監査ログも `TAVILY_WRITE_LOG` でトグル
できる 1 ファイル固定(`logs/extract_page-log.json`、実行のたび上書き)で、`tav-cli` の
`tav_core/` には依存しない独立実装。要約やキーワード検索のための別 API 呼び出しも用意しない —
取得した本文をこの会話の中で Claude が直接読んで行う方が、Tavily 側に要約させるより安く柔軟な
ため。ページ内キーワード検索に近い用途は `--query`(Tavily 側のチャンク絞り込み)で代替する。

## `tav-cli` との関係

- コード上の依存はない(`extract_page.py` は完全に独立した単一ファイルで、`tav_core/` を
  import しない)
- ライブラリの前提条件は `tav-cli` と共有している。`TAVILY_API_KEY` は共有せず、
  このスキルのフォルダに個別の `.env` を置く(`tav-cli/.env` とは別ファイル)
- 複数 URL/サイト全体/キーワード検索起点/結果の蓄積が必要になったら、`tav-cli` へ切り替える
  (判断フローは [SKILL.md](SKILL.md) 参照)

## ファイル構成

```text
skills/plugins/web-lookup/skills/tav-lit/
├── README.md         ← このファイル(前提条件・設計意図)
├── SKILL.md           ← AI に読ませるスキル本体(判断フロー・引数・出力形式)
└── extract_page.py    ← 唯一の実装。1 URL を受け取り、stdout にタイトル+本文を印字する
```
