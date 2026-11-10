# apify-docs

メンテナ向け。実行時の手順は [SKILL.md](SKILL.md)。

## 設計

[writing-skill-web](../../../cc-knowledge/skills/writing-skill-web/SKILL.md) の静的スナップショット（パターン1）+ ページ単位 `.md` 取得 + Store 検索。

| 取得物                                   | 役割                                                                                                    |
| ---------------------------------------- | ------------------------------------------------------------------------------------------------------- |
| `https://docs.apify.com/llms.txt`        | docs 全索引（約515行、449エントリ）。コミットする                                                       |
| `https://apify.com/llms.txt`             | apify.com 側索引（Store・料金・MCP・`agents.md`）。`output/apify-com-llms.txt` としてコミットする       |
| `output/excerpt.md`                      | llms.txt が200行超のため作った AI 抜粋（writing-skill-web 1.6節）。81件、手でレビュー済み。コミットする |
| `https://docs.apify.com/llms-full.txt`   | 約45MB。`Source: URL` のページ境界が0件で、セクション抽出が成立しない。**取得しない**                   |
| 各ページの `.md`                         | 公式の本文取得方法（docs.apify.com / apify.com の両方で `text/markdown`）。`fetch-page`                 |
| `https://api.apify.com/v2/store?search=` | 公開 Store 検索（トークン不要）。`search-store`                                                         |

`extract_doc_section.py` / `grep_doc_sections.py` / `inspect_section_markers.py` を同梱しない理由: llms-full.txt にページ単位の Source URL が無く、サイズも大きすぎる。形式が変わったら writing-skill-web の `inspect_section_markers.py` で再判定する。

`fetch_doc_page.py` は `docs.apify.com` / `apify.com` 以外のホストを拒否する。

## 抜粋のメンテナンス

- 抽出基準は [prompts/prompt_generate_excerpt.md](prompts/prompt_generate_excerpt.md)（各領域の入口ページ、Actor/storage の概念、AI 連携。API 個別エンドポイント・Academy 講座・法務文書は除外）
- 生成後に手で追加したもの: Claude / Claude Code CLI / Codex CLI / Cursor / GitHub Copilot CLI / VS Code の各 integration、MCP connectors
- `aim` の既定モデルは `gemini-3.8-flash`（この環境の `aim` で選べるモデルに合わせた）

```text
python webref_cli.py download --force
python webref_cli.py check-excerpt        # MISSING/TITLE MISMATCH は excerpt.md を直接編集して直す
python webref_cli.py generate-excerpt --force   # 大きく崩れたときだけ。再生成後は再レビュー
```

## コマンド

```text
python webref_cli.py download
python webref_cli.py fetch-page actors cli/docs/reference
python webref_cli.py fetch-page https://apify.com/agents.md
python webref_cli.py search-store "google maps" --limit 5
python webref_cli.py check-urls --url https://docs.apify.com/llms.txt --url https://apify.com/llms.txt
```
