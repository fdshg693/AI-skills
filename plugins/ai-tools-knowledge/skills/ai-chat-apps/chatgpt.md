# ChatGPT（chatgpt.com）機能マップ

最終確認日: 2026-11-18 ／ 対象: chatgpt.com の WEB 版。デスクトップアプリ固有の機能は [desktop.md](desktop.md)。モバイルは記事に差分が書かれている範囲だけ注記する

機能名 → 公式ページの索引。上限・料金・対応プランの**具体値は書かない**（変わりやすい）。回答前に必ずリンク先の本文を取る（取り方は [SKILL.md](SKILL.md)）。

## 情報源

- ヘルプセンター: https://help.openai.com/en/
- リリースノート: [ChatGPT release notes](https://help.openai.com/en/articles/6825453-chatgpt-release-notes)（全プラン共通。巨大なので先頭から読む）、[ChatGPT Business release notes](https://help.openai.com/en/articles/11391654-chatgpt-business-release-notes)、[ChatGPT Enterprise and Edu release notes](https://help.openai.com/en/articles/10128477-chatgpt-enterprise-and-edu-release-notes)
- プランと上限: [Understanding ChatGPT and Codex usage limits](https://help.openai.com/en/articles/20001625-understanding-chatgpt-and-codex-usage-limits)、料金ページ https://chatgpt.com/pricing（価格は JS 描画で抜けることがある）。詳細は「[プランと上限](#プランと上限)」
- 範囲外（別物。利用者向けアプリの仕様として流用しない）: 開発者ドキュメント developers.openai.com（Apps SDK・MCP サーバーの構築手順。プラン条件はヘルプと食い違うことがある）、OpenAI API、Codex（`codex-docs` スキル）、ChatGPT Ads

## 目次

- [プロジェクト](#プロジェクト) — Projects
- [カスタムアシスタント・再利用できる指示](#カスタムアシスタント再利用できる指示) — GPTs / Plugins / Skills
- [外部連携](#外部連携) — Connected apps / Custom MCP servers
- [メモリ・パーソナライズ](#メモリパーソナライズ) — Memory / Custom instructions / Personality
- [調査](#調査) — Search / Deep research / File uploads
- [作成物](#作成物) — Images / Writing blocks and code blocks / Space / ChatGPT Sites
- [エージェント・自動化](#エージェント自動化) — ChatGPT Work / Scheduled tasks / Dots / Workspace agents
- [音声](#音声) — ChatGPT Voice / ChatGPT Record
- [共有・チーム管理](#共有チーム管理) — Shared links / Workspace admin
- [プランと上限](#プランと上限) — Usage limits / Free tier
- [廃止・終了した機能](#廃止終了した機能) — ChatGPT agent / Canvas / Group chats / ChatGPT Atlas / Sora / Pulse

## プロジェクト

### Projects

- **概要**: 関連するチャット・ファイル・指示をまとめる。プロジェクト指示はそのプロジェクト内だけで効き、全体の custom instructions より優先される。共有（chat／edit 権限）もできる
- **入口**: サイドバーの **New project**。指示は ••• → **Project settings**
- **公式ページ**: [Projects in ChatGPT](https://help.openai.com/en/articles/10169521-projects-in-chatgpt)
- **プラン・提供範囲**: サインインしたユーザー（プランと workspace 設定次第）。共有は Free〜Enterprise/Edu の web とモバイル。ファイル数・共同編集者数はプラン依存（本文に表あり）。根拠: 同上
- **注意**: GPT で作ったチャットはプロジェクトへ移せない。共有プロジェクトはプロジェクト内だけのメモリになる。Space（[作成物](#space)）とは別物で、Space が入ってもプロジェクトは残る

## カスタムアシスタント・再利用できる指示

### GPTs

- **別名**: custom GPTs／GPT Store（公開先）
- **概要**: 指示・知識ファイル・機能を組み合わせた目的別の ChatGPT。**廃止予定で、移行先は Plugins**
- **入口**: **Explore GPTs**（利用）。移行は **My GPTs** → **Migrate to plugin**
- **公式ページ**: [GPTs in ChatGPT](https://help.openai.com/en/articles/8554407-gpts-in-chatgpt)、[Custom GPT retirement and migration FAQ](https://help.openai.com/en/articles/20001519-custom-gpt-retirement-and-migration-faq)、[Creating and editing GPTs](https://help.openai.com/en/articles/8554397-creating-and-editing-gpts)、[Sharing and publishing GPTs](https://help.openai.com/en/articles/8798878-sharing-and-publishing-gpts)
- **プラン・提供範囲**: 既存 GPT の利用はサインインした全ユーザー。**個人アカウント（Free・Go・Plus・Pro）は新規作成・公開ができない**。Business・Enterprise・Edu は workspace 設定次第。対象の Enterprise workspace は 2026-10-26 で新規作成終了（FedRAMP を除く）。根拠: GPTs in ChatGPT
- **注意**: 標準の廃止日は **2026-12-11**（FedRAMP と延期承認済み workspace は 2027-02-11）。廃止日に GPT とそのページは使えなくなる（過去の会話は残る）。移行で指示は plugin 内の skill に、知識ファイルは参照ファイルに、connected apps は apps になる。custom actions とモデル選択は移らない（custom actions の置き換えは custom MCP server が要ることがある）。移行後の元 GPT は読み取り専用。継続作業用ならプロジェクトでもよい、と FAQ にある。今から作る人には GPT ではなく Plugins を案内する

### Plugins

- **別名**: 日本語 UI「プラグイン」（サイドバー。2026-11-18 Plus の実画面で確認）
- **概要**: skills（指示・手順）、connected apps、app templates、extensions（対話型 UI）を束ねる単位。ChatGPT（Chat・Work）と Codex で使う。関連するときは自動で使われ、`@` でも呼べる
- **入口**: サイドバーの **Plugins**（directory。Public／Your workspace／Personal／Installed）。作成は **Plugin Creator** を入れて `@plugin-creator` に頼むか、**Plugins** → **Add (+)**。会話では `@`・**+**・コンポーザーの **Plugins**
- **公式ページ**: [Plugins in ChatGPT](https://help.openai.com/en/articles/20001256-plugins-in-chatgpt)、[Plugin use cases and prompts](https://help.openai.com/en/articles/12084614-plugin-use-cases-and-prompts)、[Troubleshooting plugins and apps in ChatGPT](https://help.openai.com/en/articles/20001497-troubleshooting-plugins-and-apps-in-chatgpt)
- **プラン・提供範囲**: directory は全プラン。個々の plugin の導入・利用はプラン・workspace・ロール・地域・中身次第。workspace 内での共有は Business・Enterprise。根拠: Plugins in ChatGPT
- **注意**: 2023 年にベータで出た旧「ChatGPT plugins」（リリースノートの古い項目）とは別物。**Desktop only** の plugin や、local MCP apps を含む plugin はデスクトップアプリでしか動かない。ZIP のアップロード・GitHub からの marketplace 取り込みもある（権限が要る）。個人の plugin を Public に出すには別の plugin submission process が要ると FAQ にあるが、その手順の記事はヘルプセンターに無い（2026-11-18、索引を submit／submission／plugin directory で検索）。GPT ストアの後継を聞かれたら、そう明示する

### Skills

- **別名**: Skills in ChatGPT
- **概要**: 指示・例・コードを持つ再利用できるワークフロー。関連するとき自動で使われ、複数併用できる。plugin の中身にもなる
- **入口**: サイドバー **Plugins** → **Plugin Directory** の **Skills** タブ → **Create**（**Create with chat**／**Create with editor**／**Upload from your computer**）
- **公式ページ**: [Skills in ChatGPT](https://help.openai.com/en/articles/20001066-skills-in-chatgpt)
- **プラン・提供範囲**: Business・Enterprise・Healthcare・Edu の対象ユーザー（workspace 設定次第）。根拠: 同上、Plugins in ChatGPT の FAQ「Why don't I have access to skills?」
- **注意**: 個人プランでは skills の作成画面は案内されていないが、GPT 移行や Plugin Creator で作る plugin には skill が含まれる。アップロードした skill はスキャンされ、**Needs Review**／**Blocked** になることがある

## 外部連携

### Connected apps

- **別名**: 旧称 connectors（2025-12-18 のリリースノートで apps に呼び替え）
- **概要**: Google Drive・Slack などのサービスを会話で使う。検索・参照、deep research の情報源、対話型 UI、書き込み操作。アプリ単体か plugin の一部として入る
- **入口**: **Settings > Plugins**（ごく古いモバイル版は **Apps**）。会話では `@` か **+**
- **公式ページ**: [Connected apps in ChatGPT](https://help.openai.com/en/articles/11487775-connected-apps-in-chatgpt)、[Connecting and managing app accounts in ChatGPT](https://help.openai.com/en/articles/20001494-connecting-and-managing-app-accounts-in-chatgpt)、[Managing app permissions in ChatGPT](https://help.openai.com/en/articles/20001495-managing-app-permissions-in-chatgpt)
- **プラン・提供範囲**: アプリ・プラン・地域・workspace・ロール・モデル・利用画面で変わる。根拠: Connected apps in ChatGPT
- **注意**: アプリのイベントで起動するタスク（Gmail・Slack・GitHub）は Work で動き、Free・Go では使えない（[Scheduled tasks](#scheduled-tasks)）。plugin 経由の金融取引は米国の 18 歳以上のみ

### Custom MCP servers

- **別名**: 日本語 UI「カスタム MCP サーバーを追加」（**Plugins** → 右上「追加」の中。2026-11-18 Plus の実画面で確認）
- **概要**: 自作・他者作のリモート MCP サーバーを繋ぎ、plugin として使う。ローカルのサーバーは直接は繋げず、Secure MCP Tunnel を使う
- **入口**: **Plugins** → プラスボタン → **Add custom MCP server** → 接続先（HTTPS の URL か **Tunnel**）・認証 → リスク警告の **I understand and want to continue** → **Create as a plugin**。**Developer Mode を先に有効にする必要はない**（旧手順）。workspace 公開は Admin console → **Plugins** → **Manage Legacy Apps**
- **公式ページ**: [Connecting custom MCP servers in ChatGPT](https://help.openai.com/en/articles/12584461-connecting-custom-mcp-servers-in-chatgpt)。構築側の参考（範囲外）: developers.openai.com `/api/docs/guides/custom-mcp-server`
- **プラン・提供範囲**: **公式どうしで食い違う**。ヘルプ記事は「Business と Enterprise/Edu の ChatGPT web」とし、FAQ で「Full MCP は Business・Enterprise/Edu のみ、Pro は read/fetch 権限で接続可」とする（Plus への言及なし）。開発者ドキュメントはプラン制限を書かず、個人の plugins に出るとする。2026-11-18 に日本の Plus の実画面で追加画面が開くことを確認した。根拠: 上記 2 ページ、[tests/scenarios.md](tests/scenarios.md) の S1 補足
- **注意**: 回答では両方の記述を示し、実画面での確認を促す。Plus で書き込みツールが使えるかは未確認。モバイルからは追加できない（web のみ）。地域制限は「なし」と FAQ にある。workspace では作成は管理者・オーナー（Enterprise/Edu は RBAC で許可された人）、公開は管理者・オーナーのみ

## メモリ・パーソナライズ

### Memory

- **概要**: 保存したメモリ・過去のチャット・Library/Space のファイルなどから関連情報を覚えて使う。メモリの要約を確認・修正・削除できる
- **入口**: **Settings** → **Personalization** → **Memory**（**Reference saved memories**／**Reference chat history** などは表示される範囲で）
- **公式ページ**: [Memory in ChatGPT](https://help.openai.com/en/articles/8590148-memory-in-chatgpt)、[Memory FAQ (Business Version)](https://help.openai.com/en/articles/9295112-memory-faq-business-version)
- **プラン・提供範囲**: プラン・地域・プラットフォーム・workspace で機能と設定項目が変わる。根拠: Memory in ChatGPT
- **注意**: 新旧 2 つのメモリ体験があり、切り替えられる場合がある。プロジェクトのメモリは Projects の記事側

### Custom instructions

- **概要**: すべてのチャットに効く指示
- **入口**: web・デスクトップは **Settings** → **Personalization** → **Enable customization** → **Custom Instructions**（iOS・Android は **Customize ChatGPT**）
- **公式ページ**: [ChatGPT Custom Instructions](https://help.openai.com/en/articles/8096356-chatgpt-custom-instructions)
- **プラン・提供範囲**: 全プラン、web・デスクトップ・iOS・Android。根拠: 同上

### Personality

- **概要**: 応答の口調・スタイル（Professional・Friendly・Candid など）を選ぶ。できることや安全ルールは変わらない
- **入口**: web はプロフィールアイコン → **Personalization** → **Base style and tone**
- **公式ページ**: [Customizing Your ChatGPT Personality](https://help.openai.com/en/articles/11899719-customizing-your-chatgpt-personality)、[Characteristics in ChatGPT](https://help.openai.com/en/articles/20001038-characteristics-in-chatgpt)
- **注意**: プリセットは増減する（「Nerdy」は廃止済み。リリースノート）

## 調査

### Search

- **概要**: Web 検索して出典付きで答える
- **入口**: `/` → **Search**、または回答の **Try again** → **Search the web**
- **公式ページ**: [Searching the web with ChatGPT](https://help.openai.com/en/articles/9237897-searching-the-web-with-chatgpt)、[ChatGPT search for Enterprise and Edu](https://help.openai.com/en/articles/10093903-chatgpt-search-for-enterprise-and-edu)
- **プラン・提供範囲**: Free〜Edu の全プラン。サインインなしでも使える。根拠: Searching the web with ChatGPT

### Deep research

- **概要**: 計画を立てて多数の情報源（Web・指定サイト・アップロード・connected apps）を調べ、出典付きのレポートを作る。実行中に介入できる
- **入口**: `/Deepresearch`、**+** の **Deep research**、サイドバーの **Deep research**
- **公式ページ**: [Deep research in ChatGPT](https://help.openai.com/en/articles/10500283-deep-research-in-chatgpt)
- **プラン・提供範囲**: 回数はプラン依存（製品内のカウンターで確認）。国・地域でも提供が変わる。根拠: 同上
- **注意**: connected apps は読み取りだけ使う（custom MCP も read/fetch のみ）。旧 deep research モードは 2026-03-26 に終了

### File uploads

- **概要**: 文書・表・スライド・画像・音声をアップロードして質問・分析する
- **公式ページ**: [Uploading files and audio to ChatGPT](https://help.openai.com/en/articles/8555545-uploading-files-and-audio-to-chatgpt)、[Data analysis with ChatGPT](https://help.openai.com/en/articles/8437071-data-analysis-with-chatgpt)、[Using Library to manage files in ChatGPT](https://help.openai.com/en/articles/20001052-using-library-to-manage-files-in-chatgpt)
- **プラン・提供範囲**: 文書・画像は Free と有料（プラン別の上限あり）。音声のアップロードは有料プランと workspace のみ。根拠: Uploading files and audio to ChatGPT
- **注意**: 音声の文字起こしは Chat だけで、Work・Codex では不可。Space が使えるアカウントでは Library が Space に置き換わる

## 作成物

### Images

- **別名**: ChatGPT Images
- **概要**: 画像の生成・編集。GIF、参照画像の保存、テンプレート、スケッチからの生成
- **入口**: プロンプトで頼むか **Images** を選ぶ。テンプレートはサイドバー **Images** → **Templates**
- **公式ページ**: [Images in ChatGPT](https://help.openai.com/en/articles/11084440-images-in-chatgpt)、[ChatGPT Image Inputs FAQ](https://help.openai.com/en/articles/8400551-chatgpt-image-inputs-faq)
- **プラン・提供範囲**: 全プラン、web・iOS・Android。「Images with thinking」は一部の有料プランのみ。根拠: Images in ChatGPT
- **注意**: 公式の DALL·E GPT は 2026-08-30 に廃止。Work ではテンプレート未対応

### Writing blocks and code blocks

- **別名**: 旧 Canvas の後継（[Canvas](#canvas) 参照）
- **概要**: 応答の中に編集できる下書き（writing block）と、プレビュー・実行できるコード（code block）を出す
- **公式ページ**: [Working with writing blocks and code blocks in ChatGPT](https://help.openai.com/en/articles/20001246-working-with-writing-blocks-and-code-blocks-in-chatgpt)
- **プラン・提供範囲**: 使える操作はブロックの種類・端末・プラン・workspace・展開状況で変わる。根拠: 同上

### Space

- **概要**: pages（共同編集できる文書）・ファイル・slides をまとめて共有する場所。Pages、Slides（作成・共同編集・書き出し）を含む
- **入口**: Slides は **Work** でプレゼンの作成を頼む
- **公式ページ**: [Getting started with Space in ChatGPT](https://help.openai.com/en/articles/20001549-getting-started-with-space-in-chatgpt)、[Creating and collaborating on slides in ChatGPT](https://help.openai.com/en/articles/20001605-creating-and-collaborating-on-slides-in-chatgpt)
- **プラン・提供範囲**: 作成・編集は Pro・Business・Enterprise（web とデスクトップ。モバイルは閲覧のみ）。根拠: Getting started with Space
- **注意**: Space が使えるアカウントでは Library を置き換える。Projects は別に残る

### ChatGPT Sites

- **概要**: 対話型の Web サイト・軽量アプリを作って公開・共有する。MCP app をホストして plugin に入れることもできる
- **入口**: サイトを作るよう頼むか、プロンプトで **@Sites**
- **公式ページ**: [Creating and using ChatGPT Sites](https://help.openai.com/en/articles/20001339-creating-and-using-chatgpt-sites)、[Hosting a plugin with ChatGPT Sites](https://help.openai.com/en/articles/20001547-hosting-a-plugin-with-chatgpt-sites)、[Managing ChatGPT Sites for your workspace](https://help.openai.com/en/articles/20001338-managing-chatgpt-sites-for-your-workspace)
- **プラン・提供範囲**: Plus・Pro と Business・Enterprise workspace（web とデスクトップ）。根拠: Creating and using ChatGPT Sites
- **注意**: 作成・編集は Codex の使用量を消費し、実行・ホスティングの使用量は別

## エージェント・自動化

### ChatGPT Work

- **別名**: Work（Chat と並ぶモード）
- **概要**: 長い多段の作業と成果物（文書・表・スライド）のためのエージェント。cloud browser で Web 操作もする。旧 ChatGPT agent（[廃止](#chatgpt-agent)）の後継
- **入口**: web・モバイルで **Work** を選ぶ
- **公式ページ**: [ChatGPT Work and Codex](https://help.openai.com/en/articles/20001275-chatgpt-work-and-codex)、[Using cloud browser in ChatGPT](https://help.openai.com/en/articles/20001280-using-cloud-browser-in-chatgpt)、[Creating and editing documents, spreadsheets, and presentations with ChatGPT Work](https://help.openai.com/en/articles/20001278-creating-and-editing-documents-spreadsheets-and-presentations-with-chatgpt-work)
- **プラン・提供範囲**: 対象の有料プラン（web・モバイル、プラン次第でデスクトップ）。cloud browser は Free・Go 不可。根拠: 上記 2 本目まで
- **注意**: Work の使用量は Codex と同じ枠組み。Work 用のモデルは Chat のモデル選択とは別

### Scheduled tasks

- **概要**: 1 回・定期のタスク、変化の監視、アプリのイベントで起動するタスク。タスクはリンクで共有できる
- **入口**: **Scheduled**。通知は **Settings > Notifications**
- **公式ページ**: [Scheduled tasks in ChatGPT](https://help.openai.com/en/articles/10291617-scheduled-tasks-in-chatgpt)、[Creating and managing team tasks in ChatGPT](https://help.openai.com/en/articles/20001540-creating-and-managing-team-tasks-in-chatgpt)
- **プラン・提供範囲**: 有効なタスク数はプラン依存（Free を含む。本文に表あり）。イベント起動のタスクは Plus 以上と workspace（Free・Go 不可）。根拠: Scheduled tasks in ChatGPT
- **注意**: Pulse の後継（[Pulse](#pulse)）

### Dots

- **別名**: your dot
- **概要**: 目標を渡すと会話の合間も作業を進める常駐エージェント。専用のクラウドコンピューターを持つ。ChatGPT Wallet（代理購入）は dot の中で使う
- **入口**: デスクトップアプリ・デスクトップ web・モバイルアプリで作成（オンボーディングに従う）
- **公式ページ**: [Getting started with your dot](https://help.openai.com/en/articles/20001530-getting-started-with-your-dot)、[Making purchases with ChatGPT Wallet](https://help.openai.com/en/articles/20001654-making-purchases-with-chatgpt-wallet)、[Managing dots in ChatGPT workspaces](https://help.openai.com/en/articles/20001554-managing-dots-in-chatgpt-workspaces)
- **プラン・提供範囲**: Pro（18 歳以上、EEA・スイス・英国を除く）と Business Premium、対象の Enterprise・Edu・Healthcare。Wallet は米国の Pro のみ・段階展開。根拠: 上記 2 本
- **注意**: 2026-09-29 開始、Wallet は 2026-11-13 開始の新機能

### Workspace agents

- **別名**: ChatGPT workspace agents
- **概要**: 業務の定型作業用エージェントを作り、テスト・共有・Slack で利用する
- **入口**: サイドバーの **Agents**
- **公式ページ**: [ChatGPT Workspace Agents for Enterprise and Business](https://help.openai.com/en/articles/20001143-chatgpt-workspace-agents-for-enterprise-and-business)
- **プラン・提供範囲**: Business・Enterprise（Enterprise は既定でオフ）。根拠: 同上

## 音声

### ChatGPT Voice

- **概要**: リアルタイムの音声会話。**Live**（GPT-Live）は検索・メモリ・plugins を使える。Work でも使える
- **入口**: モードの切り替えは **Settings > Voice**
- **公式ページ**: [ChatGPT Voice](https://help.openai.com/en/articles/20001274-chatgpt-voice)、[Voice Dictation - FAQ](https://help.openai.com/en/articles/12168547-voice-dictation-faq)
- **プラン・提供範囲**: Free を含む全プラン（プラン別の時間上限は本文の表）。workspace は設定次第。根拠: ChatGPT Voice
- **注意**: **Advanced と Standard は 2026-12-11 に廃止**し、Live へ自動で切り替わる（2026-11-10 発表）。動画・画面共有は当面 Advanced（モバイル）で提供

### ChatGPT Record

- **概要**: 会議や音声メモを録音し、要約・メモにする
- **公式ページ**: [ChatGPT Record](https://help.openai.com/en/articles/11487532-chatgpt-record)
- **プラン・提供範囲**: **macOS デスクトップアプリのみ**（web 版は無い）。対象プランは本文の冒頭と注記で書き方が違う。根拠: 同上
- **注意**: デスクトップアプリの Meetings plugin（2026-09-29、ベータ）が会議メモの新しい手段として出ている（[The Meetings plugin in ChatGPT](https://help.openai.com/en/articles/20001546-the-meetings-plugin-in-chatgpt)）

## 共有・チーム管理

### Shared links

- **概要**: 会話・個別の応答・scheduled task をリンクで共有する
- **公式ページ**: [Sharing conversations and scheduled tasks in ChatGPT](https://help.openai.com/en/articles/7925741-sharing-conversations-and-scheduled-tasks-in-chatgpt)
- **プラン・提供範囲**: タスクの共有は Free・Go を含む対象ユーザー。根拠: 同上
- **注意**: プロジェクトの共有は [Projects](#projects)、Space の共有は [Space](#space)

### Workspace admin

- **別名**: Business／Enterprise／Edu の管理（Admin console・Workspace settings）
- **概要**: メンバー・ロール・RBAC、apps と plugins の有効化、custom MCP の公開、SSO・SCIM
- **公式ページ**: [ChatGPT Business overview](https://help.openai.com/en/articles/8792828-chatgpt-business-overview)、[What is ChatGPT Enterprise?](https://help.openai.com/en/articles/8265053-what-is-chatgpt-enterprise)、[ChatGPT Enterprise admin quickstart](https://help.openai.com/en/articles/20001264-chatgpt-enterprise-admin-quickstart)、[Admin controls, security, and compliance for plugins and apps](https://help.openai.com/en/articles/11509118-admin-controls-security-and-compliance-for-plugins-and-apps)、[Managing feature access with role-based access control in ChatGPT](https://help.openai.com/en/articles/11750701-managing-feature-access-with-role-based-access-control-in-chatgpt)
- **注意**: 変更点は Business・Enterprise/Edu それぞれのリリースノート（[情報源](#情報源)）

## プランと上限

### Usage limits

- **概要**: プラン別の使用量の考え方と、workspace プランのモデル・上限
- **入口**: 残量とリセット時刻は **Settings → Usage**（下の注意の移行後）
- **公式ページ**: [Understanding ChatGPT and Codex usage limits](https://help.openai.com/en/articles/20001625-understanding-chatgpt-and-codex-usage-limits)、[ChatGPT Business models and limits](https://help.openai.com/en/articles/12003714-chatgpt-business-models-and-limits)、[ChatGPT Enterprise and Edu models and limits](https://help.openai.com/en/articles/11165333-chatgpt-enterprise-and-edu-models-and-limits)、[About ChatGPT Pro tiers](https://help.openai.com/en/articles/9793128-about-chatgpt-pro-tiers)、[What is ChatGPT Plus?](https://help.openai.com/en/articles/6950777-what-is-chatgpt-plus)、[What is ChatGPT Go?](https://help.openai.com/en/articles/11989085-what-is-chatgpt-go)
- **注意**: **2026 年 12 月から Plus・Pro・Business の使用量は ChatGPT と Codex で共通の枠になり、トークンで測る**（Instant の Chat は消費しない）と予告されている。12 月以降の質問は、この記事とリリースノートで移行後の状態を確かめる。機能別の上限（Voice・scheduled tasks・projects など）は各機能の記事にある

### Free tier

- **概要**: 無料プランで使える機能と制限
- **公式ページ**: [ChatGPT Free Tier FAQ](https://help.openai.com/en/articles/9275245-chatgpt-free-tier-faq)
- **注意**: 本文に「Discover and use GPTs」が残っているが、GPT の新規作成は不可で GPT 自体も廃止予定（[GPTs](#gpts)）

## 廃止・終了した機能

### ChatGPT agent

- **別名**: agent mode（`/agent`）、旧 Operator を統合したもの
- **概要**: **提供終了**。記事冒頭に「no longer available」とあり、移行先は [ChatGPT Work](#chatgpt-work)（Web 操作は cloud browser）
- **公式ページ**: [ChatGPT agent](https://help.openai.com/en/articles/11752874-chatgpt-agent)、[ChatGPT agent - release notes](https://help.openai.com/en/articles/11794368-chatgpt-agent-release-notes)
- **注意**: 記事の本文は終了前の内容（対応プラン・回数）のまま残っている。終了日はリリースノートに見当たらない

### Canvas

- **概要**: 2026-05-28 から新しいモデル（GPT-5.5 Instant・Thinking 以降）では使えない。後継は [Writing blocks and code blocks](#writing-blocks-and-code-blocks)。有料ユーザーはレガシーモデルが終わるまで一時的に使える
- **公式ページ**: [ChatGPT release notes](https://help.openai.com/en/articles/6825453-chatgpt-release-notes)（2026-05-28「GPT-5.5 Instant Update」）
- **注意**: Projects や Enterprise/Edu の上限記事、Record の記事にはまだ canvas の記述が残っている

### Group chats

- **概要**: 2026-07-09 から新規作成・参加ができない。既存のものは閲覧でき、英国では読み取り専用
- **公式ページ**: [Retiring group chats in ChatGPT](https://help.openai.com/en/articles/12703475-retiring-group-chats-in-chatgpt)

### ChatGPT Atlas

- **概要**: ChatGPT のブラウザアプリ。2026-08-09 に停止予定と告知され、現在は廃止済み。ブラウザ操作は ChatGPT（Work の cloud browser、デスクトップアプリの内蔵ブラウザ）へ移った
- **公式ページ**: [ChatGPT Atlas retirement](https://help.openai.com/en/articles/20001371-chatgpt-atlas-retirement)

### Sora

- **概要**: Sora の web・アプリは 2026-04-26 に終了（API は 2026-09-24）。データの書き出しは sora.chatgpt.com/sunset
- **公式ページ**: [What to know about the Sora discontinuation](https://help.openai.com/en/articles/20001152-what-to-know-about-the-sora-discontinuation)

### Pulse

- **概要**: 2026-06-17 に終了を告知（Pro は 14 日間の猶予）。毎日の更新は [Scheduled tasks](#scheduled-tasks) で代わりに作る
- **公式ページ**: [ChatGPT release notes](https://help.openai.com/en/articles/6825453-chatgpt-release-notes)（2026-06-17「Scheduled tasks in ChatGPT」）
