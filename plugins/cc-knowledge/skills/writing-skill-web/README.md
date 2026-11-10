# writing-skill-web スキルについて

`writing-skill-web` は、WEB上の情報を根拠にするスキルを作る際に「静的スナップショット参照」と「動的検索/取得」のどちらのパターンを使うかを判断し、実装用のテンプレートを提供するメタスキルである。このファイルは人間のメンテナ向けで、由来・ファイルの位置付け・命名変更の経緯をまとめる。Claudeが実行時に読むのは[SKILL.md](SKILL.md)であり、こちらは参照しない。

## なぜこのスキルがあるか

`vscode-docs`（`skills/plugins/others/skills/`）・`github-copilot-docs`・`vscode-copilot-docs`（`copilot-plugins/meta/`）など、WEBドキュメントを参照する複数のスキルで、以下のロジックがほぼ同じ形で個別に実装されていた。

- ダウンロード結果への`fetched_at`記録とfreshnessチェック(既定24時間)
- `llms.txt`/`llms-full.txt`候補パスの存在確認
- 索引が大きい場合のAI生成抜粋(excerpt)とその機械バリデーション
- `# タイトル`+`Source: URL`形式の全文ダンプからのセクション抽出

個別実装のたびに同じ設計判断（なぜ24時間か、なぜAIに自由文要約をさせず構造化出力を強制するか等）をゼロから捻り出すコストが無視できなくなったため、判断基準とテンプレート一式を1箇所にまとめて`writing-skill`から派生させた。

## `scripts/`はライブラリではなくコピー用テンプレートである

`scripts/`配下の各Pythonファイルは、**このスキルが直接実行するものではない**。新しいスキルを作る際に、対象スキルのディレクトリへコピーしてから`DEFAULT_*`定数などを書き換えて使う「ひな形」である。

この設計を選んだ理由（[web-patterns-reference.md](web-patterns-reference.md) 1.1節・1.5節も参照）:

- 単発の`skills/plugins/*/skills/`配下のスキルでは、共有`scripts/`モジュールを1つ上の階層に作るより、スキル単体にスクリプトを1本コピーする方がシンプルで、依存関係も追跡しやすい
- 複数スキルで本当にロジックを共有したい場合（プラグイン内など）は、共通モジュールを1つ上の階層に置くパターンもあるが、それは例外的な対応であり本スキルの既定ではない

そのため、**このスキル自身の`scripts/`を更新しても、既にコピーして使っている個別スキル(`vscode-docs`等)には自動反映されない**。個別スキル側のコピーが古い設計のままになっていないかは、`skill-maintenance`スキルのような横断メンテナンス作業で気づいた時に見直す。

## 依存関係の全体像

```text
writing-skill        … name/description/本文構造などスキル一般の作法（必須の前提）
  └─ writing-skill-web … WEB固有の判断（静的/動的パターンの選択、テンプレート提供）
       ├─ tav-cli / tav-lit … 動的検索/取得の実装（クライアントを重複実装しない）
       └─ aim CLI          … 索引が大きい場合のAI生成抜粋(excerpt)でのAIモデル単発呼び出し
```

## ファイル名の経緯

設計詳細ファイルはもともと`reference.md`という名前だったが、`writing-skill`の[bestpractices.md](../writing-skill/bestpractices.md)が定める「ファイル名は内容が分かるものにする（`reference.md`より`skills-reference.md`のように）」という基準に反していたため、`web-patterns-reference.md`へ改名した。新しく参照ファイルを追加する場合も、`reference.md`のような曖昧な名前は避けること。

## ファイル構成

```text
writing-skill-web/
├── SKILL.md                      # 判断フロー(静的/動的の分岐)とチェックリスト
├── README.md                     # このファイル(人間向け設計意図)
├── web-patterns-reference.md     # 設計詳細・実例(旧reference.md)
├── pyproject.toml                # scripts/をuv workspaceメンバーにするためだけの設定(下記「テスト」参照)
├── scripts/                      # コピー用テンプレート一式(このスキル自身は実行しない)
│   ├── webref_cli.py             # 統一CLI(Typer)。コピーした各スクリプトを1つの入口にまとめる
│   ├── download_web_reference.py
│   ├── download_github_docs.py      # GitHubリポジトリのdocsを`gh api`でミラー
│   ├── check_urls.py
│   ├── generate_llms_excerpt.py
│   ├── prompt_generate_excerpt.template.md
│   ├── check_llms_excerpt.py
│   ├── inspect_section_markers.py
│   ├── extract_doc_section.py
│   ├── grep_doc_sections.py
│   ├── download_url_index.py        # sitemap/llms.txtの正規化とtree生成
│   ├── select_url_index.py          # URL prefix/keyword選択
│   └── fetch_selected_pages.py      # 明示選択ページだけを取得
└── tests/                        # scripts/自体を検証するpytest(コピー先スキルには複製しない。tests/README.md参照)
    ├── README.md
    ├── conftest.py
    ├── test_*.py                 # スクリプトごとに1ファイル + webref_cli.py用
    └── fixtures/                 # llms.txt/llms-full.txt/sitemapサンプル等
```

