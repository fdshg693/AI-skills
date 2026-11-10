---
# WEB情報(ダウンロード済スナップショット参照 / その場での動的検索・取得)を扱うスキルを作るためのメタスキル
# writing-skillの手順・チェックリストは前提として重複させず、WEB固有の判断だけを扱う
name: writing-skill-web
description: Use when creating or editing a skill that needs web content — either a pre-downloaded/cached reference snapshot (XML sitemap or llms.txt URL index, or Markdown docs mirrored from a GitHub repository via gh api, refreshed on a freshness window) or dynamic on-the-spot web search/fetch of unknown URLs. Covers choosing between the static-snapshot pattern and the dynamic-query pattern, provides reusable sitemap/llms.txt normalization, compact-tree, selection, constrained-fetch, and GitHub docs-mirror templates, plus freshness checks and an AI-generated excerpt workflow for large indexes. For general skill-writing practice (naming, description, structure, checklist) see writing-skill first — this skill does not repeat it. For dynamic search/fetch, delegates to tav-cli/tav-lit rather than duplicating a client.

# 依存関係:
#   - writing-skillスキルへの依存: 必須の前提。name/description/本文構造などの一般原則はそちらに従う
#   - tav-cli・tav-litスキル(tools/_plugin/my-tools/skills配下)への依存: 動的検索/取得が必要な場合はまずこれらを使う想定。クライアントを重複実装しない
#   - 実運用例(出自メモ。スキル作成に必要なテンプレートはすべてscripts/配下に同梱済みで、
#     スキル外のフォルダを読みに行く必要はない):
#     skills/plugins/others/skills/vscode-docs, copilot-plugins/meta/{github-copilot-docs,vscode-copilot-docs},
#     skills/plugins/topics/skills/codegraph-docs, skills/plugins/cicd/skills/pr-agent-docs(GitHub取得の実例)
#
# 由来・scripts/のコピー前提テンプレートという性質・命名変更の経緯は同階層のREADME.md参照（人間のメンテナ向け）
meta:
  tag: []
  requires_repo_tools: aim, tav
  requires_env: none
  dependencies: requests, typer, uv, gh
  requires_install: none
  requires_hooks: none
  requires_skills: writing-skill, tav-cli, tav-lit, aim-cli
  status: stable
  description: no description
  version: 1.2.4
---

# WEB情報を扱うスキルの作り方

新しく作る・編集するスキルが「WEB上の情報」を根拠にする場合に、**静的スナップショット参照**と**動的検索/取得**のどちらのパターンを使うべきかを判断し、その型に沿った実装を進めるためのメタスキル。

**REQUIRED BACKGROUND:** スキル一般の作法(name/description/本文構造/チェックリスト)は**writing-skillスキル**が前提。このスキルはWEB固有の判断だけを扱い、writing-skillの内容は繰り返さない。

## 最初の判断: どちらのパターンか

```text
対象URLは事前に分かっている固定の情報源(公式ドキュメント等)で、
内容が数時間〜数日単位でしか変わらないか?
  Yes -> 静的スナップショット参照パターン(下記)
  No、対象URL/クエリがその場ごとに変わる、または最新性が重要 -> 動的検索/取得パターン(下記)

両方当てはまる(索引は静的スナップショットだが、載っていない場合は動的に探したい)
  -> 静的スナップショットをまず参照し、見つからない場合だけ動的検索にフォールバックする
     (vscode-docs/github-copilot-docsスキルの「補足」節がこの実例)
```

静的スナップショットの**取得元**は、サイト側(`llms.txt`/`llms-full.txt`/sitemap → パターン1・1b)と、ドキュメントのソースMarkdownを置いたGitHubリポジトリ(→ パターン1c)の2系統がある。両方ある場合にどちらへ寄せるか・ミックスするかは**このメタスキルでは決めない**。対象サイトごとに、作成時に実物を見て判断する(判断材料は [web-patterns-reference.md](web-patterns-reference.md) 1.12節)。

## パターン1: 静的スナップショット参照

