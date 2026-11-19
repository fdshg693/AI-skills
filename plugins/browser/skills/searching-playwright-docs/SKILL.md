---
name: searching-playwright-docs
description: Searches Playwright's official documentation sources (docs/src/**/*.md — the source of truth for the public API and every playwright.dev guide) from a local snapshot, instead of answering from memory. Use when asked what a Playwright API method/option/event does or when it was added, how to do something in Playwright (auth, fixtures, locators, network mocking, tracing, CI, reporters, emulation, components …), which languages support a feature, or to quote/cite the official docs; also when writing Playwright code or skills that must match the documented API.
allowed-tools: Bash(uv run ${CLAUDE_SKILL_DIR}/*.py *) Read Grep
# 同梱ファイル:
#   - sync_playwright_docs.py: GitHub の microsoft/playwright から docs/src の MD を sparse clone で取得 + 索引生成（!`` で起動時に実行。7 日以内ならスキップ）
#   - search_playwright_docs.py: スナップショットの検索・セクション抽出ツール
#   - output/docs/: docs/src の MD コピー（生成物。手で編集しない。3 MB あるので gitignore）
#   - output/index.md, output/_meta.json: 生成された索引とメタ
#   - README.md: メンテナ向け。設計意図、取得対象の変え方
# 暗黙の前提:
#   - `git` と `uv` が PATH にあること（スクリプトは標準ライブラリのみ使用）
# 設計メモ:
#   - 約 3MB / 180 ファイルと巨大なので「全部読む」は不可。必ず検索 → セクション単位で読む
#   - 鮮度は 7 日。docs はリリース単位でしか動かないうえコピーが重いため長めに取っている
# 依存スキル: なし（ブラウザ操作そのものは using-playwright-cli）
meta:
  tag: []
  requires_repo_tools: none
  requires_env: none
  dependencies: git, uv
  requires_install: none
  requires_hooks: none
  requires_skills: none
  status: experimental
  description: Playwright 公式 docs/src のスナップショットを検索・セクション抽出する
  version: 1.0.0
---

!`uv run "${CLAUDE_SKILL_DIR}/sync_playwright_docs.py"`

# Playwright 公式ドキュメントを検索する

記憶ではなく `${CLAUDE_SKILL_DIR}/output/docs/`（microsoft/playwright `main` の `docs/src/**/*.md` のスナップショット）を根拠にする。
`docs/src` は公開 API と playwright.dev の各ガイドの **source of truth**。
上のコマンドで取得済み。エラーが出ていた場合は原因を伝えてから続行する。

## 使い方（全部読まない）

約 3MB / 180 ファイル。`api/class-page.md` だけで 184KB ある。
**まず検索し、ヒットしたセクションだけを読む。** `output/docs/` をまとめて Read したり Grep で流したりしない。

```bash
S="uv run ${CLAUDE_SKILL_DIR}/search_playwright_docs.py"

$S storage state reuse            # 全文検索（全語 AND、大小無視）。スコア順にファイル + path:line
$S --api Locator.click            # API エントリの位置（## async method: ... を検索）
$S --api Clock                    # クラスのメンバー一覧
$S --sections auth.md             # 見出し一覧（どのセクションを読むか決める）
$S --show auth.md#"Reusing signed in state"   # そのセクションだけ出力
$S --show api/class-locator.md#Locator.click  # API 1 エントリだけ出力（param/option 込み）
```

絞り込み・広げ方:

| オプション                        | 用途                                                                         |
| --------------------------------- | ---------------------------------------------------------------------------- |
| `--lang js\|python\|java\|csharp` | その言語向けファイル + 言語非依存ファイルだけ（`-js.md` などの接尾辞で判定） |
| `--path "test-*"` / `--path api/` | パスの glob または部分一致で限定（複数回指定可）                             |
| `--any`                           | 全語 AND ではなくどれか 1 語でヒット                                         |
| `--regex`                         | 語を正規表現として扱う                                                       |
| `--limit N` / `--per-file N`      | 表示ファイル数 / 1 ファイルあたりのヒット数（既定 12 / 6）                   |

`release-notes-*.md` はどの語でも大量にヒットして本来のガイドを押し下げるため、既定でスコアを下げてある。
**「いつ追加された機能か」を調べるときは明示的に** `--path "release-notes-*"` を付ける
（API 側は各エントリの `* since: v1.x` 行が一次情報）。

## 索引

ファイル単位の一覧は [output/index.md](output/index.md)（タイトル / 対象言語 / サイズ / API メンバー数）。
どのファイルを見るか当たりが付かないときだけ開く。大まかな構成:

| 場所                                                   | 内容                                                                                                         |
| ------------------------------------------------------ | ------------------------------------------------------------------------------------------------------------ |
| `output/docs/*.md`                                     | ガイド（auth, locators, network, emulation, ci, test-fixtures-js …）。`-js` / `-python` 等の接尾辞が対象言語 |
| `output/docs/api/`                                     | コア API リファレンス（`class-page.md`, `class-locator.md`, `class-browsercontext.md` …）                    |
| `output/docs/test-api/`                                | テストランナー API（`class-test.md`, `class-testconfig.md`, `class-testinfo.md` …）                          |
| `output/docs/test-reporter-api/`                       | レポーター API                                                                                               |
| `output/docs/electron-api/`, `output/docs/mobile-api/` | Electron / Android                                                                                           |

## docs/src の記法

生の doc ソースであって playwright.dev の HTML ではない。読むとき・引用するときに注意する。

- `## async method: Locator.click` / `## property: Page.clock` / `## event: Page.close` が API エントリ、
  続く `### param:` / `### option:` が引数。`* since: v1.14` が追加バージョン、`* langs: js` が対象言語
- `[`method: Page.goto`]` `[Locator]` はドキュメント内リンク記法。そのままユーザーに貼らず、通常の名前に直す
- コードブロックは `js` / `python async` / `python sync` / `java` / `csharp` に分かれている。
  **回答する言語のブロックだけを使う**（`--lang` で絞ると混入しにくい）
- `:::note` / `:::warning` は注記ブロック

## 回答するとき

- 根拠として `output/docs/` 内の相対パスと行番号、および upstream URL
  （`https://github.com/microsoft/playwright/blob/main/docs/src/<相対パス>`）を示す
- スナップショットは取得時点の upstream `main`（コミットは `output/_meta.json` の `source`）。
  ユーザーが使っているリリースより新しい記述がありうるので、バージョン依存の話題では `* since:` を確認し、
  断定できないときはその旨を添える
- ドキュメントにない挙動を聞かれたら、記憶で補わずに「docs/src には記述がない」と言い、
  必要なら upstream の `packages/` の実装を確認する

## スナップショットの更新

既定では 7 日以内に取得済みならスキップ。強制再取得:

```bash
uv run "${CLAUDE_SKILL_DIR}/sync_playwright_docs.py" --force
```

新しいリリースの直後や、`--sections` で期待する見出しが無いときは `--force` してから答える。
手元の playwright チェックアウトから取りたいときは `--repo-root <パス>` を付ける。
