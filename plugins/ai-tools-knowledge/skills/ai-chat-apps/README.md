# ai-chat-apps

メンテナ向け。実行時の手順は [SKILL.md](SKILL.md)。作成時の調査・判断の記録はアンブレラの `plans/ai-chat-apps-knowledge/`。

## 構成

情報を 2 層に分けている。

| 層                   | ファイル                                                   | 持つもの                                                                             | 更新                                                          |
| -------------------- | ---------------------------------------------------------- | ------------------------------------------------------------------------------------ | ------------------------------------------------------------- |
| 機能マップ（手書き） | `chatgpt.md`・`gemini.md`・`claude-ai.md`・`comparison.md` | 機能名（旧名・移行先）→ 公式ページ URL、プラン条件の要約、既知の食い違い、最終確認日 | 手で。月 1 回程度、またはリリースノートで改名・廃止を見たとき |
| 都度取得             | 公式ヘルプ・リリースノート                                 | 上限値・対応プラン・手順などの具体値                                                 | 回答のたびに取る                                              |

機能の存在・名前・対応関係は月単位でしか変わらないが、上限値・対応プラン・手順は頻繁に変わる。だから具体値は持たず、「どこに書いてあるか」だけを手で持つ。

## 情報源

| アプリ  | 索引                                                                                                                                            | 本文                                        | 理由                                                                                                                           |
| ------- | ----------------------------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------ |
| Claude  | `https://support.claude.com/llms.txt` の `## English` 節（約 390 本）。更新日は `/sitemap.xml`（約 10 MB）の `lastmod` を記事 ID で突き合わせる | 記事 URL に `.md` を付けて直取得（`fetch`） | 公式の索引と Markdown 版がある                                                                                                 |
| ChatGPT | `help.openai.com/en` から `/en/collections/<id>` を直列に辿る（約 500 本、1 秒間隔で 1 分強）                                                   | `web-lookup` の `page`                      | sitemap・llms.txt が無い。コレクションページは SSR。既定の python-requests の User-Agent は 403 になるのでブラウザの UA を送る |
| Gemini  | 持たない。記事 ID は `gemini.md` に手書き                                                                                                       | `web-lookup` の `page`（`?hl=en`）          | `/gemini/sitemap` にタイトルが無く、取るには全ページ取得が要る。並列取得で HTTP 429 → CAPTCHA になった                         |

- HTML の本文はスクリプトで取らず、`web-lookup` スキルの `page` に任せる（JS 描画による欠落の検知と代替経路が向こうに揃っている）。スクリプトが本文を取るのは静的な Markdown の Claude だけ
- 英語版を正にする。ChatGPT の日本語版リリースノートは英語版より約 4 か月遅れていた（2026-11 時点）
- `tav extract` はキャッシュ版を返すことがあるので、上限・モデル名の確認には使わない（SKILL.md に書いた唯一のスキル固有の注意）

## スクリプト

すべて `webref_cli.py`（PEP 723 で `requests`・`typer` を宣言。`uv run` で依存が入る）から呼ぶ。

| サブコマンド                      | ファイル                | 出自                                                                                                                                                           |
| --------------------------------- | ----------------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| —                                 | `download_url_index.py` | writing-skill-web の `scripts/download_url_index.py` をそのままコピー。URL 検証・`fetched_at` の読み取りをライブラリとして使う。自身の `main` は配線していない |
| `download <claude\|chatgpt\|all>` | `download_index.py`     | 新規。情報源の設定（`SOURCES`）と、Claude の llms.txt 英語節＋lastmod、ChatGPT のコレクションのクロール。テンプレートに無い取得方法なので書き起こした          |
| `search <語...>`                  | `search_index.py`       | 新規。索引の行を AND（`--any` で OR）で絞って標準出力に出す。古い索引はその情報源だけ取り直す                                                                  |
| `fetch <URL...>`                  | `fetch_claude_pages.py` | writing-skill-web の `scripts/fetch_selected_pages.py` を改変。manifest を廃し、Claude の `/en/articles/` だけを `.md` で取る                                  |
| —                                 | `webref_cli.py`         | writing-skill-web の `scripts/webref_cli.py`。`SUBCOMMANDS` を差し替え、PEP 723 ヘッダーを足した                                                               |

鮮度は両方 3 日（`download_index.py` の `SOURCES`）。起動時の `!` コマンドでのダウンロードはしない。3 情報源を毎回取ると重く、質問に要るのは多くて 2 つなので、`search` が必要な情報源だけ取り直す。

## 生成物

- `output/claude-index.md`・`output/chatgpt-index.md` — 記事索引。コミットする（オフラインでも引けるように。差分で記事の追加・改名も追える）。形式は frontmatter（`fetched_at` 等）＋ `## セクション` ＋ `- [タイトル](URL): 説明 (lastmod: …)`
- `output/temp/` — `fetch` の本文。コミットしない（`.gitignore`）

## 更新手順

```sh
uv run skills/plugins/ai-tools-knowledge/skills/ai-chat-apps/webref_cli.py download all --force
```

確認すること:

- 記事数が大きく減っていない（2026-11-18: claude 386・chatgpt 499）。ChatGPT が 0 本ならヘルプセンターのマークアップが変わった。`download_index.py` の `CollectionPageParser`（記事カードは `<a><span>タイトル</span><span>説明</span></a>`）を直す
- Claude の行に `lastmod` が付いている（sitemap の取得に失敗すると付かないだけで、索引は書かれる）

### Gemini の記事一覧を作り直す

機能マップの記事 ID を見直すときだけ行う。`https://support.google.com/gemini/sitemap` の URL から `community-guide`・`thread` を除き、`co=GENIE.Platform=` 違いの重複を除いてから、**1 本ずつ間隔を空けて**（並列にしない）`?hl=en` の `<title>` を取る。2026-11-18 の一覧はアンブレラの `plans/ai-chat-apps-knowledge/progress/01-gemini-help-index.md`。

## テスト

評価シナリオと RED/GREEN の記録は [tests/scenarios.md](tests/scenarios.md)。スクリプトの pytest は持たない（コピー元テンプレートのテストは writing-skill-web 側にある）。
