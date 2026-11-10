# vercel-docs

メンテナ向け。実行時の手順は [SKILL.md](SKILL.md)。

## 設計

[writing-skill-web](../../../cc-knowledge/skills/writing-skill-web/SKILL.md) の静的スナップショット参照（パターン1）+ 公式 `.md` による本文取得。Vercel は `vercel.com/docs` 配下の機械可読リソースが整備されているため、HTML スクレイピングや URL クロールは行わない。

| 取得物                                  | 役割                                                                                                     | 扱い                               |
| --------------------------------------- | -------------------------------------------------------------------------------------------------------- | ---------------------------------- |
| `https://vercel.com/docs/llms.txt`      | エージェント向けの短い案内（CLI / MCP / API / 主要索引への導線、約50行）                                 | コミット                           |
| `https://vercel.com/docs/products.md`   | 全製品の一覧（約50行）。質問の当たりを付ける起点                                                         | コミット                           |
| `https://vercel.com/docs/sitemap.md`    | 意味的索引（約1336エントリ、約400KB）。Type / Lastmod / Summary / Prerequisites / Topics 付き。Grep 専用 | コミット                           |
| `https://vercel.com/docs/taxonomy.json` | 正規製品名・別名・非推奨/退役（`aliases` / `status` / `supersededBy` / `retiredAt`）                     | コミット                           |
| `https://vercel.com/docs/llms-full.txt` | 全ドキュメント + REST API の連結ダンプ（約9.6MB）。フォールバック Grep 専用                              | gitignore、`--include-full` で取得 |
| 各ページの `.md`                        | 公式の本文取得方法（例: `https://vercel.com/docs/functions.md`）。`fetch-page` サブコマンド              | 都度 `output/temp/`                |

## なぜ AI 抜粋（excerpt）を作らないか

writing-skill-web は「索引が200行以上なら excerpt を作る」と定めるが、これは `llms.txt` 索引が巨大で大半が無関係という前提の指針。Vercel の `llms.txt` は約50行の短い導線で、巨大なのは `sitemap.md`（既に Summary / Topics 付きの意味的索引）である。このスキルの対象は Vercel ドキュメント全体で、除外すべき「無関係な大半」が存在しないため、`sitemap.md` をそのまま Grep する方が正確で安い。`ai-sdk-docs` も同じ判断をしている。

## なぜ `extract_doc_section.py` / `grep_doc_sections.py` を同梱しないか

これらは `llms-full.txt` が `# Title` の直後に `Source: URL` を置く形式（`(# タイトル / Source: URL)` ペア）であることを前提にする。Vercel の `llms-full.txt` はページ境界が次の形で、`source:` が `# Title` より**前**に来る:

```text
--------------------------------------------------------------------------------
title: "Access tokens"
source: "https://vercel.com/docs/accounts/access-tokens"
--------------------------------------------------------------------------------

# Access tokens
```

したがってセクション抽出は成立しない（`uv run "${CLAUDE_SKILL_DIR}/webref_cli.py" inspect-markers "${CLAUDE_SKILL_DIR}/output/llms-full.txt"` で再判定できる。`Source:` は大文字始まりでないため既定パターンにも一致しない）。本文取得は `.md` 付与で行う。ダンプ形式が将来 `(# Title / Source: URL)` に変わったら、その時点でこれら2スクリプトの同梱を検討する。

## コマンド

```text
uv run "${CLAUDE_SKILL_DIR}/webref_cli.py" download
uv run "${CLAUDE_SKILL_DIR}/webref_cli.py" download --force
uv run "${CLAUDE_SKILL_DIR}/webref_cli.py" download --include-full
uv run "${CLAUDE_SKILL_DIR}/webref_cli.py" fetch-page docs/functions docs/environment-variables
uv run "${CLAUDE_SKILL_DIR}/webref_cli.py" check-urls --url https://vercel.com/docs/llms.txt --only-broken
uv run "${CLAUDE_SKILL_DIR}/webref_cli.py" inspect-markers "${CLAUDE_SKILL_DIR}/output/llms-full.txt"
```

スキル起動時の動的コンテキスト注入は `uv run "${CLAUDE_SKILL_DIR}/webref_cli.py" download`（この環境では素の `python` に `requests` / `typer` が入っていないため `uv run` を使う。`meta.requires_repo_tools: uv`）。

## 保守時の注意

- `sitemap.md` / `products.md` / `taxonomy.json` / `llms.txt` は24時間の freshness で更新される。リポジトリ上は差分が出るので、更新は通常のスキル実行に任せ、手で編集しない
- Vercel 側の索引構成（例: `.graph.md` の追加、`/docs/graph.json` の公開）が変わったら [SKILL.md](SKILL.md) の「索引と本文の取り方」を更新する
- 候補 URL の存在確認は `check-urls` に複数 URL をまとめて渡す（1件ずつ WebFetch しない）