`webref_cli.py`を追加した設計意図: 従来は`scripts/`配下のテンプレートを新しいスキルにコピーしたあと、SKILL.md本文で各スクリプトを`python download_xxx.py`のように個別のファイル名で都度呼び分けていた。`webref_cli.py`はTyperで実装した薄いディスパッチャで、コピーした各スクリプトをサブコマンドにまとめ、引数はそのスクリプト自身のargparseへそのまま転送する。既存のサブコマンドに加え、URLインデックス用の`download-index`/`select-urls`/`fetch-pages`も登録できる。

## テスト

`scripts/*.py`は「コピーして使う」テンプレートだが、テンプレート自身のロジック(frontmatter+freshness契約、URLバッチチェック、excerptのverbatim組み立て+バリデーション、セクション抽出の境界判定など)はコピー先が変わっても共通なので、[tests/](tests/README.md)でこのスキル内に一度だけ検証している。

- テスト対象はあくまで`writing-skill-web`同梱の`scripts/*.py`自身であり、これらをコピーして作る個別スキル(`vscode-docs`等)に`tests/`を複製する運用ではない(理由・実行方法は[tests/README.md](tests/README.md)参照)
- リポジトリルートの`pyproject.toml`の`[tool.uv.workspace]`にこのディレクトリ(`skills/plugins/cc-knowledge/skills/writing-skill-web`)を登録しており、`uv sync`で`requests`/`typer`が解決される。このスキル直下の`pyproject.toml`はこの登録のためだけに存在し、`scripts/`を配布可能なパッケージにする意図はない
- 実行: `uv sync && uv run pytest skills/plugins/cc-knowledge/skills/writing-skill-web/tests`(引数無しの`uv run pytest`だけでは収集されない場合がある理由は[tests/README.md](tests/README.md)参照)

## 保守時の注意

- `scripts/`配下のいずれかを更新したら、次の3箇所を合わせて更新する。テンプレートとドキュメント・テストが食い違うと、コピー先での適応作業がそのまま間違った実装として複製される
  1. [web-patterns-reference.md](web-patterns-reference.md)内の対応する節（該当スクリプトの使い方・設計上のポイント）
  2. [tests/](tests/README.md)内の対応するテストファイル(挙動が変わったなら、まずテストを直してから実装を直す)
  3. スクリプトを追加/削除/リネームした場合は[scripts/webref_cli.py](scripts/webref_cli.py)の`SUBCOMMANDS`テーブル

## GitHub docsテンプレート

`download_github_docs.py`は、`codegraph-docs`・`pr-agent-docs`で個別に書かれていた「`gh api`でリポジトリのdocsディレクトリをミラーし、frontmatterから`summary.md`を生成し、`_meta.json`でfreshness判定する」ダウンローダーを、リポジトリ・docsルート・ref・目次ファイルを引数/定数化して一般化したもの。`llms.txt`とGitHubの両方がある場合にどちらを使うかはテンプレート側で決めず、スキル作成時の判断に委ねている(判断材料は[web-patterns-reference.md](web-patterns-reference.md) 1.12節)。既存の`codegraph-docs`等は自動では置き換わらない。

## URLインデックステンプレート

`download_url_index.py`はXML sitemap(`urlset`/`sitemapindex`)または`llms.txt`を取得し、フラグメント除去・重複排除済みのMarkdown URLリスト(`output/urls.md`)と、深さ制限付きのコンパクトなパスツリー(`output/url-tree.md`)を生成する。子sitemapもHTTPSの許可ホスト内でのみ、文書数・深さ・サイズの上限付きで辿る。raw入力は保存せず、URLリストのfrontmatterに`source`/`fetched_at`を記録してfreshness(既定24時間)を適用する。

`select_url_index.py`はURLリストを`--include-prefix`/`--exclude-prefix`と大文字小文字を区別しない`--keyword`/`--exclude-keyword`で絞り、フィルタ条件を含むJSON manifestを生成する。`fetch_selected_pages.py`は`--url`またはmanifestだけを入力として受け、HTTPS・許可ホスト・許可prefix・リダイレクトを再検証し、ページ数と本文サイズを制限して`output/temp/`へ書き出す。未選択のURLを推測してクロールする処理はない。

3本とも`webref_cli.py`の`download-index`、`select-urls`、`fetch-pages`から呼び出す。個別スキルへコピーする場合は`SUBCOMMANDS`と`DEFAULT_*`を対象サイトに合わせ、raw indexと取得本文を`.gitignore`で除外する。