対象ドキュメントを事前にダウンロードしてファイルに保存し、Claudeはそのファイルを読んで回答する。`llms.txt`/`llms-full.txt`のような索引・全文ダンプを公開しているサイト向け。

- 同梱スクリプトはすべて[scripts/webref_cli.py](scripts/webref_cli.py)(Typer製の統一CLI)経由で実行する。新しいスキルにコピーした各スクリプトを個別に`python download_xxx.py`のように都度呼び分けるのではなく、`python webref_cli.py <subcommand>`という1つの入口に統一する(詳細は本節末尾)
- スキル起動時に**必ず**ダウンロードスクリプトを実行させる(判断をClaudeに委ねず、`!`記号の直後にバッククォートでコマンドを囲む動的コンテキスト注入の記法、例えば`python webref_cli.py download`をそう囲んだ形、で確実に実行する)
- ダウンロード結果には`fetched_at`(取得時刻)を記録し、一定期間(既定24時間)以内なら再取得をスキップする。強制更新用に`--force`を用意する
- `llms-full.txt`(全文)が無いサイトも多い。索引(`llms.txt`)しか無い場合は、本文取得にWebFetchを都度使う指示を本文に書く(`vscode-docs`/`github-copilot-docs`スキルの実例を参照)
- 索引(`llms.txt`)から、スキルの目的に関連するエントリだけを集めた**AI生成の抜粋(excerpt)ファイル**を用意する。**索引が200行以上なら必ず**生成し、200行をはるかに下回っていても、目的のパスが索引のごく一部しか占めないなら積極的に生成する。生成には同梱の [scripts/generate_llms_excerpt.py](scripts/generate_llms_excerpt.py) と [scripts/prompt_generate_excerpt.template.md](scripts/prompt_generate_excerpt.template.md) を新しいスキルにコピーして使う(aim CLIによるAIモデル単発呼び出し)。プロンプトには**構造化された出力を強制する指示を必ず入れる**(自由文の要約は不可。同梱ひな形は「URLを元索引から文字単位でコピーして1行1件」を強制し、`- [Title](URL)`エントリの組み立てはスクリプト側が元索引からverbatimで行うため、後段のスクリプトバリデーションが可能になる)。生成後は同梱の [scripts/check_llms_excerpt.py](scripts/check_llms_excerpt.py) のコピーで形式と元索引との一致(URL実在・タイトル一致)を検証し、問題が見つかったら**AIモデルを再度呼び出さず**、抜粋ファイルを自分で直接編集して修正→再チェックする(手順詳細は [web-patterns-reference.md](web-patterns-reference.md) 1.6節)
- 対象サイトに`llms.txt`/`llms-full.txt`(ルート、ガイド単位など候補が複数あり得る)が実際に存在するかどうかは、WebFetchで1件ずつ確認しない。同梱の [scripts/check_urls.py](scripts/check_urls.py) に候補URLを`--url`でまとめて渡し、並列HEADリクエストで一括確認する(詳細は [web-patterns-reference.md](web-patterns-reference.md) 1.5節)
- `llms-full.txt`(全文ダンプ)を取得できた場合、`# タイトル`+`Source: URL`の組で複数ページが連結されている形式かどうかを同梱の [scripts/inspect_section_markers.py](scripts/inspect_section_markers.py) で確認する。この形式なら1問1問`llms-full.txt`全体をGrepせず、URL/パス単位でセクションだけ抽出できる。確認できた場合は同梱の [scripts/extract_doc_section.py](scripts/extract_doc_section.py) をコピーして使う(詳細は [web-patterns-reference.md](web-patterns-reference.md) 1.7節)。抽出した本文が大きい場合は`extract_doc_section.py`組み込みの閾値ベース要約(`aim` CLI、全文パスも必ず併記)が働く(1.8節)
- 上記の形式が成立するサイトに対して、質問のキーワードでGrepしたいがどのURL由来か分からない場合は、同梱の [scripts/grep_doc_sections.py](scripts/grep_doc_sections.py) をコピーして使う。該当行と、その行が属するセクションのURL/タイトルを紐付けて返す(1.9節)

