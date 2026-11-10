# WEB情報スキルの設計詳細・実例

[SKILL.md](SKILL.md) 本文の判断フローを補足する詳細リファレンス。スキル作成時に都度読む前提ではなく、実装で迷ったときだけ参照する。

## 目次

- [1. 静的スナップショット参照パターン](#1-静的スナップショット参照パターン)
  - [1.1 ファイル配置の基本形](#11-ファイル配置の基本形)
  - [1.2 frontmatter + freshnessチェックの契約](#12-frontmatter--freshnessチェックの契約)
  - [1.3 動的コンテキスト注入で起動を保証する](#13-動的コンテキスト注入で起動を保証する)
  - [1.4 `llms-full.txt`が無いサイトの扱い](#14-llms-fulltxtが無いサイトの扱い)
  - [1.5 候補パスの存在確認は`check_urls.py`でまとめて](#15-候補パスの存在確認はcheck_urlspyでまとめて)
  - [1.6 索引が大きい/大部分が無関係な場合のAI生成抜粋](#16-索引が大きい大部分が無関係な場合のai生成抜粋excerpt--バリデーション--ドリフト検知)
  - [1.7 `Source:`/`# タイトル`型の全文ダンプからのセクション抽出](#17-sourceタイトル型の全文ダンプからのセクション抽出)
  - [1.8 巨大なセクションのAI要約(閾値超え時のみ)](#18-巨大なセクションのai要約閾値超え時のみ)
  - [1.9 Grepの該当行とURLの紐付け](#19-grepの該当行とurlの紐付け)
  - [1.10 統一CLI(`webref_cli.py`)とテンプレート自体のテスト](#110-統一cliwebref_clipyとテンプレート自体のテスト)
  - [1.11 sitemap/`llms.txt` URLインデックス](#111-sitemapllmstxt-urlインデックス)
  - [1.12 GitHubリポジトリからのドキュメント取得](#112-githubリポジトリからのドキュメント取得)
- [2. 動的検索/取得パターン](#2-動的検索取得パターン)
  - [2.1 まず既存スキルで足りるか確認する](#21-まず既存スキルで足りるか確認する)
  - [2.2 独自スクリプトを書く場合の規約](#22-独自スクリプトを書く場合の規約)
- [3. どちらのパターンでもない場合](#3-どちらのパターンでもない場合)

## 1. 静的スナップショット参照パターン

### 1.1 ファイル配置の基本形

```text
<skill-name>/
├── SKILL.md                   # !`python webref_cli.py download` で起動時に必ず実行
├── webref_cli.py               # 統一CLI(scripts/webref_cli.pyをコピーし、SUBCOMMANDSを対象スキルに合わせて調整)
├── download_xxx.py            # ダウンロード本体(scripts/download_web_reference.pyを叩き台にコピー)
├── download_github_docs.py    # GitHubリポジトリのdocsをミラーする場合(1.12節)
├── generate_xxx_excerpt.py    # ↓3つは1.6節の条件(索引200行以上など)を満たす場合のみ
├── check_xxx_excerpt.py       #   抜粋の生成/検証(scripts/generate_llms_excerpt.py / check_llms_excerpt.pyをコピー)
├── prompts/
│   └── prompt_generate_excerpt.md  # 生成プロンプト(scripts/prompt_generate_excerpt.template.mdをコピーして<<...>>を埋める)
├── extract_doc_section.py     # ↓2つは1.7節の条件(Source:/# タイトル型の全文ダンプ)を満たす場合のみ
├── grep_doc_sections.py       #   セクション抽出(1.7-1.8節)・Grep結果へのURL紐付け(1.9節)
├── download_url_index.py      # sitemap/llms.txtの正規化、URLリスト/tree生成
├── select_url_index.py        # URL prefix/keywordによるmanifest選択
├── fetch_selected_pages.py    # manifest/明示URLだけの本文取得
└── output/
    ├── reference.md           # ダウンロード結果(frontmatterにsource/fetched_atを記録)
    ├── excerpt.md             # AI生成抜粋(frontmatterに生成元・生成時刻を記録)
    └── temp/                  # extract_doc_section.pyの抽出結果(<slug>.txt)・要約(<slug>.summary.md)。.gitignoreに追加する
```

すべてのスクリプトは[scripts/webref_cli.py](scripts/webref_cli.py)経由(`webref_cli.py <subcommand>`)で呼ぶ。個別スクリプトを`python download_xxx.py`のように直接呼ぶ本文は書かない(以降の節のコマンド例も`webref_cli.py`経由の形で示す)。

- 複数スキルで同じダウンロードロジックを共有したい(プラグイン内など)場合は、共通モジュールを1つ上の階層に置き、各スキルの`download_xxx.py`はそれを呼ぶ薄いラッパーにする。ただしプラグインではない単発の`.claude/skills/`配下では、共有先の`scripts/`ディレクトリを作らずスキル単体にスクリプトを1本コピーする方がシンプル
- 出力は必ず`output/`のようなサブディレクトリに置き、スクリプトの実行位置に依存しないよう`Path(__file__).resolve().parent`基準の絶対パスで解決する

### 1.2 frontmatter + freshnessチェックの契約

ダウンロード結果ファイルの先頭に以下のYAML frontmatterを必ず書く。

```yaml
---
source: <取得したURL>
fetched_at: <ISO8601形式のUTCタイムスタンプ>
---
```

再実行時はこの`fetched_at`を読み、既定のfreshness window(通常24時間)以内なら再取得せずスキップする。`--force`で無条件に再取得できるようにする。この契約は同梱の[scripts/download_web_reference.py](scripts/download_web_reference.py)、および実例の`skills/plugins/others/skills/vscode-docs/download_vscode_reference.py`・`skills/plugins/ai-tools-knowledge/skills/copilot-cli-docs/generate_copilot_help_yaml.py`で共通。

なぜ毎回ダウンロードしないか: スキル起動のたびに外部サイトへリクエストすると、レイテンシとレート制限リスクが積み重なる。ドキュメントサイトの更新頻度は通常24時間より粗いため、frontmatterで最終取得時刻を自己記述させれば安価に鮮度を判定できる。

### 1.3 動的コンテキスト注入で起動を保証する

ダウンロードの実行を「Claudeが気を利かせて実行する」判断に任せない。SKILL.md本文の先頭で`` !`command` ``記法を使い、スキルが読み込まれた時点で強制的にスクリプトを走らせる。

```markdown
---
name: some-docs
description: ...
allowed-tools: Bash(python .claude/skills/some-docs/*.py *)
---

!`python "${CLAUDE_SKILL_DIR}/webref_cli.py" download`

# 本文...
```

`allowed-tools`でダウンロードスクリプトの実行を許可リストに入れておくと、実行時の確認プロンプトが出ない(`copilot-cli-docs`/`github-copilot-docs`/`vscode-docs`が実例)。

### 1.4 `llms-full.txt`が無いサイトの扱い

`llms.txt`(索引: URL+短い説明のリスト)だけを公開し、`llms-full.txt`(全文連結)は公開していないサイトが多い(`code.visualstudio.com`、`docs.github.com`など)。この場合:

1. まず`output/`の索引ファイルをGrep/Readして関連URLを特定する
2. 本文が必要なら、見つけたURLを個別にWebFetchで取得する(索引ファイル自体には本文がない旨をSKILL.md本文に明記する)
3. 索引に無関係な質問が来た場合は、サイトの検索エンドポイントやドキュメントルートを直接WebFetchで探索してよい、という逃げ道も書いておく

実例: `skills/plugins/others/skills/vscode-docs/SKILL.md`、`skills/plugins/ai-tools-knowledge/skills/github-copilot-docs/SKILL.md`(GitHub Docsは`docs.github.com/api/article/body?pathname=...`という本文取得専用エンドポイントも持っており、WebFetchより軽量に本文だけ取れる。サイトごとにこの種の隠れた取得手段が無いか調べる価値がある)

### 1.5 候補パスの存在確認は`check_urls.py`でまとめて

対象サイトの`llms.txt`/`llms-full.txt`は、ルート直下・ガイド単位・サブディレクトリなど候補パスが複数あり得る(実例: AWSドキュメントはルート`llms.txt`とガイドごとの`llms.txt`の両方を持つが、ガイド単位の`llms-full.txt`は存在しない)。これをWebFetchで1件ずつ確認すると、候補数分の往復レイテンシがそのまま積み上がって非効率。

同梱の [scripts/check_urls.py](scripts/check_urls.py)(`--url`を複数指定できる)を使い、候補URLをまとめて1回のバッチで並列チェックする。

```sh
python "${CLAUDE_SKILL_DIR}/webref_cli.py" check-urls \
  --url https://example.com/llms.txt \
  --url https://example.com/llms-full.txt \
  --url https://example.com/docs/llms.txt \
  --only-broken --format markdown
```

- `--only-broken`を外せば存在したURLも含めた全件が返る。存在が確認できたURLだけを`download_web_reference.py`の`--url`に渡す
- 結果はスクリプトと同じ階層の`.cache/url_cache.sqlite3`(既定TTL 24時間)にキャッシュされるため、同じスキル呼び出し内や翌日以降の再確認で無駄なリクエストを繰り返さない
- 索引ファイル(既存の`output/`配下のMarkdown等)からリンク切れを検出したい場合は、従来通り`file`引数を渡す(`--url`と併用可。両方から集めたURLがまとめて1回のバッチでチェックされる)

### 1.6 索引が大きい/大部分が無関係な場合のAI生成抜粋(excerpt) + バリデーション + ドリフト検知

`llms.txt`索引は非常に便利だが極めて巨大になりうるし、スキルの主目的に無関係なエントリが大半を占めることもある。その場合、関連エントリだけを集めた抜粋ファイルを`output/`配下に別途持ち、通常の質問ではまず抜粋を参照させる。

**いつ抜粋を作るか:**

- 索引が**200行以上なら必ず**作る
- 200行をはるかに下回っていても、スキルの目的に関係するパスが索引のごく一部しか占めない(大半のエントリが毎回ノイズになる)なら積極的に作る

**生成手順(同梱テンプレートのコピー&適応):**

同梱の3ファイルを新しいスキルのディレクトリにコピーして使う。AIモデルの単発呼び出しは`aim` CLI経由(使い方・モデル選定は`aim-cli`スキルを参照)。

| 同梱テンプレート                                                                           | コピー先(例)                         | 適応する箇所                                                                                                  |
| ------------------------------------------------------------------------------------------ | ------------------------------------ | ------------------------------------------------------------------------------------------------------------- |
| [scripts/generate_llms_excerpt.py](scripts/generate_llms_excerpt.py)                       | `generate_xxx_excerpt.py`            | `DEFAULT_SOURCE`/`DEFAULT_OUT`/`DEFAULT_PROMPT`/`DEFAULT_MODEL`(索引のエントリ形式が違う場合のみ`ENTRY_RE`も) |
| [scripts/prompt_generate_excerpt.template.md](scripts/prompt_generate_excerpt.template.md) | `prompts/prompt_generate_excerpt.md` | `<<...>>`プレースホルダ(対象サイト、含める基準、紛らわしい除外例)。**「Output format」節は変更しない**        |
| [scripts/check_llms_excerpt.py](scripts/check_llms_excerpt.py)                             | `check_xxx_excerpt.py`               | `DEFAULT_EXCERPT`/`DEFAULT_SOURCE`/`CANDIDATE_KEYWORDS`(と`ENTRY_RE`)                                         |

テンプレートが実装済みの設計上のポイント(適応時に崩さないこと):

1. **構造化出力の強制**: プロンプトは「含めるエントリのURLのみを、元索引から文字単位でコピーして1行1件、余計なコメント禁止」で出力させる。AIには「どのエントリを含めるか」の判断だけをさせ、抜粋ファイル(`- [Title](URL): desc`形式)の組み立てはスクリプトが元索引のエントリをverbatimで行う。AIがタイトルや説明を書き換える余地が構造的に無くなり、自由文要約では不可能な機械バリデーションが成立する
2. AI出力に含まれるURLのうち元索引に存在しないもの(幻覚・typo)は、生成時点で警告を出して除外する
3. 抜粋ファイルのfrontmatterに`source`(元索引への相対パス)・`extracted_from_fetched_at`(元索引の取得時刻)・`generated_at`・`generated_by`(スクリプト名とモデル名)を記録する
4. プロンプトに`<<...>>`プレースホルダが残っていたら生成を拒否する

**生成後のバリデーション(チェックスクリプト):**

生成した抜粋は必ず`check_xxx_excerpt.py`(上記コピー)で検証する。抜粋の各`- [Title](URL)`エントリを元索引とURL(より安定なキー)で突き合わせ、以下を報告する(`MALFORMED`/`MISSING`/`TITLE MISMATCH`があれば終了コード1):

- `MALFORMED`: `- `で始まるのにエントリとしてパースできない行(AIの崩れた出力や手編集のtypo)
- `MISSING`: 抜粋のURLが元索引に存在しない(上流で改名/削除、または幻覚)
- `TITLE MISMATCH`: URLはあるがタイトルが元索引と異なる
- `DESC DRIFT`: タイトル/URLは一致するが説明文が変わった(情報提供のみ)
- `STALE`: 抜粋生成後に元索引が再取得されている(情報提供のみ)
- 元索引にあるが抜粋に無い関連候補の`CANDIDATE_KEYWORDS`ヒューリスティックによる提案(情報提供のみ)

**問題が見つかったら、AIモデルを再度呼び出して再生成しない。** 抜粋ファイルを自分で直接編集して修正し(タイトルを元索引の表記に合わせる、`MISSING`の行を削除する等)、チェックを再実行する。再生成は非決定的で別の箇所が壊れうるうえ、修正すべき箇所はチェック出力で機械的に特定できているため、直接編集のほうが確実で安い。

**運用:** 元索引は再ダウンロードのたびに更新されるので、抜粋は時間とともにドリフトする。チェックスクリプトはメンテナが手動で走らせる運用が前提で、スキル呼び出しの都度は実行しない。

(このテンプレート群は`skills/plugins/ai-tools-knowledge/skills/vscode-copilot-docs`で実運用しているスクリプト群を汎用化して同梱したもの。実装に必要なものはすべて同梱済みで、実運用側を読みに行く必要はない)

### 1.7 `Source:`/`# タイトル`型の全文ダンプからのセクション抽出

`llms-full.txt`のような全文ダンプは、サイトによっては次のようにページ単位の見出しとソースURLが規則的に繰り返される形式になっている。

```text
# <Title>
Source: <URL>

<本文>
# <Title>
Source: <URL>
...
```

この形式が成立するなら、質問のたびに`llms-full.txt`全体（数MBになることも珍しくない）をGrepするのではなく、URL/パスを指定してそのセクションだけを抽出できる。以下の2ステップで進める。

1. **パターンの成立を確認する**: 同梱の [scripts/inspect_section_markers.py](scripts/inspect_section_markers.py) にダウンロード済みの`llms-full.txt`を渡し、`# `行と`Source:`行の先頭N件（既定10件、`--limit`で変更可）を行番号付きで表示させる。各`# `行の直後（既定3行以内）に`Source:`行が来ているかを見て、パターンが成立しているかを判定する。

   ```sh
   python "${CLAUDE_SKILL_DIR}/webref_cli.py" inspect-markers output/llms-full.txt --limit 10
   ```

   - 見出しキーワードがサイトによって異なる場合(`Source:`ではなく`URL:`など、見出しが`## `など)は`--h1-pattern`/`--source-pattern`で正規表現を差し替えて再実行する
   - このスクリプトは先頭からの単純な行スキャンによるヒューリスティックであり、本文中にたまたま`# `で始まる行(コード例中の見出しなど)が混ざっていると「Inconsistent」と誤検知することがある(実例: `openrouter.ai/docs/llms-full.txt`本文中の`# Using sed (macOS)`)。実際の抽出は見出し行の直後に`Source:`行が続く**組**をアンカーにするため、そのような孤立した本文中の`# `行では境界を誤認しない。「Inconsistent」と出た場合でも、次のステップで実URLを2〜3件試し抽出してみて、本文が正しく切り出せるかで最終判断する
   - 判定基準・実装の詳細は`inspect_section_markers.py`のdocstringを参照

2. **パターンが成立すると判断したら抽出スクリプトを同梱する**: 同梱の [scripts/extract_doc_section.py](scripts/extract_doc_section.py) を新しいスキルのディレクトリにコピーし、`DEFAULT_INPUT`(通常`output/llms-full.txt`)と`DEFAULT_BASE_URL`(対象サイトのドキュメントルート)を書き換える。動作確認は必ず、`llms.txt`索引から拾った実在のURL/パスを2〜3件渡して本文が正しく切り出せるかで行う。

   ```sh
   python "${CLAUDE_SKILL_DIR}/webref_cli.py" extract-section some/known/page another/known/page
   ```

   - URLパスの末尾セグメントがサイト内で衝突する場合(実例: `openrouter.ai`は`client-sdks/go/sdks/chat/README`と`client-sdks/python/sdks/chat/README`のように`README`が81件重複する)、`slug_from_url`はURLパス全体を`/`→`__`に置換したものをキー・出力ファイル名に使う。末尾セグメントだけをキーにすると別ページを取得してしまうので、コピー後もこのロジックは変更しない
   - 実例: `skills/plugins/cc-knowledge/skills/claude-code-docs/extract_doc_section.py`(`code.claude.com`、パターンが素直に成立するケース)、`skills/plugins/topics/skills/openrouter-docs/extract_doc_section.py`(`openrouter.ai`、上記の末尾衝突への対処込み)

### 1.8 巨大なセクションのAI要約(閾値超え時のみ)

`extract_doc_section.py`で抽出した1ページ分の本文が非常に大きい場合、全文をそのままコンテキストに流すとそれだけで消費量が膨らむ。同梱の [scripts/extract_doc_section.py](scripts/extract_doc_section.py) には閾値ベースの自動要約が組み込み済みで、コピーしてそのまま使える。

- 抽出した本文は**常に**`output/temp/<slug>.txt`に全文を書き出し、そのパスを毎回印字する(要約する場合もしない場合も)。全文は要約の裏付け確認のため常に1パス先に置いておく
- 本文の文字数が`--summarize-threshold`(既定`DEFAULT_SUMMARIZE_THRESHOLD_CHARS` = 6000文字)を超える場合のみ、`aim` CLI(使い方・モデル選定は`aim-cli`スキル参照)で要約し、`output/temp/<slug>.summary.md`に書き出す。要約ファイルのfrontmatterには`source`・`title`・`original_length_chars`・`full_text`(全文ファイル名)・`summarized_at`・`summarized_by`を記録する
- 標準出力には「全文を書いた」「閾値を超えたので要約した」「要約ファイルのパス」「(確認用に)全文ファイルのパス」を毎回まとめて印字するので、Claude側は追加の判断なしに両方のパスを受け取れる
- 閾値以下なら要約は行わず、従来通り全文ファイルのパスだけを返す(小さいページで無駄なaim呼び出しをしない)
- `aim` CLIが失敗した場合(未インストール・APIエラー等)は警告を出して**全文ファイルへのフォールバック**にとどめ、処理全体は継続する(1ページの要約失敗で他のURLの抽出を止めない)
- コピー後に調整するのは`--summarize-threshold`(対象サイトの1ページあたりの分量次第で)と`--model`(既定`minimax-m3`)。閾値・要約自体が不要なら`--no-summarize`で無効化できる

### 1.9 Grepの該当行とURLの紐付け

`llms-full.txt`を素朴にGrepすると、該当行とその行番号は分かってもその行がどのページ(URL)由来かは分からない。ページ単位の見出し(`# タイトル` / `Source: URL`)がファイル中に散らばっているだけで、行ごとにURLが付与されているわけではないため。

同梱の [scripts/grep_doc_sections.py](scripts/grep_doc_sections.py) は、ファイルを先頭から走査しながら直近の`(# タイトル / Source: URL)`ペアを追跡し、検索パターンにマッチした行それぞれに、その時点で有効なタイトル・URLを紐付けて出力する。

```sh
python "${CLAUDE_SKILL_DIR}/webref_cli.py" grep-sections "検索パターン" --input output/llms-full.txt
python "${CLAUDE_SKILL_DIR}/webref_cli.py" grep-sections "ERROR_CODE_\d+" --ignore-case --max-matches 50
python "${CLAUDE_SKILL_DIR}/webref_cli.py" grep-sections "exact literal string" --fixed-strings
```

- 見出し判定は`extract_doc_section.py`/`inspect_section_markers.py`と同じヒューリスティック(見出し行の直後`MAX_PAIR_GAP_LINES`行以内に`Source:`行が来て初めて「新しいセクションに入った」とみなす)を使うため、本文中にたまたま`# `で始まる行が混ざっていても誤ってセクション境界と誤認しない
- 出力はURLごとにグルーピングされ、`== URL (Title) ==`の下に該当行番号・行テキストが並ぶ。まだどの`Source:`行も現れていない箇所(ファイル冒頭など)でマッチした場合は`(no Source seen yet at this point in the file)`として区別する
- `--max-matches`(既定`DEFAULT_MAX_MATCHES` = 200)で件数を打ち切った場合、末尾に総マッチ数との差分を明記するので、無言の切り捨てにはならない
- **1.7節が成立する(`inspect_section_markers.py`でパターン確認済み)サイトでのみ使う。** 見出しパターンがサイト固有の場合は`--h1-pattern`/`--source-pattern`で正規表現を差し替える(`extract_doc_section.py`の`DEFAULT_BASE_URL`のように、コピー後にサイトごとへ調整する箇所)

### 1.10 統一CLI(`webref_cli.py`)とテンプレート自体のテスト

本節までのコマンド例はすべて[scripts/webref_cli.py](scripts/webref_cli.py)経由(`python webref_cli.py <subcommand>`)で示してきた。これはTyperベースの薄いディスパッチャで、コピーした各スクリプトを1つの入口にまとめる。個別スクリプトの引数仕様(argparse)は変更しない -- `webref_cli.py`は「どのスクリプトを呼ぶか」を統一するだけで、引数はサブコマンド名の後にそのまま転送される。

- 新しいスキルにコピーする際は、ファイル先頭の`SUBCOMMANDS`テーブルを対象スキルに合わせて調整する: コピーしなかったスクリプトの行を削除し、ファイル名を変えた場合はモジュール名を修正する
- `python webref_cli.py --help`で、そのスキルに実際に配線されているサブコマンド一覧と各サブコマンドの短い説明を確認できる。`python webref_cli.py <subcommand> --help`は転送先スクリプト自身のargparseヘルプ(`--url`/`--force`等の詳細な引数)を表示する
- SKILL.md本文の`` !`command` ``による起動時ダウンロードも`webref_cli.py download`経由にする(1.3節参照)

**このテンプレート自体(`writing-skill-web`が同梱する`scripts/*.py`)には、[tests/](tests/README.md)配下にpytestテストが同梱されている。** これは`writing-skill-web`というメタスキル自身の同梱テンプレートを検証するものであり、これらのテンプレートをコピーして作る個別スキル側(`vscode-docs`等)にテストを複製する運用ではない(コピー-適応前提のテンプレートである、という1.1節の設計方針と同じ理由。詳細は[tests/README.md](tests/README.md)参照)。

### 1.11 sitemap/`llms.txt` URLインデックス

サイトのURL数が多い場合は、`scripts/download_url_index.py`をコピーして、サイトのsitemapまたは`llms.txt`を正規化する。出力は完全なURLリスト(`output/urls.md`)と、パスを深さ制限付きで畳み込んだツリー(`output/url-tree.md`)に分ける。URLリストの各エントリは次の形式で、`title`/`description`は利用可能な入力情報から作る。

```text
---
source: https://example.com/sitemap.xml
fetched_at: 2026-01-01T00:00:00+00:00
generated_at: 2026-01-01T00:00:00+00:00
---

# URL Index
- [Router](https://example.com/docs/router): Configure routing.
```

`urlset`は名前空間の有無にかかわらず`loc`/`lastmod`を読む。`sitemapindex`は子URLを同一のHTTPS許可ホスト内だけで再帰取得し、フラグメントを除去してURLを重複排除する。`llms.txt`はMarkdownリンクとプレーンなHTTPS URLを読む。XML入力はDTD/entity、サイズ、子文書数、深さ、正規化エントリ数を制限する。リダイレクトは自動追従せず、次のURLを許可ホストで検証してから取得する。

```sh
python "${CLAUDE_SKILL_DIR}/webref_cli.py" download-index \
  --url https://example.com/sitemap.xml \
  --allowed-host example.com \
  --include-prefix https://example.com/docs/
```

`select_url_index.py`は完全リストを読み、prefixとキーワードのinclude/exclude、件数上限を適用してJSON manifestを作る。条件はmanifestの`filters`に保存し、選択結果は入力順(ダウンローダー出力はURL順)を維持する。

```sh
python "${CLAUDE_SKILL_DIR}/webref_cli.py" select-urls \
  --include-prefix https://example.com/docs/ \
  --keyword routing --limit 5 \
  --output output/selection.json
```

`fetch_selected_pages.py`は`--url`の明示URLまたは`select-urls`のmanifestのどちらか一方だけを受け付ける。既定の最大ページ数は20、本文上限は4 MiBで、出力は`output/temp/`へ置く。各リダイレクト先にもHTTPS・ホスト・prefix検証を適用し、失敗したURLは本文を出力せずエラーとして報告する。manifestなしにURLリスト全体を取得することはできない。

```sh
python "${CLAUDE_SKILL_DIR}/webref_cli.py" fetch-pages \
  --manifest output/selection.json \
  --allowed-host example.com \
  --include-prefix https://example.com/docs/
```

raw sitemap、manifest、取得本文はrefresh可能な作業データとして`.gitignore`へ入れる。生成物をコミットする個別スキルでは、対象prefixでフィルタ済みのURLリストとツリーだけを保持する。

### 1.12 GitHubリポジトリからのドキュメント取得

ドキュメントサイトの多く(Astro Starlight、Docusaurus、MkDocs、VitePress等)はソースMarkdownを公開リポジトリに置いている。[scripts/download_github_docs.py](scripts/download_github_docs.py)をコピーすると、`gh api`でそのディレクトリをまるごと(または目次のリンク先だけ)ミラーできる。

```sh
python "${CLAUDE_SKILL_DIR}/webref_cli.py" download-github                     # DEFAULT_*で取得(fresh ならスキップ)
python "${CLAUDE_SKILL_DIR}/webref_cli.py" download-github --force
python "${CLAUDE_SKILL_DIR}/webref_cli.py" download-github --repo owner/name --docs-root docs --toc summary.md
```

- **列挙方法**: 既定はGit Trees API(`git/trees/<ref>?recursive=1`)で1リクエスト。巨大リポジトリで`truncated`が返った場合だけContents APIの再帰walkに落ちる。docsルートに下書き・include用の部品が混ざる、または公式目次の順序を保ちたい場合は`--toc`で目次ファイル(`summary.md`/`SUMMARY.md`/`index.md`等)のリンク先だけを取る(`pr-agent-docs`が目次方式、`codegraph-docs`が全列挙方式の実例)
- **索引**: 各ページのfrontmatter `title`/`description`から`output/summary.md`を生成する(上流ファイルではない)。frontmatterが無いリポジトリではファイル名がラベルになるので、必要ならコピー後に見出し(`# `)から拾うよう調整する
- **鮮度**: `_meta.json`の`fetched_at`で判定、既定7日。docsリポジトリは頻繁にコミットされても内容の変化は緩やかなので、サイト側の24時間より長めにしている。変更が速い製品なら`FRESHNESS`を縮める
- **stale削除**: 再取得時、索引に無い`output/`内ファイルは削除する。`output/temp/`など他スクリプトの成果物は`PRESERVE_PREFIXES`で保護する。CLI `--help` YAML等を同じ`output/`に置くなら(`codegraph-docs`の`cli/`)そのprefixを足す
- **回答時の引用**: 相対パスに加え、上流URL(`https://github.com/<repo>/blob/<ref>/<docs_root>/<path>`)を示させる。公開サイトURLへの変換規則(拡張子除去・末尾スラッシュ等)が分かるなら、SKILL.md本文にその規則も書く
- **MDX**: `.mdx`も取得するが、JSXコンポーネント(`<Tabs>`等)はそのまま残る。本文がほぼコンポーネントで読めない場合は、サイト側(`llms.txt`/レンダリング済みページ)を優先する判断材料になる
- **1ファイルだけなら**: 仕様書1本のように対象が単一ファイルなら、`download_web_reference.py`に`https://raw.githubusercontent.com/<repo>/<ref>/<path>`を渡す方が単純(`okf-spec`が実例)。`gh`不要でfrontmatter+24時間freshnessの契約もそのまま使える

**`llms.txt`とGitHubの両方がある場合**: どちらに寄せるか、ミックスするかは**スキルごとに作成時に判断する**(このメタスキルは既定を決めない)。判断材料の例:

| 観点             | サイト側(`llms.txt`/`llms-full.txt`)に寄りやすい        | GitHub側に寄りやすい                                     |
| ---------------- | ------------------------------------------------------- | -------------------------------------------------------- |
| 網羅性           | `llms-full.txt`に全ページが入っている                   | `llms.txt`が一部ページしか載せていない/古い              |
| 本文の読みやすさ | ソースがMDXコンポーネントだらけ、include/変数展開が多い | ソースがほぼ素のMarkdown                                 |
| 取得コスト       | 1ファイルで済む                                         | ページ数が少なく`gh`の呼び出し回数が問題にならない       |
| 版管理           | 最新版だけで足りる                                      | タグ/ブランチ単位で特定バージョンのdocsが欲しい(`--ref`) |
| 依存             | `gh`を前提にしたくない                                  | `gh`が既に前提(開発者向けツールのdocs等)                 |

ミックスする場合の典型は「索引・URL発見はサイト側`llms.txt`、本文はGitHubの原文」あるいは「主要docsはGitHub、ブログ/変更履歴などリポジトリ外のページだけ`llms.txt`+WebFetch」。いずれも出力先を`output/site/`・`output/github/`のように分け(`--output-dir`)、SKILL.md本文に「どの質問でどちらを先に見るか」を明記する。

## 2. 動的検索/取得パターン

### 2.1 まず既存スキルで足りるか確認する

| 状況                                                                                               | 使うスキル |
| -------------------------------------------------------------------------------------------------- | ---------- |
| 1つの既知URLの本文(またはクエリ関連部分)をその場で1回取得したいだけ                                | `tav-lit`  |
| キーワード検索、サイトmap/crawl、複数タスクにまたがる蓄積(`--topic`)、AIによる調査要約(`research`) | `tav-cli`  |

両スキルの詳細な使い方(クエリ言語、`--detail`プリセット、出力レイアウト、終了コード等)はそれぞれのSKILL.md本体を参照し、ここでは繰り返さない。**新しいスキルを作る前に、作ろうとしている手順が`tav search`/`tav extract`等の組み合わせで表現できないか必ず検討する。**

### 2.2 独自スクリプトを書く場合の規約

Tavily系スキルの守備範囲外(Web検索ではない特定SaaS APIとの連携、Tavilyが対応しない取得方式など)でのみ、独自の取得スクリプトを書く。その場合もtav-cli/tav-litが確立した規約に合わせる。

- **APIキー等の秘匿情報は`.env`経由で読む**。スキルディレクトリ直下に置き、カレントディレクトリからの上方探索はしない(`tav-lit`と同じ設計)。コミット対象からは除外し、出力・ログにも書き出さない
- **大きな結果は必ずファイルに書き出し、ターミナル/コンテキストにはファイルパスだけを印字する**。ページ全文のような大きなペイロードをそのまま標準出力に流さない(`tav-lit`の`extract_page.py`と同じ方式)
- **自己記述的な出力エンベロープにする**。生の配列やベタテキストではなく、`{"script": ..., "result_kind": ..., "exit_code": ..., "result": ...}`のような形にすると、後続タスクや他のスクリプトから機械的に読みやすい(`tav-cli`の各スクリプトが実例)
- **ネットワーク呼び出しには明示的なtimeoutを付け、例外を握りつぶさない**。タイムアウト値や並列数の上限のようなマジックナンバーには、なぜその値かをコメントで残す
- **終了コードで成否を機械判定できるようにする**。`0`=成功、キー不備・対象0件・その他失敗などを別コードに割り当てる(`tav-lit`の終了コード表が実例)
- **並列実行时のレート制限を考慮する**。`tav-cli`の「並列実行・レート・コストの扱い」節にある「軽い処理から並列度を上げ、429やタイムアウト増加が見えたら半分に落とす」という運用ルールは、独自スクリプトでも踏襲する価値がある

## 3. どちらのパターンでもない場合

CLI自体の`--help`出力を根拠にするスキル(`copilot-cli-docs`が実例)は、WEB上の情報ではなくローカルコマンドの出力を対象とするため、本メタスキルの対象外。ただし「取得結果をYAML/Markdownに構造化し、frontmatterでfetched_atを記録し、freshnessチェックする」という骨格は静的スナップショットパターンと共通なので、参考にはなる。
