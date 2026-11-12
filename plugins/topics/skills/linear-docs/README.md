# linear-docs

メンテナ向け。実行時の手順は [SKILL.md](SKILL.md)。

## 設計

[writing-skill-web](../../../cc-knowledge/skills/writing-skill-web/SKILL.md) の静的スナップショット参照（パターン1）+ 公式 `.md` による本文取得。構成は [vercel-docs](../vercel-docs/README.md) とほぼ同じで、ダンプ（`llms-full.txt`）とセクション抽出を持たない版。

| 取得物                                                                                   | 役割                                                                                                                                      | 扱い                              |
| ---------------------------------------------------------------------------------------- | ----------------------------------------------------------------------------------------------------------------------------------------- | --------------------------------- |
| `https://linear.app/llms.txt`                                                            | サイト全体の索引（約250行）。`## Website` / `## Documentation`（約105ページ）/ `## Developers`（約26ページ）の3節。リンクは全て `.md` URL | コミット（`output/llms.txt`）     |
| 各ページの `.md`                                                                         | 公式の本文取得方法（例: `https://linear.app/docs/triage.md`）。`fetch-page` サブコマンド。先頭の共通 MCP 案内行は除去して保存             | 都度 `output/temp/`               |
| `https://linear.app/changelog.md`                                                        | 最新 約20件の Changelog（約75KB）。`fetch-page changelog`                                                                                 | 都度 `output/temp/`               |
| `https://raw.githubusercontent.com/linear/linear/master/packages/sdk/src/schema.graphql` | GraphQL SDL（約1.4MB）。`schema` サブコマンド。1行目に `# fetched_at:` を付けて freshness 判定                                            | 都度 `output/temp/schema.graphql` |

## 採用しなかった方式

- **`llms-full.txt` + `extract_doc_section.py` / `grep_doc_sections.py` / `inspect_section_markers.py`** — `https://linear.app/llms-full.txt` は HTTP 200 を返すが中身は SPA の HTML フォールバックで、ダンプは存在しない。`/docs/llms.txt`・`/developers/llms.txt` とその `-full` 版は 404。全ページを自前で結合してダンプを作る案もあるが、`.md` の都度取得で足り、保守対象が増えるだけなので作らない。このため `download` はステータスコードではなく Content-Type（`text/plain`）と先頭行（`# Linear`）で取得物を検査する
- **`sitemap.xml` を索引に使う** — llms.txt とほぼ同じページ集合で、タイトルも分類も無い
- **GraphQL スキーマをコミットする** — 約1.4MBでほぼ毎週更新され、差分が膨らむ。必要時に取得して Grep する
- **Changelog の個別エントリを索引化する** — llms.txt に個別エントリは無く（sitemap に約255件）、「最近の変更」には `/changelog.md` の最新分で足りる
- **AI 抜粋（excerpt）** — llms.txt は約250行と小さく、Documentation / Developers の両方が対象範囲なので除外すべき大半が無い。Grep でそのまま使う
- **ドキュメントの GitHub ソースから取得する** — `linear` org に docs リポジトリは公開されていない

## コマンド

```text
uv run "${CLAUDE_SKILL_DIR}/webref_cli.py" download
uv run "${CLAUDE_SKILL_DIR}/webref_cli.py" download --force
uv run "${CLAUDE_SKILL_DIR}/webref_cli.py" fetch-page docs/triage developers/graphql
uv run "${CLAUDE_SKILL_DIR}/webref_cli.py" fetch-page changelog
uv run "${CLAUDE_SKILL_DIR}/webref_cli.py" schema
uv run "${CLAUDE_SKILL_DIR}/webref_cli.py" check-urls --url https://linear.app/llms.txt --url https://linear.app/llms-full.txt
```

スキル起動時の動的コンテキスト注入は `uv run "${CLAUDE_SKILL_DIR}/webref_cli.py" download`（素の `python` に `requests` / `typer` が入っていないため `uv run` を使う）。

## 保守時の注意

- `output/llms.txt` は24時間の freshness で更新される。リポジトリ上は差分が出るので、更新は通常のスキル実行に任せ、手で編集しない
- Linear が `llms-full.txt` の実体や分割版 llms.txt を公開したら、`check-urls` で Content-Type を確認したうえで、セクション抽出スクリプトの同梱を検討する
- llms.txt の節構成（`## Documentation` / `## Developers`）や `.md` 先頭の共通行の文言が変わったら、[SKILL.md](SKILL.md) と `fetch_doc_page.py` の `AGENT_NOTICE_PREFIX` を更新する
- スキーマの置き場所（`linear/linear` の `master`・`packages/sdk/src/schema.graphql`）が変わったら `fetch_graphql_schema.py` の `SCHEMA_URL` を更新する（llms.txt の `### GraphQL Schema` 節に現在のリンクがある）
