---
# ChatGPT・Gemini・Claude の利用者向けチャットアプリ（まずは WEB 版）の知識スキル。
# 機能マップ（chatgpt.md / gemini.md / claude-ai.md / comparison.md）で公式ページを引き、具体値は都度取得する 2 層構成。
# 索引（output/*-index.md）は起動時に取らず、search が古い索引だけ取り直す（3 情報源を毎回取ると重いため）。
# 情報源・スクリプトの出自・索引の更新手順は同階層の README.md（メンテナ向け）。
name: ai-chat-apps
description: Use when answering questions about the consumer chat apps ChatGPT (chatgpt.com), Gemini (gemini.google.com) and Claude (claude.ai) — features, settings, how-to steps, plan limits and availability, or how equivalent features map across the three (projects/notebooks, custom GPTs/Gems/skills/plugins, connectors/apps/custom MCP, memory, deep research, canvas/artifacts, agents). Grounds answers in the official help centers and release notes instead of training-data memory, which goes stale quickly here (features are renamed and retired often). Not for the OpenAI, Gemini or Claude APIs, Claude Code, Codex or Gemini CLI.
allowed-tools: Bash(uv run ${CLAUDE_SKILL_DIR}/webref_cli.py *) Read Grep
meta:
  tag: []
  requires_repo_tools: none
  requires_env: none
  dependencies: requests, typer, uv
  requires_install: uv
  requires_hooks: none
  requires_skills: web-lookup
  status: experimental
  description: Official-source answers about the ChatGPT, Gemini and Claude web apps, with a cross-app feature map
  version: 0.1.0
---

# ChatGPT・Gemini・Claude アプリの最新情報

3 つのチャットアプリの機能・設定・プラン差を、公式ヘルプとリリースノートを根拠に答える。この領域は機能名の変更・廃止・提供範囲の拡大が月単位で起きるので、**記憶や検索結果の抜粋で答えない**。

## 範囲

- 対象: chatgpt.com・gemini.google.com・claude.ai の WEB 版（デスクトップ・モバイルは差分が公式に書かれている範囲で触れる）
- 範囲外は次のスキルへ渡す。質問の製品があいまい（「Claude に MCP サーバーを追加したい」等）なら、製品ごとの振り分けを示し、このスキルの範囲の分を答える。どの製品か分からないと何も答えられないときだけ先に尋ねる
  - Claude API・Anthropic SDK → `claude-api`
  - Claude Code → `claude-code-docs`（CLI のオプションは `claude-cli-docs`）
  - Codex（CLI・クラウド）→ `codex-docs`／`codex-cli-docs`
  - OpenAI API・Gemini API・Gemini CLI → 本スキルの対象外。各公式ドキュメント（developers.openai.com・ai.google.dev 等）を `web-lookup` で引く

## 手順

1. **アプリと機能を特定する。** 旧名で聞かれることが多い（GPTs・Gems・Extensions・connectors 等）。機能マップで現在の名前・移行先に置き換えてから調べる
2. **機能マップで公式ページを引く。** アプリ別は [chatgpt.md](chatgpt.md)・[gemini.md](gemini.md)・[claude-ai.md](claude-ai.md)、アプリ間の対応・比較は [comparison.md](comparison.md)。マップに無ければ下の「索引検索」で探す
3. **公式ページの本文を取って具体値を確かめる。** 上限・対応プラン・地域条件・UI の項目名・手順は、必ずこのステップで取った本文から書く（取り方は「情報源と取り方」）
4. **直近の変更を確かめる。** 廃止・移行・名称変更・提供範囲（地域・プラン）が絡む質問なら最終確認日に関係なく、それ以外でも機能マップの最終確認日が 30 日より前なら、そのアプリのリリースノートを確かめる。リリースノートは 10 万字を超えるので通読しない。取ったファイルを機能名で grep し、最終確認日より新しい項目だけ読む（Gemini は日本語と英語が混ざるので「カスタム アプリ」と「custom app」のように両方で探す）
5. **回答する。** 参照した公式 URL と確認日を添える。本文で確認できなかった部分（UI の文言、プラン条件の空白など）は、そう明示して実画面での確認を促す

## 情報源と取り方

英語版を正にする（日本語版は更新が数か月遅れることがある）。

