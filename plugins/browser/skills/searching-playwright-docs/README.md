# searching-playwright-docs（メンテナ向け）

Playwright の公式ドキュメントソース `docs/src/**/*.md` をスナップショットして検索可能にするスキル。
実行時の判断・手順は [SKILL.md](SKILL.md)。ここは設計意図のみ。

参考にしたのは同ディレクトリの [using-playwright-cli](../using-playwright-cli/README.md)。
「一次情報を `output/` にスナップショットし、`SKILL.md` は薄いルーターにする」構成を踏襲している。

## 何をミラーしているか

`docs/src` 配下の **MD ファイルのみ**（約 180 ファイル / 約 3MB）。`docs/src/images/**` は除外。
`docs/src` は公開 TypeScript 型と playwright.dev の source of truth で、
`utils/doclint` が実装との突き合わせに使っているため、API の挙動・オプション・対応言語の一次情報になる。

## なぜ `git` の sparse clone で取るのか

using-playwright-cli は `gh api`（Contents API）で 1 ファイルずつ取っている。こちらは 180 ファイルあり、
同じ方式だと毎回 180+ 回叩くことになる（未認証は 60 req/h で即死、認証済みでも遅い）。

そこで `git clone --depth 1 --filter=blob:none --sparse` を一時ディレクトリに行い、
`git sparse-checkout set --no-cone '/docs/src/**/*.md'` で MD の blob だけを落としてから `output/docs/` にコピーする。
ネットワークの往復は実質 1 回、依存は `git` だけ。一時ディレクトリは毎回消す（git のオブジェクトは読み取り専用なので
Windows では属性を外してから消す）。

もともとは microsoft/playwright のクローンの中に置いていて、親ディレクトリの `docs/src` をコピーしていた。
fdshg693/AI へ移すときに Playwright 本体を持ち込まないため、upstream から取る形に作り替えた。
手元のチェックアウトを使いたいときのために `--repo-root` は残してある。

## 何を git で追跡するか

`output/docs/`（3 MB）は `.gitignore` で無視し、`output/index.md` と `output/_meta.json` だけ追跡する
（topics の litellm-docs・ai-sdk-docs と同じ扱い）。スキルを読み込むたびに `!` の同期が走り、
7 日以内ならスキップ、無ければ取りに行く。

## なぜ「検索スキル」なのか

3MB は読めない。`api/class-page.md` 単体で 184KB ある。
そこで `search_playwright_docs.py` を同梱し、`SKILL.md` は
**検索 → セクション単位で読む** という動線だけを規定している。

`--show path#heading` がこのスキルの肝で、ヒットしたセクション（`## async method: Locator.click`
とその `### param:` / `### option:` まで）だけを切り出せる。ファイル全体を Read させない。

## ファイル構成

| パス                        | 位置づけ                                                                                  |
| --------------------------- | ----------------------------------------------------------------------------------------- |
| `SKILL.md`                  | 実行時のルーター。検索コマンドと docs/src の記法                                          |
| `sync_playwright_docs.py`   | upstream からのスナップショット + 索引生成。`SKILL.md` の `` !`...` `` で起動時に必ず走る |
| `search_playwright_docs.py` | 検索 / API 検索 / 見出し一覧 / セクション抽出                                             |
| `output/docs/**/*.md`       | `docs/src` のコピー（生成物。gitignore）                                                  |
| `output/index.md`           | ファイル単位の索引（タイトル・対象言語・KB・API メンバー数）                              |
| `output/_meta.json`         | 取得日時、取得元コミット、元パス対応、ファイルごとのメタ（`search` 側のフィルタが参照）   |

`output/_meta.json` は鮮度判定だけでなく検索時のファイル列挙にも使う。
`--lang` フィルタはここに入っている `langs`（ファイル名の `-js` / `-csharp-java` 接尾辞から判定）を見ている。

## 鮮度を 7 日にしている理由

`FRESHNESS = timedelta(days=7)`（`sync_playwright_docs.py`）。

- スナップショットが大きく、毎回 180 ファイルを取り直すのは無駄
- docs はリリース単位でしか動かない

新しいリリースの直後は `--force` を明示する。

## 実装メモ

- 両スクリプトとも標準ライブラリのみ。`uv run` で起動する（PEP 723 の空の依存宣言付き）。同期は `git` を使う
- コードフェンス内の `# コメント` を見出しと誤認しないよう、`headings()` で ``` を追跡している
  （Python サンプルの `# Navigate to a page` を見出しとして拾う事故があった）
- `release-notes-*.md` は語がばらまかれていてどの検索でも上位に来るため、スコアを 1/4 に落としている
  （`RELEASE_NOTES_PENALTY`）。「いつ入った機能か」を調べるときは `--path "release-notes-*"` で明示的に呼ぶ
- `output/` 内で列挙から外れたファイルは次回同期時に自動削除される（`remove_stale_outputs`）

## 取得対象を変えるとき

`sync_playwright_docs.py` の定数を編集する。

- `REPO_URL` / `REF` — 取得元リポジトリとブランチ
- `DOCS_SRC_REL` — 取得元ディレクトリ（リポジトリルートからの相対。sparse-checkout のパターンにも使う）
- `SUFFIXES` — 拾う拡張子。現状 `.md` のみ
- `SKIP_DIRS` — 除外するトップレベルディレクトリ。現状 `images`

変更後は `--force` で同期し、`output/index.md` に反映されること、
`search_playwright_docs.py` の各モードが動くことを確認する。
