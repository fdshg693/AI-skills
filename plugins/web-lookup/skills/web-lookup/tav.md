# Tavily (`tav`)

一般 Web（ニュース、製品比較、一次情報の裏取り）を取るときの手順。起動プレフィックスは [SKILL.md](SKILL.md) と同じ。以降は `tav search` / `tav extract` だけ書く。オプションは `--help` を正本にする。表は転記しない。

`TAVILY_API_KEY` が空なら `unavailable`。呼ばない。この CLI にあるのは `search` と `extract` だけ。`search-extract` / `map-extract` / `--topic` / `--detail` / `--json` は無い。

**`map` / `crawl` / `research` は Tavily API には存在するが、この CLI には出していない。** サイト単位の偵察では `curl` + `sitemap.xml`（0 円）に劣るため — 実測で `map` は 15 クレジットを払って sitemap に無い生きた新規ページが 1 枚だけ、代わりに死 URL を 5 件掴まされた（別サイトでも sitemap の 20% しかカバーしない部分集合）。**「無いなら出そう」と考える前に、`browser` プラグインの `using-playwright-cli` スキルの `references/site-recon.md` §6（`map` を使う条件）を見る。**

**`localhost` / 社内 / 非公開 / 認証壁の向こうの URL は外部サービスに渡さない**（`tav` に限らず）。第三者への送信にあたり、そもそも到達もできない。

## 判断フロー

```text
1. Microsoft/Azure/.NET/M365 の公式ドキュメントか?
   Yes -> 系統を `ms` に切り替える（[SKILL.md](SKILL.md) の振り分け）
   外部ライブラリの現行 API か? -> `ctx`
   公開 GitHub の実コードか?    -> `grep`

2. 対象 URL が分かっているか?
   Yes -> 先に `page <url>`（[page.md](page.md)。キー不要・URL を外部に送らない）
          index に `failed` / `too short` が出た公開 URL だけ tav extract <url>
   No  -> tav search "<query>"

3. search の抜粋で足りるか?
   正確性が要るページ（求人票・スペック表・料金表など、1 項目の欠落で判断を誤るもの）
     -> 抜粋で結論を出さない。結果ファイルの `URL:` 行を page に渡す
   概要・当たりを付けるだけ -> 抜粋をそのまま使う
   全文が要る -> 結果ファイルの `URL:` 行を page に渡す

4. page / tav extract でも JS の初期値（`0+` 等）・項目の欠落・ログイン誘導しか取れない
   -> 言い換えて粘らず、ブラウザ（`browser` プラグインの `using-playwright-cli` スキル）へ
      SNS・口コミサイト・地図のレビューなどログイン壁が分かっているサイトは最初からブラウザ
```

迷ったら URL 起点は `page`（失敗したら `extract`）、キーワード起点は `search`。必要なページだけ `search` → `page` で足す。**サイト全体の一覧が要るときはこの CLI ではなく `curl` + `sitemap.xml`**（`using-playwright-cli` スキルの `references/site-recon.md`）。

## クエリとドメイン

- `query` は日本語でよい。製品名・機能名・正式ドキュメント名は英語の方が強いことがある。弱ければ英語または日英混在で再実行する
- `--include-domain` は優先・許可の強い絞り込みであり、完全一致の隔離フィルタではない。広い host（`microsoft.com`）より狭い host（`techcommunity.microsoft.com`）を優先する。想定外 URL は結果を見て捨てる
- `--exclude-domain` も繰り返し指定できる

`search` と、`--query` を付けた `extract` は、本文全体ではなく関連チャンクだけを返す。出力の `[...]` はチャンク境界であり、抽出失敗ではない。全文は `page` で取る。`page` が失敗して `extract` を使うときは `--query` を付けない（`--query` は長いページの特定セクションを確かめ直す用途に使う）。

`--query` なしの `extract` はページ全体を Markdown にするので、先頭にナビゲーション・メニュー・繰り返しの装飾が大量に乗ることがある。index の `body from line N` を見て、その行付近から読む。

## 結果の読み方

成功時 stdout は `index.md` のパスだけ。本文は出ない。

1. `index.md` を Read する。各行は `(N chars)` で、欠落の目安があれば `—` の後ろに続く（下表）
2. タイトルから読むファイルを選ぶ。Read で足りるものだけ読む。他スキルには回さない
3. 各結果ファイルは先頭付近に `URL:` がある。search には `Score:` もある。深掘りするときはその URL を `page` に渡す（失敗したら `tav extract`）
4. 空結果は stderr `No results.`

| 目安               | 意味                                                                                  | 次の動き                                                                    |
| ------------------ | ------------------------------------------------------------------------------------- | --------------------------------------------------------------------------- |
| `excerpt gaps: N`  | search・`--query` 付き extract の抜粋で、チャンク境界 `[...]` が N 個ある。省略は仕様 | 抜粋の外に要る情報があり得る。正確性が要るなら `page` で全文を取る          |
| `possible gaps: N` | `--query` なし extract の本文に `[...]` が N 個ある                                   | 該当箇所を読み、欠けていれば `page` かブラウザで確かめる                    |
| `cut off`          | 最後の行が文・表・リスト・見出しの終わり方をしていない                                | 抜粋なら `page` で全文を取る。誤検知（URL・メールアドレスで終わる等）もある |
| `body from line N` | 最初の見出しが N 行目。手前にナビゲーションが残っている                               | N 行目付近から読む                                                          |

別のクエリで同じ URL が再びヒットしたら、前に読んだ結果ファイルを読み直さない。index.md のタイトルで見当を付け、迷えば結果ファイル先頭の `URL:` 行だけ確かめる。

同じクエリ/URL を再実行しても上書きされず、連番フォルダが増えるだけ。`--topic` の役割フォルダは無い。
