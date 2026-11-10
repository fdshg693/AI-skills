# litellm-docs

メンテナ向け。実行時の手順は [SKILL.md](SKILL.md)。

## 設計

LiteLLM公式サイトの sitemap をURL発見の唯一の入口とし、厳密な `https://docs.litellm.ai/docs/` prefixを通過したURLだけを正規化する。sitemapの全ルートにはリリースノート、ブログ、タグ、ルートページなどが混在するため、技術文書以外は生成物へ入れない。

| 情報源                                                                                                     | 役割                                                          |
| ---------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------- |
| `https://docs.litellm.ai/robots.txt`                                                                       | 公開された sitemap 宣言の確認                                 |
| `https://docs.litellm.ai/sitemap.xml`                                                                      | 現在の公開URL発見と生成元                                     |
| `https://docs.litellm.ai/docs/...`                                                                         | 回答の主たる現行本文                                          |
| `https://raw.githubusercontent.com/BerriAI/litellm-docs/3c0d2ef3ef4890c705577eb74a79fc473139e829/docs/...` | レンダリングページで不足する場合のcommit固定Markdown fallback |

`llms.txt` は `/docs/` URLをほとんど含まず、`llms-full.txt` はリリース履歴が多くページ境界もないため、現行本文の索引・一括取得には使わない。

## 生成物

- `output/docs-urls.md` — 完全な `/docs/` URL一覧。frontmatterにsource、取得時刻、生成時刻を含む
- `output/docs-url-tree.md` — 子孫数付きのコンパクトなパスツリー。大分類の確認用

URL一覧とツリーは意図的に別ファイルとする。一覧はGrep用、ツリーはコンテキストへ最初に読み込む方位磁針である。raw sitemap、`output/selection.json`、`output/temp/` は `.gitignore` で除外する。

## 更新

`uv` と依存パッケージ（`requests`、`typer`）が利用可能な環境で、Skillディレクトリから次を実行する。

```sh
uv run webref_cli.py download-index --force
```

通常は `--force` を付けず、24時間のfreshnessチェックを使う。生成後、次を確認する。

- `docs-urls.md` の全URLがHTTPSかつ `docs.litellm.ai/docs/` prefix内である
- `docs-url-tree.md` に providers、proxy、routing、observability、pass_through などの主要領域が現れる
- raw sitemap由来のURL、selection manifest、取得本文が差分へ入っていない

## コマンド

```text
uv run webref_cli.py download-index --force
uv run webref_cli.py select-urls --keyword providers --limit 5
uv run webref_cli.py fetch-pages --manifest output/selection.json
uv run webref_cli.py --help
```

`select-urls` と `fetch-pages` は検証用の作業コマンドであり、選択ページ以外を取得しない。生成物の更新時もこの制約を維持する。