## パターン1b: sitemap/llms.txt URLインデックス

サイト全体のURL発見が必要な場合は、全文をコンテキストへ投入せず、同梱テンプレートをコピーして正規化インデックスを作る。XML sitemap(`urlset`とネームスペース付き`urlset`、`sitemapindex`の子サイトマップ)と`llms.txt`を同じMarkdownエントリ形式へ変換し、完全なURLリストとコンパクトなパスツリーを分離する。

コピー後の起動時更新は`webref_cli.py`経由に統一する。対象スキルの`SKILL.md`先頭で次のように動的コンテキスト注入を使う。

```markdown
!`python "${CLAUDE_SKILL_DIR}/webref_cli.py" download-index`
```

`download-index`は`fetched_at`(既定24時間)が新しければ再取得を省略し、`--force`で強制更新できる。`--allowed-host`を明示し、必要なら`--include-prefix`で技術文書のURL範囲を限定する。非HTTPS、認証情報付き、プライベート/ループバック/リンクローカル、許可ホスト外のURLは取得しない。XMLのDTD/entityを拒否し、文書数・ネスト深度・入力サイズ・エントリ数にも上限を設ける。

通常の参照順序は次のとおり。

1. `output/url-tree.md`をReadして大分類を特定する。ツリーは子孫数を表示し、設定深度以降を`…`へ畳み込む。
2. `output/urls.md`をGrepし、質問のキーワードとURL prefixで候補を絞る。全リストを毎回コンテキストへ読み込まない。
3. `select-urls`を実行して、フィルタ条件を記録した`output/selection.json` manifestを作る。`--include-prefix`/`--exclude-prefix`、`--keyword`/`--exclude-keyword`、`--limit`を必要最小限で指定する。
4. `fetch-pages`を実行するのは、manifestまたは明示的な`--url`で選んだページだけにする。HTTPS・許可ホスト・prefixをリダイレクト後にも再検証し、本文は`output/temp/`へ書いてパスだけを扱う。未選択ページを推測してクロールしない。

```sh
python "${CLAUDE_SKILL_DIR}/webref_cli.py" download-index --url https://example.com/sitemap.xml --allowed-host example.com
python "${CLAUDE_SKILL_DIR}/webref_cli.py" select-urls --keyword routing --include-prefix https://example.com/docs/
python "${CLAUDE_SKILL_DIR}/webref_cli.py" fetch-pages --manifest "${CLAUDE_SKILL_DIR}/output/selection.json" --allowed-host example.com --include-prefix https://example.com/docs/
```

索引に本文は含まれない。本文が必要な場合だけ選択済みURLを取得し、回答では取得元の正規URLを引用する。raw sitemap、selection manifest、取得本文は通常コミットしない。

再利用可能なダウンローダーのひな形が [scripts/download_web_reference.py](scripts/download_web_reference.py) にある。新しいスキルのディレクトリにコピーし、`DEFAULT_URL`/`DEFAULT_OUTPUT`をそのスキル用に書き換えて使う。詳細な設計判断・ファイル配置・実例へのリンクは [web-patterns-reference.md](web-patterns-reference.md) を参照。

**統一コマンド([scripts/webref_cli.py](scripts/webref_cli.py)):** 上記の各スクリプトをコピーしたら、[scripts/webref_cli.py](scripts/webref_cli.py) も一緒にコピーする。これはTyperベースの薄いディスパッチャで、コピーした各スクリプトを`download`/`download-github`/`check-urls`/`generate-excerpt`/`check-excerpt`/`inspect-markers`/`extract-section`/`grep-sections`というサブコマンドにまとめ、各スクリプト自身のargparseへ引数をそのまま転送する(各スクリプトの引数仕様は変えない)。

```sh
python "${CLAUDE_SKILL_DIR}/webref_cli.py" download --force
python "${CLAUDE_SKILL_DIR}/webref_cli.py" check-urls --url https://example.com/llms.txt --only-broken
python "${CLAUDE_SKILL_DIR}/webref_cli.py" extract-section some/known/page
```

