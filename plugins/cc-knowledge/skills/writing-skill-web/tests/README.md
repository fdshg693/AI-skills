# `writing-skill-web` テンプレートスクリプトのテスト

このディレクトリは、`../scripts/*.py` に同梱されている11個のコピー用テンプレート(`download_web_reference.py`・`download_github_docs.py`・`check_urls.py`・`generate_llms_excerpt.py`・`check_llms_excerpt.py`・`inspect_section_markers.py`・`extract_doc_section.py`・`grep_doc_sections.py`・`download_url_index.py`・`select_url_index.py`・`fetch_selected_pages.py`)と、それらを束ねる`webref_cli.py`を検証するpytestスイートです。

## スコープ: このスキル自身のテンプレートのみ

**これらのテストは`writing-skill-web`自身の同梱テンプレートを検証するためのものであり、このテンプレートをコピーして作られる個別スキル(`vscode-docs`・`claude-code-docs`等)側にテストを用意する運用ではありません。**

理由:

- テンプレートは「コピーしてDEFAULT_\*定数を書き換える」前提の型であり、コピー先ごとにテストを複製すると保守コストがテンプレートの利点を上回る
- テンプレートのロジック(frontmatter+freshness契約、URLバリデーション、セクション抽出の正規表現境界判定など)はコピー先で変わらない共通部分であり、ここで一度検証しておけば十分
- コピー先固有の検証(実際のサイトの`llms.txt`が本当に想定形式か等)は`inspect_section_markers.py`のようなスクリプト自体が担う実行時チェックであり、静的なユニットテストの対象ではない

新しいスキルを作る際にこの`tests/`ディレクトリはコピーしない。

## 実行方法

リポジトリルートの`pyproject.toml`の`[tool.uv.workspace]`に`skills/plugins/cc-knowledge/skills/writing-skill-web`が登録されているため、`uv sync`で依存関係(`requests`・`typer`)が解決される。

```bash
uv sync
uv run pytest skills/plugins/cc-knowledge/skills/writing-skill-web/tests
```

**引数無しの`uv run pytest`では他のworkspace memberのテストと混ざって収集される可能性があるため、このディレクトリを明示パスで指定して実行すること。**

## ファイル構成

```text
tests/
├── README.md                          # このファイル
├── conftest.py                        # scripts/をsys.pathに追加するだけの共通セットアップ
├── test_download_web_reference.py
├── test_download_github_docs.py
├── test_check_urls.py
├── test_generate_llms_excerpt.py
├── test_check_llms_excerpt.py
├── test_inspect_section_markers.py
├── test_extract_doc_section.py
├── test_grep_doc_sections.py
├── test_webref_cli.py
└── fixtures/
    ├── sample_llms.txt                # 索引フィクスチャ(frontmatter付き、3セクション・7エントリ)
    ├── sample_excerpt_ok.md           # sample_llms.txtと矛盾しない抜粋(正常系)
    ├── sample_excerpt_broken.md       # MALFORMED/MISSING/TITLE MISMATCH/DESC DRIFT/STALEを1ファイルで再現
    ├── sample_llms_full.txt           # `# タイトル`+`Source: URL`型の全文ダンプフィクスチャ(3ページ)
    ├── sample_prompt_generate_excerpt.md  # <<...>>を埋め済みのプロンプト
    ├── sample_sitemap*.xml                # 名前空間付きurlset/ネストしたsitemapindex
    └── sample_llms_index.txt              # llms.txt形式URL索引
```

## 設計方針

- ネットワーク呼び出し(`requests.get`・`urllib.request.urlopen`)、`gh api`呼び出し(`download_github_docs.run_gh`)と`aim` CLI呼び出し(`subprocess.run`)は全テストで`monkeypatch`により置き換えている。実際の外部通信は一切行わない
- 各スクリプトの`main()`は`sys.argv`をmonkeypatchして呼び出す(スクリプト側のargparseが`parse_args()`で素の`sys.argv`を読む設計を変えていないため)
- `sample_excerpt_broken.md`は意図的に壊れたフィクスチャであり、「直す」対象ではない。`check_llms_excerpt.py`が報告すべき問題カテゴリ(MALFORMED/MISSING/TITLE MISMATCH/DESC DRIFT/STALE)を1ファイルで網羅するために存在する
