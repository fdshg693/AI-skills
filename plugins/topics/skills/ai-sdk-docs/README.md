# ai-sdk-docs

メンテナ向け。実行時の手順は [SKILL.md](SKILL.md)。

## 設計

[writing-skill-web](../../../cc-knowledge/skills/writing-skill-web/SKILL.md) の静的スナップショット + 公式検索フォールバック。

| 取得物                                  | 役割                                                                                        |
| --------------------------------------- | ------------------------------------------------------------------------------------------- |
| `https://ai-sdk.dev/llms.txt`           | 公式の短い案内（検索 URL と起点）。51行なので AI 抜粋は作らない                             |
| `https://ai-sdk.dev/sitemap.md`         | 全パス索引。スキル対象はサイト全体なので、ここからさらに抜粋しない                          |
| `https://ai-sdk.dev/llms-full.txt`      | 全文ダンプ。`inspect-markers` では `# Title` / `Source: URL` が不成立。本文取得には使わない |
| `https://ai-sdk.dev/api/search-docs?q=` | 公式検索。`search` サブコマンド                                                             |
| 各ページの `.md`                        | 公式の本文取得方法。`fetch-page` サブコマンド                                               |

`extract_doc_section.py` / `grep_doc_sections.py` を同梱しない理由: ダンプにページ単位の Source URL が無い。ダンプ形式が変わったら `python webref_cli.py inspect-markers output/llms-full.txt` で再判定する。

`output/llms-full.txt` は約6MB のため gitignore。`llms.txt` と `sitemap.md` はコミットする。

## コマンド

```text
python webref_cli.py download
python webref_cli.py search ToolLoopAgent
python webref_cli.py fetch-page docs/agents
python webref_cli.py inspect-markers output/llms-full.txt
```