コピー時に、ファイル先頭の`SUBCOMMANDS`テーブルを対象スキルに合わせて調整する: そのスキルにコピーしなかったスクリプトの行は削除し、コピー時にファイル名を変えた場合はモジュール名(拡張子を除いたファイル名)を修正する。`python webref_cli.py --help`で、そのスキルに実際に配線されているサブコマンド一覧を確認できる。

## パターン1c: GitHubリポジトリ上のドキュメント

公式ドキュメントのソース(Markdown/MDX)がGitHubの公開リポジトリにある場合(`site/src/content/docs`、`docs/`等)、HTMLサイトを経由せず`gh api`でリポジトリから直接ミラーする。同梱の [scripts/download_github_docs.py](scripts/download_github_docs.py) をコピーし、`DEFAULT_REPO`/`DEFAULT_DOCS_ROOT`/`DEFAULT_REF`を書き換えて`webref_cli.py download-github`で起動時に実行する。

```markdown
!`python "${CLAUDE_SKILL_DIR}/webref_cli.py" download-github`
```

- 列挙は既定でGit Trees API(1リクエストで全ツリー、truncated時はContents APIの再帰walkへフォールバック)。docsルートに下書き・部品ファイルが混ざるなら、目次ファイル(`summary.md`等)のリンク先だけを取る`--toc`を使う
- 出力は`output/<docsルートからの相対パス>`の原文、各ページのfrontmatter `title`/`description`から生成した`output/summary.md`(索引)、`output/_meta.json`(`fetched_at`、既定7日のfreshness、`--force`で強制更新)
- SKILL.md本文では「`summary.md`をRead/Grep → 該当ファイルだけRead → 相対パスと上流URL(`https://github.com/<repo>/blob/<ref>/<path>`、公開サイトURLへの変換規則が分かればそれも)を明示して回答」の順を指示する(`codegraph-docs`スキルが実例)。`output/`をまとめて流さない
- `gh`CLIが必要(公開リポジトリは未認証でも読めるが、レート制限回避のため`gh auth login`済みが望ましい)。前提として`requires_repo_tools`に`gh`を書く
- 1ファイルだけで足りる(仕様書1本など)なら、このテンプレートではなく`download_web_reference.py`に`raw.githubusercontent.com`のURLを渡す方が単純(`okf-spec`スキルが実例)
- llms.txtスナップショットと併用する場合は`--output-dir output/github`のように出力先を分ける(同じ`output/`で両方がstale削除を行うと互いの成果物を消すため)

## パターン2: 動的検索/取得

対象URLが事前に分からない、キーワードから探す必要がある、サイト全体をクロールしたい、あるいは最新性が重要な場合。

**このスキルはWEB検索クライアントを自前実装しない。** まず以下のスキルで要件が満たせないか確認する。

- 1つの既知URLの本文をその場で1回取得したいだけ -> **tav-litスキル**
- キーワード検索・サイトmap/crawl・複数タスクにまたがる蓄積・AIによる調査要約(`research`)が必要 -> **tav-cliスキル**

これらで満たせない要件(Tavily以外のAPI、Web検索ではない特定SaaS連携など)がある場合のみ、独自スクリプトを書く。その場合に守るべき規約は [web-patterns-reference.md](web-patterns-reference.md) の「独自スクリプトを書く場合の規約」を参照。

## チェックリスト(WEB固有・writing-skillの一般チェックリストへの追加分)

