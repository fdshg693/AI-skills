# AWS Knowledge MCP (`aws`)

AWS の公式ドキュメント・Blog・What's New・re:Post Knowledge Center・CDK/CloudFormation リファレンスを取るときの手順。起動プレフィックスは [SKILL.md](SKILL.md) と同じ。以降は `aws search` / `aws fetch` だけ書く。オプションは `--help` を正本にする。表は転記しない。

この CLI にあるのは `search` と `fetch` だけ。`regions` / `availability` / `skill` / `tools` / `call` / `--json` / `--start-index` は無い。リージョン可用性はここでは調べられない。

## 判断フロー

```text
1. 対象ページの URL がすでに手元にあるか（前回の search 結果、ユーザー提示など）?
   Yes -> aws fetch <url>
   No  -> 2 へ（URL は推測で組み立てない。理由は「罠」参照）

2. 何を探すかで --topic を1つ選んで aws search する:
   API/SDK/CLI の仕様          -> --topic reference_documentation
   エラー解決                  -> --topic troubleshooting（エラー文をそのまま引用）
   新機能・リリース情報        -> --topic current_awareness
   CDK / CloudFormation        -> --topic cdk_docs / cdk_constructs / cloudformation
   Amplify / Strands Agents    -> --topic amplify_docs / strands_docs
   概念・ベストプラクティス    -> トピック無し（general。Blog も混ざる）

3. search の結果ファイル（各件は約2000字の逐語チャンク）で答えられるか?
   Yes -> fetch しない
   No（一覧・全件・手順全体が要る） -> 該当ファイルの `URL:` 行を aws fetch に渡す

4. AWS 以外のサイト、または取得できない URL
   -> 系統を `tav` に切り替える（[SKILL.md](SKILL.md) の振り分け）
```

`fetch` は切り詰められたページを同じ接続で追い読みし、1ページを1ファイルに連結して書く。本文の前にサーバーが付けた見出しごとの文字範囲付き TOC が1回だけ残る。長いページは `index.md` の文字数を見て、必要な節だけ Read する。

## クエリのコツ・罠

- **トピック未指定（`general`）だと Blog が上位に来やすい。** 公式リファレンスが欲しいときはトピックを1つ指定する（複数指定すると順位が薄まる。最大3）
- **的外れなクエリでもゼロ件にならず、無関係な結果が返る。** タイトルで関連性を必ず確認し、外れていればクエリを具体化して引き直す
- **存在しない docs URL を `fetch` するとエラーにならず、ガイドのトップページへリダイレクトされた本文が返る**（exit 0）。stderr とファイル先頭の `> Warning: redirected to ...` を確認する。URL は search の `URL:` 行を使う
- 取得できる URL は AWS 系のみ（docs.aws.amazon.com、aws.amazon.com、repost.aws の Knowledge Center、docs.amplify.aws、strandsagents.com 等）。それ以外は exit 1 で許可ドメインの一覧が stderr に出る

## 結果の読み方

成功時 stdout は `index.md` のパスだけ。本文は出ない。

1. `index.md` を Read する（各行末に文字数がある）
2. タイトル先頭の区分ラベルで出典を見分ける: ラベル無し＝docs 系、`[Blog]`、`[What's New]`、`[re:Post]`、`[Skill]`。番号は元の検索順位のまま
3. 各結果ファイルは見出し直後に `URL: <出典>` がある。深掘りするときはその URL を `aws fetch` に渡す
4. `[Skill]` は AWS Agent Skill の名前と説明だけ（`Skill: <name>` 行、URL なし）。本文を取るサブコマンドはこの CLI に無い
5. `fetch` が途中で止まった場合（長いページの特定範囲で空応答が出るサーバー側の既知の癖）は、取れた分を書き出し、ファイル先頭に `> Incomplete: reading stopped at char N ...` を付けて exit 0。1チャンク目から取れなければ exit 1
6. レート制限は `rate limited by the AWS Knowledge MCP server` が stderr に出て exit 1。自動再試行はしないので、少し待って再実行する