| アプリ  | ヘルプセンター                                | 本文の取り方                                                                   | リリースノート                                                                                                                         |
| ------- | --------------------------------------------- | ------------------------------------------------------------------------------ | -------------------------------------------------------------------------------------------------------------------------------------- |
| Claude  | `support.claude.com/en/`                      | `fetch`（下記。`.md` 版を直取得）                                              | `https://support.claude.com/en/articles/12138966-release-notes`（`fetch` で取る）                                                      |
| ChatGPT | `help.openai.com/en/`                         | `web-lookup` の `page`                                                         | `https://help.openai.com/en/articles/6825453-chatgpt-release-notes`（巨大。先頭から読む）。Business・Enterprise/Edu 版は機能マップ参照 |
| Gemini  | `support.google.com/gemini/answer/<id>?hl=en` | `web-lookup` の `page`。WEB 版の手順は `&co=GENIE.Platform%3DDesktop` を付ける | `https://gemini.google/release-notes/`                                                                                                 |

- `page` の使い方と、失敗・JS 描画による値の欠落・ログイン壁のときの切り替え（`page` → `tav extract` → ブラウザ）は、`web-lookup` スキルの `page.md` の判断フローに従う。ここでは繰り返さない
- **このスキル固有の注意:** `tav extract` はキャッシュされた古い版を返すことがある（Gemini の上限記事で旧モデル名が返った例がある）。上限・モデル名・対応プランは `page` で取れた本文かブラウザで確かめる。`tav search` は記事を探す用途になら使ってよい
- support.google.com はまとめて取ると CAPTCHA になり、1 本目の `page` から HTTP 429 になることも多い。Gemini の記事は 1 本ずつ、必要なものだけ取る。429 なら `tav extract` に切り替え、取れた本文の条件・上限が機能マップの要約と合うかを照らす。合えばその本文で答え、`tav extract` で取ったことを回答に書く。合わない、または本文が空なら、そこを「公式本文で未確認」と明示して実画面での確認を促す（Android 版など別プラットフォームの記事や検索の抜粋で WEB 版の値を埋めない）
- `web-lookup` は作業ディレクトリの `temp/web-lookup/` に書き出す。このスキルのディレクトリに `cd` してから実行しない
- 料金ページ（chatgpt.com/pricing・claude.com/pricing・gemini.google/subscriptions）は価格の数値が JS 描画で抜けることがある。プラン別の上限はヘルプの上限記事を正にする（記事は機能マップ参照）

### 索引検索・Claude 記事の取得（同梱スクリプト）

機能マップに載っていない記事は、ヘルプセンターの記事索引（タイトル・説明・所属セクション）から探す。キーワードは英語で渡す。索引が古ければ（3 日）`search` がその情報源だけ取り直す。ChatGPT の取り直しは 1 分ほどかかる。

```sh
uv run "${CLAUDE_SKILL_DIR}/webref_cli.py" search custom mcp --source chatgpt
uv run "${CLAUDE_SKILL_DIR}/webref_cli.py" search projects limit --source claude
uv run "${CLAUDE_SKILL_DIR}/webref_cli.py" fetch https://support.claude.com/en/articles/9517075-what-are-projects
```

- `search`: 既定はすべての語を含む記事（`--any` でどれか）。`--source` 省略時は claude と chatgpt の両方。終了コード 3 は該当なし。Claude の結果には記事の `lastmod`（更新日）が付く
- `fetch`: Claude の記事だけ。URL は複数まとめて渡せる。本文を `output/temp/` に書き、`<URL> -> <ファイル>` を出す。そのファイルを Read する
- Gemini の索引は持たない。機能マップに無い記事は `tav search "site:support.google.com/gemini <語>"` 等で探し、本文は `page` で取る
- 索引に見当たらない新しい記事がありそうなら `uv run "${CLAUDE_SKILL_DIR}/webref_cli.py" download <claude|chatgpt> --force` で取り直す

## 回答の注意

- 公式どうしで食い違う（ヘルプ記事と開発者ドキュメント、プラン表と記事本文など）ときは、片方で断定しない。両方の URL と記述を示し、実画面での確認を促す。既知の食い違いは機能マップに書いてある
- 開発者向けドキュメント（developers.openai.com 等）・企業向けの別製品（Gemini Enterprise 等）・別のヘルプセンターの記述を、利用者向けアプリの仕様として流用しない。使う場合は別物だと明記する
- UI のメニュー名・ボタン名は記憶で書かない。本文にある英語表記をそのまま示し、日本語 UI での名前が分からなければそう書く
- 横断比較では、1 対 1 に対応しない機能（Claude の projects＋skills＋plugins など）を無理に 1 つに寄せない。[comparison.md](comparison.md) の対応表に従う