- [ ] 静的/動的/ハイブリッドのどれかを最初に決めた
- [ ] (静的の場合)コピーした各スクリプトを`scripts/webref_cli.py`経由の1つの入口(`download`/`download-github`/`check-urls`/`generate-excerpt`/`check-excerpt`/`inspect-markers`/`extract-section`/`grep-sections`サブコマンド)にまとめた。個別スクリプトを`python xxx.py`で都度呼び分ける本文にしていない
- [ ] (静的の場合)取得元がサイト側(`llms.txt`/sitemap)かGitHubリポジトリか、両方ある場合はどちらに寄せる/どう組み合わせるかを、対象の実物を確認して決めた(1.12節)
- [ ] (GitHub取得の場合)`scripts/download_github_docs.py`をコピーし`DEFAULT_REPO`/`DEFAULT_DOCS_ROOT`/`DEFAULT_REF`を設定した。本文で`summary.md`→該当ファイルだけReadの順を指示し、回答に上流URLを明示させている
- [ ] (静的の場合)`fetched_at`によるfreshnessチェックと`--force`を実装した。毎回無条件で再ダウンロードしていない
- [ ] (静的の場合)候補パス(`llms.txt`/`llms-full.txt`等)の存在確認は`scripts/check_urls.py`に複数URLをまとめて渡している。WebFetch等で1件ずつ確認していない
- [ ] (静的の場合)ダウンロードは`!`記号+バッククォート囲みコマンドの動的コンテキスト注入で起動時に確実に実行させている(Claudeの判断任せにしていない)
- [ ] (静的の場合)`llms-full.txt`が無いサイトなら、本文取得にWebFetchが必要である旨を本文に明記した
- [ ] (静的の場合、`llms-full.txt`がある場合)`scripts/inspect_section_markers.py`で`(# タイトル / Source: URL)`パターンかどうかを確認し、成立するなら`scripts/extract_doc_section.py`をコピーしてセクション抽出スクリプトを同梱した(全文を毎回Grepしていない)
- [ ] (上記が成立する場合)`extract_doc_section.py`の閾値ベース要約(`--summarize-threshold`超えで`aim` CLI要約)をそのまま活かし、要約時も全文ファイルのパスを必ず併記するようにしている(要約だけ返して全文への経路を失っていない)
- [ ] (上記が成立し、キーワードでGrepする必要がある場合)`scripts/grep_doc_sections.py`をコピーして、該当行と所属URLを紐付けて返すようにした(行番号だけ返してどのURL由来か分からない状態にしていない)
- [ ] (静的の場合)索引が200行以上、または目的のパスが索引のごく一部しかないなら、`scripts/generate_llms_excerpt.py`+`scripts/prompt_generate_excerpt.template.md`をコピーしてAI生成の抜粋ファイルを作った。プロンプトの構造化出力指示(URL/titleを元索引から文字単位でコピー)を保っている(自由文要約にしていない)
- [ ] (静的の場合、抜粋を生成した場合)`scripts/check_llms_excerpt.py`をコピー・適応して形式・元索引との一致を検証し、スキルに同梱した。検証エラーはAIモデルの再呼び出しではなく、抜粋ファイルの直接編集で修正した
- [ ] (動的の場合)まずtav-cli/tav-litで足りるか検討し、足りる場合は独自スクリプトを書いていない
- [ ] 取得した本文が大きい場合、全文をコンテキストに流さずファイルに書き出し、パスだけを提示するようにした(tav-litスキルの方式)
- [ ] ネットワーク呼び出しには明示的なtimeoutとエラーハンドリングがある(ハングや例外の握りつぶしがない)
- [ ] APIキー等の秘匿情報は`.env`経由で読み、コミット・出力に含めていない
- [ ] コピーしたテンプレート自体のpytestテストは**このメタスキル側(`tests/`)にのみ存在する**。新しく作るスキルにはテンプレートのテストを複製しない(理由は同梱`tests/README.md`参照)。新しいスキル固有のロジックを書き足した場合、そのテストを書くかは通常のプロジェクト方針に従う

## 困ったときは

1. スキル一般の作法(name/description/本文構造など)は**writing-skillスキル**
2. 静的スナップショットの設計詳細・実例一覧は同梱の [web-patterns-reference.md](web-patterns-reference.md)
3. 動的検索の具体的な使い方(クエリ言語、出力レイアウト等)は**tav-cli**/**tav-lit**スキル本体
4. Claude Codeのスキル機構そのもの(動的コンテキスト注入`${CLAUDE_SKILL_DIR}`等)は**writing-skillスキル**同梱の`skills-reference.md`
