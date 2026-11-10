---
name: tav-lit
description: Fetch the raw text/markdown content of a single already-known URL via Tavily extract, or pull just the query-relevant chunks from that one page. Use when exactly one URL is already known and only its text (or a keyword-focused excerpt of it) is needed, via one minimal command. Results are always written to a Markdown file (never printed in full to the terminal) so large pages don't blow up context; only the file path is printed. Do not use for multiple/batch URLs, site maps or crawls, web-wide keyword search when the URL is unknown, or work whose results need to accumulate across many pages/tasks — that belongs to the `tav-cli` skill.

# 前提条件(このスキル自体はセットアップ手順を提供しない):
#   - tavily / python-dotenv がグローバルにインストール済みであること
#     (`tools/tav-cli/README.md` の「前提条件」と同じ。未インストールならそちらを先に実施)
#   - TAVILY_API_KEY が環境変数、またはこのスキルと同階層(extract_page.py と同じフォルダ)の
#     .env に設定済みであること(カレントディレクトリからの上方探索はしない)
#
# 同じ .env で TAVILY_OUTPUT_DIR(結果 .md の出力先ベース、未設定時は temp/simple_tavily。
# カレントディレクトリからの相対解決)・TAVILY_WRITE_LOG(監査ログ出力トグル、未設定=true。
# ログは extract_page.py と同階層の logs/extract_page-log.json に実行のたび上書き)も設定できる。
#
# tav-cli への依存: なし(コードは完全に独立した単一スクリプト)。
#   ただしライブラリの前提条件は tav-cli と共有する設計。TAVILY_API_KEY 自体は
#   スキルごとに同階層の .env で個別に設定する。
# このスキルは tav-cli の `tav extract` から「1 URL」のケースだけを切り出した軽量版。
# detail プリセット・--topic トピックフォルダ・自己記述 result envelope・ExitCode/ResultKind
# の型契約は意図的に持たない(1 URL のテキスト取得に対しては過剰なため)。結果ファイル・
# 監査ログ自体は書くが、tav-cli のような複数タスクを跨いだ蓄積レイアウトは持たない。
meta:
  tag: []
  requires_repo_tools: none
  requires_env: TAVILY_API_KEY
  dependencies: tavily, python-dotenv
  requires_install: tavily, python-dotenv
  requires_hooks: none
  requires_skills: none
  status: stable
  description: no description
  version: 1.0.4
---

## 前提条件

- `tavily` / `python-dotenv` がグローバルにインストール済みであること
- `TAVILY_API_KEY` が環境変数、またはこのスキルと同階層(`extract_page.py` と同じ
  フォルダ)の `.env` に設定済みであること(カレントディレクトリからの上方探索はしない)

**ライブラリの前提は `tav-cli` スキルと共有する。** まだセットアップしていない場合は、
このスキルの手順を進める前に `tav-cli` の `README.md`(前提条件セクション)を先に
済ませること。このスキル単体でのインストール手順は用意していない。`TAVILY_API_KEY` は
`tav-cli` の `.env` を共有せず、このスキルのフォルダに個別の `.env` を置く。

## 使うべきか、tav-cli を使うべきかの判断

```text
対象 URL は 1 つだけで、すでに分かっているか?
  No  -> tav-cli(tav search / tav map で URL を探す)
  Yes -> 2 へ

その 1 URL の本文(またはクエリ関連部分)を、1 ファイルとして取得できればよいか?
  Yes -> tav-lit(このスキル)
  No、以下のいずれかに該当する -> tav-cli(tav extract 等)
    - 複数 URL をまとめて処理したい
    - サイトの map / crawl が必要
    - 結果を --topic のトピックフォルダで役割別(discovery/content/report)に整理し、
      後段の複数タスクで使い回したい
    - 戻り値の型契約(ResultEnvelope/ExitCode/ResultKind)を厳密に管理したい
    - AI 自身に調査・要約までまとめて任せたい(tav research)
```

迷ったら: **1 URL・その場限りで読むだけ → tav-lit**、それ以外は全部 `tav-cli`。

## 使い方

```!
python "${CLAUDE_SKILL_DIR}/extract_page.py" --help
```

bash:

```bash
python "${CLAUDE_SKILL_DIR}/extract_page.py" https://example.com/page
```

PowerShell:

```powershell
python "${CLAUDE_SKILL_DIR}/extract_page.py" https://example.com/page
```

### 引数

| 引数      | 必須 | 説明                                                                                                                                          |
| --------- | ---- | --------------------------------------------------------------------------------------------------------------------------------------------- |
| `url`     | Yes  | 取得対象の URL。1 つだけ(複数 URL を渡したい場合は tav-cli の `tav extract` を使う)。                                                         |
| `--query` | No   | 指定すると、本文全体ではなく **このクエリに関連するチャンクだけ** を返す(Tavily 側の絞り込み)。ページ内のキーワード検索・部分的な要約に使う。 |
| `--deep`  | No   | `extract_depth=advanced` を使う(JS 重多用・表組みなど、既定の `basic` では取得が弱いページ向け)。                                             |

`--query` を付けたときの出力に現れる `[...]` は、チャンク境界(=途中が省かれた非連続抽出)を
示すもので、抽出失敗ではない。**本文を丸ごと読みたい場合は `--query` を付けない**。

## 出力先とファイルレイアウト

**本文は必ず 1 ファイルとして書き出す。ターミナルにはそのファイルのパスだけを印字する**
(本文自体を stdout に流すことはしない)。書き出し先は `TAVILY_OUTPUT_DIR`(`.env`、未設定時は
`temp/simple_tavily`。カレントディレクトリからの相対解決)配下に、`NNNN-<title のスラッグ>.md`
という連番ファイル名で置かれる。同じ出力先ディレクトリに対して再実行しても**上書きせず追記**
していく(`0001-...` の次は `0002-...`)。

```text
temp/simple_tavily/                 ← TAVILY_OUTPUT_DIR(.env、既定値)
├── 0001-example-domain.md
└── 0002-another-page.md
```

各 `.md` の中身:

```text
# <title>
Source: <url>

<本文(または --query 指定時はクエリ関連チャンクのみ)>
```

**要約用・キーワード検索用の別引数は用意していない。** 本文を取得した後の要約やキーワード検索は、
このファイルを読んだ Claude がそのまま会話の中で行う。ページが大きくキーワード検索したい範囲が
明確な場合は `--query` で Tavily 側に絞り込ませてから読む方が、本文全体を読んでから探すより
効率的。

## 監査ログ

リクエスト/レスポンスの全詳細は、`.env` の `TAVILY_WRITE_LOG`(未設定=`true`、
`false`/`0`/`no`/`off`/空で抑止)が有効な限り `extract_page.py` と同階層の
`logs/extract_page-log.json` に書かれる(実行のたびに上書き。過去分は残らない)。
書いた場合はそのパスもターミナルに印字する。ページ本文のファイルとは別ファイル・別用途
(本文はページ内容そのもの、ログは Tavily とのやり取りの記録)。

## 終了コード

| code | 意味                                                                         |
| ---- | ---------------------------------------------------------------------------- |
| `0`  | 成功。結果 `.md` のパスがターミナルに出力されている                          |
| `1`  | 実行時エラー(ネットワーク/API エラー、`tavily` パッケージ未インストールなど) |
| `2`  | `TAVILY_API_KEY` が未設定                                                    |
| `3`  | Tavily にキーを拒否された(無効なキー)                                        |
| `4`  | 抽出対象 URL からコンテンツを取得できなかった(全滅)                          |

エラーメッセージは常に stderr に出る。成功時にターミナルへ印字されるのはファイルパスのみ。
