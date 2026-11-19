# Claude（claude.ai）機能マップ

最終確認日: 2026-11-18 ／ 対象: claude.ai の WEB 版。デスクトップアプリ固有の機能は [desktop.md](desktop.md)。モバイルは記事に差分が書かれている範囲だけ注記する

機能名 → 公式ページの索引。上限・料金・対応プランの**具体値は書かない**（変わりやすい）。回答前に必ずリンク先の本文を取る（取り方は [SKILL.md](SKILL.md)。Claude の記事は `fetch` で `.md` を直取得できる）。

## 情報源

- ヘルプセンター: https://support.claude.com/en/ （日本語版 `/ja/` もあるが英語版を正にする。`fetch` は `/en/articles/` だけ受け付ける）
- リリースノート: https://support.claude.com/en/articles/12138966-release-notes （claude.ai・Desktop・Mobile・Enterprise 管理をまとめた 1 本。新しい順）
- プランと上限: [How do usage and length limits work?](https://support.claude.com/en/articles/11647753-how-do-usage-and-length-limits-work)、プラン別の記事は「プランと上限」の節。料金ページ https://claude.com/pricing （価格は JS 描画で抜けることがある）
- 範囲外（別物。利用者向けアプリの仕様として流用しない）
  - Claude Code（ヘルプの「Claude Code」節、code.claude.com）→ `claude-code-docs` スキル。新版 projects（beta）は Claude Code から先に展開しているので、その詳細もこちら
  - Claude API・Console（platform.claude.com、ヘルプの「Claude API and Console」節）→ `claude-api` スキル。API の MCP connector・Agent Skills も API 側の話
  - Amazon Bedrock・Microsoft Foundry など他社クラウド経由の Claude
  - Claude Desktop のローカル MCP（desktop extensions）は claude.ai では使えない。[外部連携](#外部連携) の Desktop extensions を参照

## 目次

- [プロジェクト](#プロジェクト) — Projects / Projects (new version, beta)
- [カスタムアシスタント・再利用できる指示](#カスタムアシスタント再利用できる指示) — Skills / Plugins
- [外部連携](#外部連携) — Connectors / Custom connectors / Desktop extensions / Interactive connectors / Personal Finance
- [メモリ・パーソナライズ](#メモリパーソナライズ) — Memory / Search and reference chats / Import and export memory / Incognito chats / Instructions
- [調査](#調査) — Research
- [作成物](#作成物) — Artifacts / Claude Docs / Claude Design
- [エージェント・自動化](#エージェント自動化) — Claude Cowork / Scheduled tasks / Claude in Chrome / Cloud browser / Claude Meetings / Claude Duet
- [音声](#音声) — Voice mode
- [共有・チーム管理](#共有チーム管理) — Share chats / Share artifacts / Organization settings
- [プランと上限](#プランと上限) — Plans / Usage limits
- [廃止・終了した機能](#廃止終了した機能) — Standalone Claude Design / Legacy artifacts

## プロジェクト

### Projects

- **概要**: チャット履歴・ナレッジ（アップロードしたファイル）・プロジェクト指示をまとめた作業空間。ナレッジが大きくなると有料プランでは自動で RAG（project knowledge search）に切り替わる
- **入口**: サイドバーの "Projects"（claude.ai/projects）→ "+ New Project"
- **公式ページ**: [What are projects?](https://support.claude.com/en/articles/9517075-what-are-projects)、[How can I create and manage projects?](https://support.claude.com/en/articles/9519177-how-can-i-create-and-manage-projects)、[RAG for projects](https://support.claude.com/en/articles/11473015-retrieval-augmented-generation-rag-for-projects)、ファイル上限は [Upload files to Claude](https://support.claude.com/en/articles/8241126-upload-files-to-claude)
- **プラン・提供範囲**: Free を含む全プラン（Free は作成数に上限あり）。RAG は有料プラン（Pro・Max・Ultra・Team・Enterprise）のみ。組織内共有（Can view / Can edit）は Team・Enterprise のみ。根拠: 9517075・11473015
- **注意**: Cowork でも同じ projects を使う（[Organize your tasks with projects in Claude Cowork](https://support.claude.com/en/articles/14116274-organize-your-tasks-with-projects-in-claude-cowork)）。ローカルフォルダに紐づく project の Cowork セッションは Desktop のみ。下の新版への移行が進行中

### Projects (new version, beta)

- **概要**: 1 プロジェクト = 1 会話。依頼を Claude が並列スレッドに分けてクラウドで実行し、ノートを閉じても続く。各スレッドはプロジェクトのファイル・リポジトリ・指示・メモリを持って始まり、成果物は project の Library に集まる
- **入口**: 提供済みなら claude.ai/code のサイドバーと Claude Desktop の Code タブに "Projects" が出る
- **公式ページ**: [What are projects?](https://support.claude.com/en/articles/9517075-what-are-projects) の "The new version of projects (beta)" 節。詳細は Claude Code docs の Projects（`claude-code-docs` スキル側）
- **プラン・提供範囲**: Claude Code を使う一部の Pro・Max・Ultra から段階展開。chat・Cowork・Team・Enterprise は後から。ウェイトリストあり。根拠: 9517075
- **注意**: 一部の Pro・Max・Ultra では既存 projects（指示・ファイル・履歴・scheduled tasks）が新版へ移行され始めている。並列スレッドは使用量の消費が速い。「Projects の仕様」を聞かれたら旧版・新版のどちらかを確かめる

## カスタムアシスタント・再利用できる指示

GPTs（ChatGPT）や Gems（Gemini）に当たる単一の機能は無い。用途により **Projects（固定の背景知識）＋ Skills（必要時に読み込む手順）＋ Plugins（skills・connectors・sub-agents の束）** を組み合わせる。Skills と Projects・MCP・custom instructions の違いは [What are skills?](https://support.claude.com/en/articles/12512176-what-are-skills) の比較節にある。

### Skills

- **概要**: 指示・スクリプト・リソースをまとめたフォルダ。Claude が関係するものだけを動的に読み込む。Anthropic 製・自作（ZIP をアップロード、または画面操作の録画から作成）・組織配布・パートナー製がある。Agent Skills のオープン標準
- **入口**: 本文の表記は **Customize > Skills**（"+" → "+ Create skill" → "Upload a skill"）。チャットでは "+" か "/" で呼ぶ。前提として **Settings > Capabilities** の "Code execution and file creation"（新しい Settings では "Create and edit files"）をオン
- **公式ページ**: [What are skills?](https://support.claude.com/en/articles/12512176-what-are-skills)、[Use skills in Claude](https://support.claude.com/en/articles/12512180-use-skills-in-claude)、[How to create custom skills](https://support.claude.com/en/articles/12512198-how-to-create-custom-skills)、組織配布は [Provision and manage skills for your organization](https://support.claude.com/en/articles/13119606-provision-and-manage-skills-for-your-organization)
- **プラン・提供範囲**: Free を含む全プラン（code execution が必要）。特定の人・グループへの共有と "Publish to org" は Team・Enterprise。録画からの作成は Mac の Cowork で一部プランのみ。根拠: 12512176・12512180・12512198
- **注意**: 「Customize」は Plugins に改名済み（下の Plugins）だが、skills の記事本文はまだ Customize 表記。有効にした skills は同じアカウントの Claude Code にも同期される（Claude Code 側の話は `claude-code-docs`）。Claude Code での提供状況を 12512176 は available、12512198 は beta と書いており食い違う

### Plugins

- **別名**: 日本語ヘルプの表記「プラグイン」（旧「カスタマイズ」）。実画面の表記は未確認／旧称 Customize（サイドバーのメニュー名）
- **概要**: skills・connectors・sub-agents を 1 つにまとめたパッケージ。Plugins ページで plugins・skills・connectors を一元管理する（個別の Skills / Connectors / Plugins タブを置き換え）。Plugin Create で自作もできる
- **入口**: サイドバーの **Plugins** → **Your plugins** / ディレクトリ（クイックフィルターで skills・connectors に絞れる）。公開 plugin には **Verified** / **Community** の表示
- **公式ページ**: [Manage plugins, skills, and connectors from one Plugins page](https://support.claude.com/en/articles/17740565-manage-plugins-skills-and-connectors-from-one-plugins-page)、[Use plugins in Claude](https://support.claude.com/en/articles/13837440-use-plugins-in-claude)、[Browse skills, connectors, and plugins in one directory](https://support.claude.com/en/articles/14328846-browse-skills-connectors-and-plugins-in-one-directory)、組織管理は [Manage plugins for your organization](https://support.claude.com/en/articles/13837433-manage-plugins-for-your-organization)
- **プラン・提供範囲**: plugins の利用は有料プラン（Pro・Max・Ultra・Team・Enterprise）。Plugins ページへの統合は Free〜Team が 2026-11-09 に一般提供、Enterprise は 2026-11-30 から既定でオン。根拠: 13837440・17740565
- **注意**: chat（web）では plugin の skills・commands は動くが、hooks・sub-agents・ローカル MCP サーバーは Cowork と Claude Code でしか動かない（chat では灰色表示）。13837440・14328846 の手順はまだ旧 "Customize" 表記。Team・Enterprise で Skills を無効にしている組織は 2026-11-30 から Desktop でも plugins が止まる。Claude の公式ディレクトリへは developer portal から plugin を申請できる（リリースノート 2026-09-25。審査・利用状況の分析つき）

## 外部連携

### Connectors

- **別名**: 日本語ヘルプの表記「コネクタ」（実画面は未確認）
- **概要**: 外部アプリ・サービスにアクセスし、データ取得や操作をする。利用者ごとの権限を引き継ぐ。Connectors Directory から追加する。Google Workspace・Microsoft 365・GitHub などは個別記事あり
- **入口**: チャットの "+"（または "/"）→ "Connectors" → "Manage connectors"、または Customize > Connectors（現在は Plugins ページ）。Team・Enterprise はまず Owner が **Organization settings > Connectors** で追加する
- **公式ページ**: [Use connectors to extend Claude's capabilities](https://support.claude.com/en/articles/11176164-use-connectors-to-extend-claude-s-capabilities)、[How Claude suggests connected apps](https://support.claude.com/en/articles/14730684-how-claude-suggests-connected-apps)
- **プラン・提供範囲**: web connectors は全ユーザー（Claude・Cowork・Desktop・Mobile）。モバイルからのインストールは beta。根拠: 11176164
- **注意**: Team・Enterprise では Owner が connector ごとに書き込み操作を禁止するなどの制限ができる（同記事）

### Custom connectors

- **別名**: 日本語ヘルプの表記「カスタムコネクタ」（実画面は未確認）
- **概要**: 自作・既存の **remote MCP サーバー**を URL で追加する。接続は Anthropic のクラウドから行われるので、サーバーは公開インターネットの HTTPS（443）で Anthropic の IP から届く必要がある
- **入口**: 個人プラン: Customize > Connectors → "+ Add" → "Add custom connector"（Customize は 2026-11 に Plugins へ改名。記事 11175166 の手順は旧表記のまま。[Plugins](#plugins)・17740565 を参照）。記事の見出しは "For Pro and Max plans" だけで、Free・Ultra の手順は明記されていない。Team・Enterprise: Owner が Organization settings > Connectors → "Add" → "Custom" → "Web"
- **公式ページ**: [Get started with custom connectors using remote MCP](https://support.claude.com/en/articles/11175166-get-started-with-custom-connectors-using-remote-mcp)
- **プラン・提供範囲**: Free を含む全プラン（Free は数に上限あり）。Claude・Cowork・Desktop で使える。Team は Owner、Enterprise は Owner か "Manage access to Libraries" を含む custom role の人だけが組織に追加できる。根拠: 11175166
- **注意**: 「Claude に自作 MCP を足したい」は製品で行き先が違う。claude.ai・Desktop・Cowork の remote MCP はこの記事、Desktop のローカル MCP は下の Desktop extensions、Claude Code は `claude-code-docs`、API の MCP connector は `claude-api`。VPN 内・社内網のサーバーは IP 許可が無いとつながらない

### Desktop extensions

- **別名**: 日本語ヘルプの表記「デスクトップ拡張機能」（実画面は未確認）／ローカル MCP サーバー（`claude_desktop_config.json`）
- **概要**: 手元の PC で動く MCP（ローカルファイル・localhost の DB・デスクトップアプリ）。remote connector と違い、自分のネットワークから接続する
- **入口**: Claude Desktop → Settings → Desktop app → Extensions の "Manage"（旧レイアウトは Settings → Extensions）
- **公式ページ**: [When to use desktop and web connectors](https://support.claude.com/en/articles/11725091-when-to-use-desktop-and-web-connectors)、[Getting Started with Local MCP Servers on Claude Desktop](https://support.claude.com/en/articles/10949351-getting-started-with-local-mcp-servers-on-claude-desktop)
- **プラン・提供範囲**: Claude Desktop の全ユーザー。**web（claude.ai）とモバイルでは使えない**（Desktop と Claude Code のみ）。根拠: 11725091・11176164
- **注意**: クラウドで動く Cowork セッションや Research もローカル MCP のツールを使えない（11175166・11088861）

### Interactive connectors

- **概要**: 一部の connector が会話内にライブの UI（ダッシュボード・タスクボード等。MCP app）を表示する。表示はインラインカード・サイドパネル・全画面
- **公式ページ**: [Use interactive connectors in Claude](https://support.claude.com/en/articles/13454812-use-interactive-connectors-in-claude)、Claude 自身が描く図表は [Custom visuals in chat and Cowork](https://support.claude.com/en/articles/13979539-custom-visuals-in-chat-and-cowork)
- **プラン・提供範囲**: 全ユーザー（Claude・Cowork・Desktop・iOS/Android）。サイドパネル・サイト表示・ナビゲーションへのピン留めは「新しい Claude experience」の web・Desktop に段階展開中で、モバイルは未対応。根拠: 13454812

### Personal Finance

- **別名**: 日本語ヘルプの表記「個人財務」（実画面は未確認）
- **概要**: 銀行・カード・ローン・投資口座を Plaid 経由でつなぎ、残高・支出を 1 ページで見て Claude に質問する。読み取りのみ
- **入口**: サイドメニューの "Personal Finance"（見当たらなければ **More** の中）→ "Get started"
- **公式ページ**: [Use Personal Finance in Claude](https://support.claude.com/en/articles/18185620-use-personal-finance-in-claude)
- **プラン・提供範囲**: beta。Pro・Max・Ultra、**米国のみ**、段階展開。Free・Team・Enterprise は対象外。根拠: 18185620（リリースノート 2026-11-05）
- **注意**: 公開リンクでチャットを共有すると、口座の数値も見える（[Public links for shared chats](https://support.claude.com/en/articles/16762437-public-links-for-shared-chats)）

## メモリ・パーソナライズ

### Memory

- **概要**: 会話から個別の分類済みエントリ（**Topics**）を作り、以後の会話で読み書きする（2026-07 に日次サマリー方式から変更）。project ごとのメモリあり。クラウドで動く Cowork・Claude Duet とメモリを共有する
- **入口**: **Settings > Your Claude**（旧レイアウトは **Settings > Memory**）の "Generate memory from chats"、"Manage"（Your memory）で閲覧・編集。1 チャットだけ切るなら "+" メニューの "Memory"。センシティブな話題は **Include sensitive topics in memory** をオンにしたときだけ保存
- **公式ページ**: [Use Claude's chat search and memory to build on previous context](https://support.claude.com/en/articles/11817273-use-claude-s-chat-search-and-memory-to-build-on-previous-context)
- **プラン・提供範囲**: Free・Pro・Max・Ultra は既定でオン。Team・Enterprise は Owner が可否を決め、2026-10-31 以降に作られた組織は既定でオン（例外あり）。根拠: 11817273
- **注意**: HIPAA・公共部門の契約の組織は新メモリ対象外。旧メモリ（Settings > Capabilities に Memory がある）の利用者は記事後半の legacy 節を読む。ローカルで動く Cowork セッションはメモリを使わない

### Search and reference chats

- **概要**: 過去のチャットを Claude が検索・参照する
- **入口**: Settings > Your Claude（旧 Settings > Memory）の **Search and reference chats**
- **公式ページ**: [11817273](https://support.claude.com/en/articles/11817273-use-claude-s-chat-search-and-memory-to-build-on-previous-context) の "Search past chats with Claude" 節
- **プラン・提供範囲**: 有料プラン（Pro・Max・Ultra・Team・Enterprise）。web・Desktop・Mobile。CMEK を使う Enterprise では使えない。根拠: 11817273

### Import and export memory

- **概要**: 他社 AI のメモリを、所定のプロンプトで書き出したテキストを貼って取り込む。書き出しはメモリ一覧を見るか、Claude に逐語で出させる
- **入口**: Settings > Your Claude（旧 Settings > Memory）の "Start import" → 貼り付け → "Add to memory"
- **公式ページ**: [Import and export your memory from Claude](https://support.claude.com/en/articles/12123587-import-and-export-your-memory-from-claude)
- **プラン・提供範囲**: 全プラン、web と Desktop。根拠: 12123587
- **注意**: 実験的機能で、取り込みが反映されないことがある。仕事に関係しない個人情報は残らないことがある

### Incognito chats

- **概要**: 履歴・メモリに残らない一時チャット。project の外で右上のおばけアイコンから始める
- **公式ページ**: [Use incognito chats](https://support.claude.com/en/articles/12260368-use-incognito-chats)、11817273 の "Incognito chats" 節
- **プラン・提供範囲**: 全プラン。根拠: 11817273
- **注意**: Team・Enterprise では組織のデータエクスポートと保持ポリシーの対象になる

### Instructions

- **別名**: 旧レイアウトでは "Instructions for Claude"（Account の中）
- **概要**: 全会話に効くアカウント単位の指示（custom instructions）。ほかに Styles などのパーソナライズがある
- **入口**: 左下のイニシャル → "Settings" → "Your Claude"（旧 "Account"）→ "Instructions"
- **公式ページ**: [Understanding Claude's personalization features](https://support.claude.com/en/articles/10185728-understanding-claude-s-personalization-features)
- **注意**: 組織全体の指示は Team・Enterprise の [Set organization instructions](https://support.claude.com/en/articles/14546867-set-organization-instructions)

## 調査

### Research

- **別名**: 日本語ヘルプの表記「調査機能」。ボタン名は日本語ヘルプでも "Research" のまま（実画面は未確認）
- **概要**: 検索を重ねて深く調べる（他アプリの deep research 相当）。web と、チャットでオンにした connectors（Google Workspace 等）を承認なしで使う
- **入口**: チャット左下の "+" → "Research"（青いインジケーターが出る）。**web search** をオンにしておく必要がある
- **公式ページ**: [Use research on Claude](https://support.claude.com/en/articles/11088861-use-research-on-claude)、使い分けは [When should I use web search, extended thinking, and research?](https://support.claude.com/en/articles/11095361-when-should-i-use-web-search-extended-thinking-and-research)
- **プラン・提供範囲**: 有料プラン（Pro・Max・Ultra・Team・Enterprise）、web・Desktop・Mobile。根拠: 11088861
- **注意**: Mobile で始めると connectors を使わず web だけを調べる（エラーも出ない）。Desktop のローカル MCP は使えない

## 作成物

### Artifacts

- **概要**: 会話の横に開く成果物（文書・スライド・デザイン・ダッシュボード・小さなアプリ）。どの会話からでも頼めるほか、**Artifacts** タブかメッセージ欄の "Output" からテンプレート（Docs・Slides・Design・Data・Sheets・Whiteboards・Motion）で始める。Claude を呼ぶアプリ、connectors 連携、データ保存もできる
- **公式ページ**: [What are artifacts and how do I use them?](https://support.claude.com/en/articles/17153992-what-are-artifacts-and-how-do-i-use-them)、テンプレート別は [Claude Sheets](https://support.claude.com/en/articles/18324300-get-started-with-claude-sheets)・[Claude Whiteboards](https://support.claude.com/en/articles/18324319-get-started-with-claude-whiteboards)・[Claude Data](https://support.claude.com/en/articles/17454700-get-started-with-claude-data)・[Claude Motion](https://support.claude.com/en/articles/17454997-get-started-with-claude-motion)、表計算などのファイル作成は [Create and edit files with Claude](https://support.claude.com/en/articles/12111783-create-and-edit-files-with-claude)
- **プラン・提供範囲**: artifacts 自体と Docs・Slides・Design テンプレートは Free を含む全プラン。Data は有料プラン。Sheets・Whiteboards は有料プランで beta。Motion は Team・Enterprise で beta。connectors 連携・データ保存は有料プラン。Enterprise は Owner の設定で既定が変わる。根拠: 17153992
- **注意**: 2026-09-16 に今の形に刷新（リリースノート）。それ以前の chat の artifacts は legacy 扱い（[廃止・終了した機能](#廃止終了した機能)）。ChatGPT の canvas・Gemini の Canvas と 1 対 1 ではない

### Claude Docs

- **概要**: Claude と人が同時に書く「生きた」リッチテキスト文書。コメント・タブ・共有リンク・エクスポート（Word・PDF・Markdown・Google Docs）
- **入口**: 会話で頼むか、Artifacts タブ（claude.ai/artifacts）から作る
- **公式ページ**: [Get started with Claude Docs](https://support.claude.com/en/articles/16923645-get-started-with-claude-docs)、[Claude Docs keyboard shortcuts](https://support.claude.com/en/articles/17458093-claude-docs-keyboard-shortcuts)
- **プラン・提供範囲**: Free を含む全プラン、既定でオン（Enterprise は Organization settings > Artifacts）。根拠: 16923645

### Claude Design

- **概要**: デザイン・モックアップ・プロトタイプ・1 枚資料を作る。design system を取り込める。単独サイトから Claude の artifacts に統合された
- **公式ページ**: [Get started with Claude Design](https://support.claude.com/en/articles/14604416-get-started-with-claude-design)、[Set up your design system in Claude Design](https://support.claude.com/en/articles/14604397-set-up-your-design-system-in-claude-design)、[Move from standalone Claude Design to Claude](https://support.claude.com/en/articles/17440474-move-from-standalone-claude-design-to-claude)
- **プラン・提供範囲**: Free を含む全プラン。根拠: 17440474・17153992
- **注意**: 単独版（claude.ai/design）は 2026-12-14 に終了（下の「廃止・終了した機能」）。Slides（スライド）も同じ artifacts テンプレートの 1 つで、説明は 17153992 にある

## エージェント・自動化

### Claude Cowork

- **概要**: Claude Code と同じエージェント基盤で、複数ステップの仕事（文書・ファイル整理・調査）を任せる。セッションはクラウドで動き、端末をまたいで続く。「新しい Claude experience」では chat と Cowork の区別がなくなり、どの会話でも任せられる
- **入口**: メッセージ欄左下で "Cowork" を選ぶ（web は claude.ai の "Home" タブ）。新しい experience では選択肢が無く、普通に頼む
- **公式ページ**: [Get started with Claude Cowork](https://support.claude.com/en/articles/13345190-get-started-with-claude-cowork)、[Use Claude Cowork on web, desktop, and mobile](https://support.claude.com/en/articles/15520349-use-claude-cowork-on-web-desktop-and-mobile)、[Claude Cowork and chat are one Claude](https://support.claude.com/en/articles/16761823-claude-cowork-and-chat-are-one-claude)、安全面は [Use Claude Cowork safely](https://support.claude.com/en/articles/13364135-use-claude-cowork-safely)
- **プラン・提供範囲**: 有料プランのみ。Desktop は全有料プラン、web・Mobile は Pro・Max・Ultra・Team（Team は beta）と、Owner が有効にした Enterprise。新しい experience は Pro・Max・Ultra に段階展開、Team・Enterprise は **Chat and Cowork unified** がオンのとき。根拠: 13345190・15520349・16761823
- **注意**: ローカルファイル・ローカル connectors・ブラウザ操作・computer use は Desktop アプリ経由（web・Mobile からは Desktop が起動中のときだけ）。15520349 の "What's available on each surface" 表で面ごとの差を確かめる

### Scheduled tasks

- **概要**: Cowork のタスクを定期または手動で実行（日次ブリーフィング・週次レポート等）。端末がオフでもクラウドで動く
- **公式ページ**: [Schedule recurring tasks in Claude Cowork](https://support.claude.com/en/articles/13854387-schedule-recurring-tasks-in-claude-cowork)
- **プラン・提供範囲**: 全有料プラン、Cowork と新しい Claude experience。根拠: 13854387
- **注意**: 外出先から Cowork に指示する持続スレッドは [Assign tasks from anywhere in Claude Cowork](https://support.claude.com/en/articles/13947068-assign-tasks-from-anywhere-in-claude-cowork)

### Claude in Chrome

- **概要**: Chrome 拡張。Claude が Web ページを読み、クリック・遷移する。サイドパネルは Cowork セッションとして動く
- **入口**: Chrome ツールバーの Claude アイコンでサイドパネルを開く
- **公式ページ**: [Get started with Claude in Chrome](https://support.claude.com/en/articles/12012173-get-started-with-claude-in-chrome)、[Use Claude in Chrome safely](https://support.claude.com/en/articles/12902428-use-claude-in-chrome-safely)、権限は [Claude in Chrome permissions guide](https://support.claude.com/en/articles/12902446-claude-in-chrome-permissions-guide)
- **プラン・提供範囲**: 有料プラン（Pro・Max・Ultra・Team・Enterprise）。Enterprise は Owner が Claude in Chrome と Cowork in the cloud を有効にする必要あり。根拠: 12012173

### Cloud browser

- **概要**: Anthropic のサーバー上で動くブラウザを Claude が使う。ログインなどのため利用者が一時的に操作を引き取れる
- **入口**: チャット・タスク内のブラウザのカード → サイドパネルのアイコン（ツールチップ "Open browser in side panel"）
- **公式ページ**: [Use the cloud browser in Claude](https://support.claude.com/en/articles/18442783-use-the-cloud-browser-in-claude)、Desktop 内蔵ブラウザは [Use the built-in browser in Claude Cowork](https://support.claude.com/en/articles/16607400-use-the-built-in-browser-in-claude-cowork)
- **プラン・提供範囲**: beta。Pro・Max・Ultra に段階展開（web・Desktop・Mobile）。Free・Team・Enterprise は対象外。根拠: 18442783
- **注意**: サイトにログインすると、そのチャット・タスク内で Claude が本人として操作できる。引き渡す前にサインアウトする

### Claude Meetings

- **概要**: Google Meet に Claude を参加者として入れ、メモ・質問への回答・artifacts（文書・ホワイトボード・スライド）作成を会議中に行う
- **入口**: Claude の **Meetings**（claude.ai/meetings）→ Google Calendar を接続 → 会議を選び "Add Claude"。自動参加は Settings > Capabilities > Meetings > Auto-join
- **公式ページ**: [Use Claude Meetings](https://support.claude.com/en/articles/18325154-use-claude-meetings)
- **プラン・提供範囲**: beta。Team・Enterprise に段階展開（Claude と Desktop）。ZDR・HIPAA・CMEK の組織は対象外。Team は既定オン、Enterprise は Owner が有効化。根拠: 18325154（リリースノート 2026-11-12）
- **注意**: 参加者全員に文字起こしの同意を取ってから使う

### Claude Duet

- **概要**: 人にメッセージするように使う、能動的なエージェントの research preview。接続したアプリで作業し、送信・支払い・署名・削除の前に確認する
- **公式ページ**: [Get started with Claude Duet](https://support.claude.com/en/articles/17631495-get-started-with-claude-duet)
- **プラン・提供範囲**: research preview。Pro・Max・Ultra、**米国のみ**、ウェイトリストか招待制。Team・Enterprise は未提供。根拠: 17631495
- **注意**: リリースノート（2026-10-21）は「Pro and Max」、記事本文は Ultra も含む。本文を正にする。メモリ・過去チャット検索の設定を共有する

## 音声

### Voice mode

- **概要**: 話しかけて音声で返答を聞く。テキストと切り替えられ、web search や接続したツールも使える
- **入口**: web・Desktop は新規チャットの右下のサウンドウェーブ記号
- **公式ページ**: [Use voice mode](https://support.claude.com/en/articles/11101966-use-voice-mode)、モバイルの音声入力は [Use dictation on Claude Mobile](https://support.claude.com/en/articles/10065434-use-dictation-on-claude-mobile)
- **プラン・提供範囲**: beta。全プラン（Free〜Enterprise）、Mobile・Desktop・web。スマートフォン向けに最適化。根拠: 11101966

## 共有・チーム管理

### Share chats

- **概要**: チャットのスナップショットをリンクで共有する。共有後のメッセージは更新しない限り含まれない
- **入口**: チャット右上の "Share"。公開リンクの停止は "Share" メニューか **Settings > Privacy** の **Shared chats**
- **公式ページ**: [Share and unshare chats](https://support.claude.com/en/articles/10593882-share-and-unshare-chats)、[Public links for shared chats](https://support.claude.com/en/articles/16762437-public-links-for-shared-chats)、[Share a chat with specific people](https://support.claude.com/en/articles/16762496-share-a-chat-with-specific-people)
- **プラン・提供範囲**: 公開リンクは Free・Pro・Max・Ultra。Team・Enterprise は組織内のみ。根拠: 16762437・10593882
- **注意**: 公開リンクは閲覧のみで、添付ファイルは含まれない。検索エンジンとの関係も 16762437 にある

### Share artifacts

- **概要**: artifacts はリンク・組織内・グループ・メール招待で共有できる。既定は非公開
- **公式ページ**: [Share artifacts](https://support.claude.com/en/articles/9547008-share-artifacts)、管理者向けは [Artifacts admin guide for Team and Enterprise plans](https://support.claude.com/en/articles/16994751-artifacts-admin-guide-for-team-and-enterprise-plans)
- **プラン・提供範囲**: 共有方法ごとにプランが違う（リンク共有は有料プラン、グループは Enterprise、legacy artifacts の公開は個人プラン等）。記事冒頭の表で確かめる。根拠: 9547008

### Organization settings

- **概要**: Team・Enterprise の管理画面。メンバー・ロール、connectors・plugins・skills の許可、project 共有、メモリ、モデル、データ保持、監査ログなど
- **入口**: **Organization settings**（例: Organization settings > Connectors、Plugins グループ）
- **公式ページ**: [Roles and permissions](https://support.claude.com/en/articles/9267276-roles-and-permissions)、[Manage members on Team and Enterprise plans](https://support.claude.com/en/articles/13133750-manage-members-on-team-and-enterprise-plans)、[Manage project visibility and sharing](https://support.claude.com/en/articles/9519189-manage-project-visibility-and-sharing)、[Manage custom roles on Enterprise plans](https://support.claude.com/en/articles/13930452-manage-custom-roles-on-enterprise-plans)、新しい experience の設定は [Team](https://support.claude.com/en/articles/18342806-set-up-and-manage-the-new-unified-claude-experience-for-your-team-organization)・[Enterprise](https://support.claude.com/en/articles/17444462-set-up-and-manage-the-new-unified-claude-experience-for-your-enterprise-organization)
- **プラン・提供範囲**: Team・Enterprise。custom roles・グループ・security center などは Enterprise のみ（多くは beta）。根拠: 各記事、ベータ一覧は [Available beta and research preview features](https://support.claude.com/en/articles/14503520-available-beta-and-research-preview-features)
- **注意**: Slack で Claude に仕事を任せる Claude Tag（Team・Enterprise）は [What is Claude Tag?](https://support.claude.com/en/articles/15594475-what-is-claude-tag)

## プランと上限

### Plans

- **概要**: 個人は Free・Pro・Max・**Ultra**、組織は Team・Enterprise（Education 版あり）
- **公式ページ**: [What is the Pro plan?](https://support.claude.com/en/articles/8325606-what-is-the-pro-plan)、[What is the Max plan?](https://support.claude.com/en/articles/11049741-what-is-the-max-plan)、[What is the Ultra plan?](https://support.claude.com/en/articles/17728952-what-is-the-ultra-plan)、[What is the Team plan?](https://support.claude.com/en/articles/9266767-what-is-the-team-plan)、[What is the Enterprise plan?](https://support.claude.com/en/articles/9797531-what-is-the-enterprise-plan)、料金 https://claude.com/pricing
- **注意**: Max・Ultra・Team には Claude API の月次クレジットが付く（記事 17154008、リリースノート 2026-10-07）。モデルごとの提供は [Claude Fable models on your plan](https://support.claude.com/en/articles/15424964-claude-fable-models-on-your-plan) など

### Usage limits

- **概要**: 有料プランは 5 時間ごとのセッション上限と週次上限の 2 種類（モデル別の週次上限がある場合も）。会話の長さはコンテキストウィンドウで決まる別の上限
- **入口**: **Settings > Usage**（Current session と次のリセット時刻）
- **公式ページ**: [How do usage and length limits work?](https://support.claude.com/en/articles/11647753-how-do-usage-and-length-limits-work)、[Usage limit best practices](https://support.claude.com/en/articles/9797557-usage-limit-best-practices)、[How large is the context window on paid Claude plans?](https://support.claude.com/en/articles/8606394-how-large-is-the-context-window-on-paid-claude-plans)、超過分は [Manage usage credits for paid Claude plans](https://support.claude.com/en/articles/12429409-manage-usage-credits-for-paid-claude-plans)・[Team and seat-based Enterprise](https://support.claude.com/en/articles/12005970-manage-usage-credits-for-team-and-seat-based-enterprise-plans)、[What is a limit reset?](https://support.claude.com/en/articles/17007452-what-is-a-limit-reset)
- **プラン・提供範囲**: プラン別の量は各プラン記事の使用量の節（11647753 からリンク）。検証済みの Ultra アカウントには 5 時間上限が無い。根拠: 11647753・17728952
- **注意**: 11647753 の "Ultra plan" のリンクは Ultra の記事（17728952）ではなく月次 API クレジットの記事（17154008）を指している。Ultra の上限は 17728952 を見る

## 廃止・終了した機能

### Standalone Claude Design

- **概要**: 単独サイト claude.ai/design は **2026-12-14 に終了**。それまでは使える。新しいデザイン・design system・スライドは Claude の artifacts として作られる
- **公式ページ**: [Move from standalone Claude Design to Claude](https://support.claude.com/en/articles/17440474-move-from-standalone-claude-design-to-claude)
- **注意**: design system は "Move to Claude" で移せるが、チャットとコメントは移らない。移行済みの design system は単独版で読み取り専用になる。project は終了前に移すかダウンロードする

### Legacy artifacts

- **概要**: 2026-09-16 より前に chat で作った artifacts。動作・公開・共有は続くが、新しくは作れない
- **公式ページ**: [What are artifacts and how do I use them?](https://support.claude.com/en/articles/17153992-what-are-artifacts-and-how-do-i-use-them)、[Share artifacts](https://support.claude.com/en/articles/9547008-share-artifacts)
- **注意**: 非公開化すると保存データが消えるなど、新しい artifacts と挙動が違う。ほかの名称変更（Customize → Plugins、旧メモリ → 新メモリ、旧 Settings レイアウト）は各機能の「別名」「注意」に書いた
