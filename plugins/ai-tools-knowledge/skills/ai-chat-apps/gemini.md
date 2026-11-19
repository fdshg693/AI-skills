# Gemini アプリ（gemini.google.com）機能マップ

最終確認日: 2026-11-18 ／ 対象: gemini.google.com の WEB 版。デスクトップアプリ（Mac・Windows）固有の機能は [desktop.md](desktop.md)。モバイルは記事に差分が書かれている範囲だけ注記する

機能名 → 公式ページの索引。上限・料金・対応プランの**具体値は書かない**（変わりやすい）。回答前に必ずリンク先の本文を取る（取り方は [SKILL.md](SKILL.md)）。Gemini には索引スクリプトが無い。このファイルに無い記事は `tav search "site:support.google.com/gemini <語>"` で探す。

## 情報源

- ヘルプセンター: https://support.google.com/gemini/?hl=en （Gemini Apps Help）。記事は `https://support.google.com/gemini/answer/<id>?hl=en`。WEB 版の手順は `&co=GENIE.Platform%3DDesktop` 付きの URL（下では付けてある）
- 2026-11-18 の確認は、support.google.com が `page` で HTTP 429 を返したため `tav extract` で本文を取った。プラン条件・上限は `page` かブラウザで取り直してから答える。本文を取れなかった記事は「本文未確認」と書いた
- リリースノート: https://gemini.google/release-notes/ （個人向け Gemini アプリ。日本語ロケールで返ると日本語訳と英語原文が混在する。新しい項目ほど英語のまま）
- プランと上限: [Gemini Apps limits & feature availability](https://support.google.com/gemini/answer/16275805?hl=en)（個人アカウント）、[Use Gemini Apps with a work or school Google Account](https://support.google.com/gemini/answer/14620100?hl=en)（Workspace 版の表）、料金ページ https://gemini.google/subscriptions/ （価格は JS 描画で抜けることがある）
- 概要ページ: `https://gemini.google/overview/<機能>/`（canvas・deep-research・gemini-live・personal-intelligence 等）。機能の紹介だけ。手順と条件はヘルプを正にする
- 範囲外（別物。Gemini アプリの仕様として流用しない）:
  - **Google Workspace の Gemini**（Gmail・Docs 等のサイドパネル）: 上限は別。[Usage limits for Gemini with Google Workspace](https://support.google.com/a/users/answer/14796585)。仕事・学校アカウントで gemini.google.com を使う場合は Gemini アプリ側（下の [Work and school accounts](#work-and-school-accounts)）
  - **Gemini Enterprise**: 企業向けの別製品。14620100 の表にある「Gemini Enterprise - Legacy」「Gemini Business - Legacy」は販売終了した Workspace エディション名で、これとも別
  - **Google AI Studio・Gemini API**（ai.google.dev）、**Gemini CLI**、**Google Antigravity**: 開発者向け。Mac アプリの Antigravity 統合も本ファイルでは扱わない
  - **Connected Apps Platform・Gemini Developer Mode**（developers.google.com/connected-apps）: MCP サーバーを作る開発者向けの文書。利用者の接続手順は [Custom apps (MCP)](#custom-apps-mcp)
  - **Gemini Notebook**（別ヘルプセンター https://support.google.com/gemininotebook ）: 情報源を読み込むリサーチ用の独立したアプリ。Gemini アプリの [Notebooks](#notebooks) と同期する（後述）。Gemini Notebook 単体の上限・共有はそちらのヘルプ。ヘルプ内のアンカー名から旧 NotebookLM と思われるが、改名を明記した公式記述は未確認。Gemini 側の古い記事は今も「NotebookLM notebooks」と書く
  - **Gemini Spark** はアプリ内の機能だが、ヘルプ記事が無くリリースノートだけ（[Gemini Spark](#gemini-spark)）

## 目次

- [プロジェクト](#プロジェクト) — Notebooks
- [カスタムアシスタント・再利用できる指示](#カスタムアシスタント再利用できる指示) — Skills / Gems
- [外部連携](#外部連携) — Connected Apps / Custom apps (MCP)
- [メモリ・パーソナライズ](#メモリパーソナライズ) — Memory / Personal Intelligence / Instructions for Gemini
- [調査](#調査) — Deep Research
- [作成物](#作成物) — Canvas / Images (Nano Banana) / Create video / Create music / Storybook
- [エージェント・自動化](#エージェント自動化) — Tasks / Schedules / Auto browse (Gemini in Chrome) / Gemini Spark
- [音声](#音声) — Gemini Live / Audio Overviews
- [共有・チーム管理](#共有チーム管理) — Share a chat / Share a Gem / Work and school accounts
- [プランと上限](#プランと上限) — Plans and limits / Models
- [廃止・終了した機能](#廃止終了した機能) — Gems from Google Labs and Opal / Extensions / Gemini Advanced

## プロジェクト

### Notebooks

- **概要**: プロジェクト単位の作業場所。ソース（ファイル・Drive・URL・テキスト）と指示を持ち、ノートブック内のチャットを続けて覚える。学習用の Study notebooks、Business Profile と繋ぐ business notebooks もある
- **入口**: サイドバーの "Notebooks" → **New notebook**。ソースは **Add sources**。既存チャットはチャット横の More → **Add to notebook**
- **公式ページ**: [Organize your projects with notebooks in Gemini Apps](https://support.google.com/gemini/answer/16972047?hl=en&co=GENIE.Platform%3DDesktop)。上限は Gemini Notebook 側の記事 [Gemini Notebook plans](https://support.google.com/gemininotebook/answer/16213268?hl=en)（別製品の記事。Gemini アプリから使うときも同じ値かは未確認）
- **プラン・提供範囲**: Gemini Notebook が Gemini アプリに接続されていること（多くの地域は自動、EEA は手動接続）。WEB とモバイル（Mac アプリは一部のみ）。段階展開中。無料プランで使えるかは 16972047 に書かれていない（Gemini Notebook 側は AI プランなしでも使え、16213268 に無料の上限がある）。根拠: 16972047
- **注意**: notebooks は Gemini Notebook（別アプリ・別ヘルプ）と相互に同期する。Gemini Notebook で共有されたノートブックは Gemini アプリのサイドバーに出ない。History（Keep Activity）がオフだと自動保存・ノートブックのメモリ・Drive ソース・Study／business notebooks が使えない。共有の仕様は Gemini アプリ側の記事に無いので、gemininotebook ヘルプから類推して断定しない

## カスタムアシスタント・再利用できる指示

### Skills

- **概要**: 再利用できる指示（`SKILL.md`＋参照ファイル）。どのチャット・タスクでも使え、関連すると自動で適用され、複数を重ねて使える。Gems の後継
- **入口**: 上部の **Skills**（Skills ページ。Gemini と対話して作る・テンプレート・`SKILL.md` やフォルダ／.zip のアップロード）。チャットで `/`（今後 `@`）＋スキル名で指定。リリースノート（2026-10-13）では左メニューの［カスタマイズ］からも追加できる
- **公式ページ**: [Create & manage skills for Gemini Apps](https://support.google.com/gemini/answer/17094296?hl=en&co=GENIE.Platform%3DDesktop)、[Write effective skills for Gemini Apps](https://support.google.com/gemini/answer/17102773?hl=en)、[About the transition from Gems to skills](https://support.google.com/gemini/answer/18560919?hl=en)
- **プラン・提供範囲**: 18 歳以上・個人アカウント（仕事・学校アカウントは今後）。WEB・モバイル・Mac アプリ。ファイルのアップロードで作るのは WEB と Mac アプリだけ。根拠: 17094296・18560919
- **注意**: 他プラットフォームの `SKILL.md` を取り込める。インターネットにアクセスするスクリプトは不可。Canvas・Deep Research・Create video・Create music・Guided learning とはまだ併用できない。Keep Activity オフでは Connected Apps（Workspace 等）を使えない。同時に有効にできる数に上限がある

### Gems

- **別名**: 個人アカウントでは skills に移行中（[Skills](#skills)）
- **概要**: 指示と Knowledge ファイルを持つカスタム版の Gemini。premade Gems もある
- **入口**: サイドバーの **Gems**
- **公式ページ**: [About the transition from Gems to skills](https://support.google.com/gemini/answer/18560919?hl=en)（最初に読む）、[Use Gems in Gemini Apps](https://support.google.com/gemini/answer/15146780?hl=en)、[Get started with Gems](https://support.google.com/gemini/answer/15236321?hl=en)、[Tips for creating custom Gems](https://support.google.com/gemini/answer/15235603?hl=en)、[Share a Gem](#share-a-gem)
- **プラン・提供範囲**: 移行の日程（18560919）: 個人アカウント（18 歳以上）は **2026-11-17 に読み取り専用**（使う・編集する・新規作成するのは不可）、**2026-12-17 に削除**。18 歳未満の個人アカウントは後日。Workspace の business・enterprise・nonprofit は 2027-03、education は 2027-06
- **注意**: 削除時に skills へ自動で作り直される（手動で先に作り直す手順も 18560919）。個人アカウントで「Gem を作りたい・共有したい」と聞かれたら、2026-11-17 以降は作れないことと skills を案内する。仕事・学校アカウントは 2027 年の移行日まで Gems を使える。15146780 等の Gems 記事は移行前の内容のまま残っている

## 外部連携

### Connected Apps

- **別名**: 旧称 Extensions（拡張機能）
- **概要**: Gmail・Calendar・Drive などの Google アプリや他社アプリ（Spotify・Instacart・OpenTable 等）に接続し、情報取得や操作をさせる
- **入口**: Connected Apps settings（https://gemini.google.com/apps 。本文では上部の **Connectors**）。チャットで `@`＋アプリ名で指定
- **公式ページ**: [Use & manage Connected Apps in Gemini](https://support.google.com/gemini/answer/13695044?hl=en&co=GENIE.Platform%3DDesktop)、提供条件の表 [Check the availability & requirements of Connected Apps](https://support.google.com/gemini/table/17434654?hl=en)（本文未確認）、[Connect the Google Workspace app](https://support.google.com/gemini/answer/15229592?hl=en)（本文未確認）
- **プラン・提供範囲**: サインイン必須。Keep Activity オフだと WEB では Connected Apps 全体が使えない。アプリごとに地域・言語・端末で異なる（多くは米国の英語。2026-10-13 のリリースノート）。根拠: 13695044・17434654
- **注意**: 仕事・学校アカウントは別記事 [Use apps connected to Gemini with a work or school Google Account](https://support.google.com/gemini/answer/14959807?hl=en)（本文未確認）。Android 専用のアプリは WEB の設定画面に出ない

### Custom apps (MCP)

- **概要**: リモート MCP サーバーの URL を登録して、自作・他社のアプリを Connected Apps に追加する
- **入口**: Connected Apps settings で MCP サーバー URL を入力（Dynamic Client Registration 非対応なら "Advanced features" の **Show more** で認証情報）。"Custom apps" の下で解除・削除
- **公式ページ**: [Connect & manage custom apps for Gemini Apps](https://support.google.com/gemini/answer/17209137?hl=en&co=GENIE.Platform%3DDesktop)
- **プラン・提供範囲**: **18 歳以上かつ米国**・**個人アカウント**（仕事・学校は不可）・Keep Activity オン・英語のみ。追加は WEB からだけ（追加後はモバイルでも使える）。根拠: 17209137
- **注意**: 日本在住なら現時点で使えない（地域拡大はリリースノート 2026-11-17 分まで見当たらない。2026-11-18 確認）。開発者向けの Connected Apps Platform・Gemini Developer Mode は別文書。Gemini Enterprise・Gemini Spark の MCP 情報を混ぜない。書き込み操作は手動確認が必要と本文にある

## メモリ・パーソナライズ

### Memory

- **別名**: 日本語 UI メモリー／旧称 Past chats（過去のチャット。2026-03-26 のリリースノートで改名）
- **概要**: 過去のチャットから学んで回答を個人化する。米国の有料プランでは memory summary（覚えている内容の一覧・編集・変更履歴）もある。他の AI アプリのメモリー・チャット履歴を取り込む切り替えツールもある
- **入口**: 設定の Memory のオン・オフ（本文の手順は省略形。UI の場所は要確認）。「What do you know about me?」で memory summary を表示
- **公式ページ**: [Get personalization with memory of your past Gemini chats](https://support.google.com/gemini/answer/16598469?hl=en&co=GENIE.Platform%3DDesktop)、[View & manage your memory summary](https://support.google.com/gemini/answer/18617127?hl=en&co=GENIE.Platform%3DDesktop)、[Import from other AI platforms](https://support.google.com/gemini/answer/16868299?hl=en)（本文未確認）、まとめ [Get personalization in Gemini Apps](https://support.google.com/gemini/answer/16598623?hl=en)
- **プラン・提供範囲**: 18 歳以上・個人アカウント（仕事・学校・保護者管理のアカウントは不可）・Keep Activity オン。memory summary は米国・Google AI プラン加入者・英語のみ。根拠: 16598469・18617127
- **注意**: Gems・Live チャットでは使われない。忘れさせるには該当チャットを Gemini Apps Activity から削除する（接続アプリ由来なら接続の解除も）

### Personal Intelligence

- **概要**: Gmail・Photos・検索履歴・YouTube 等の Google アプリを接続して個人化する
- **入口**: 対象者に出るカード → **Get started** → 接続するアプリを選ぶ（**Connect all** も可）。後から Connected Apps settings で変更
- **公式ページ**: [Connect your Google apps to personalize your Gemini experience](https://support.google.com/gemini/answer/16598406?hl=en&co=GENIE.Platform%3DDesktop)、[About personalization with Connected Apps](https://support.google.com/gemini/answer/16836988?hl=en)（本文未確認）
- **プラン・提供範囲**: 18 歳以上・個人アカウント・Keep Activity オン。EEA・ナイジェリア・スイス・英国は不可。段階展開中。根拠: 16598406
- **注意**: アプリごとに Web & App Activity・YouTube History・Smart features 等の追加条件がある。Gems では使えない。Tasks のスケジュールはこれへのオプトインが条件

### Instructions for Gemini

- **概要**: すべてのチャットに適用する指示と、「覚えて」と頼んだ事実の保存・修正
- **入口**: 指示の追加は **Add +** → 入力 → **Submit**（画面の場所は本文で省略。要確認）。チャットで「Remember that …」
- **公式ページ**: [Manage what Gemini remembers about you and customize responses](https://support.google.com/gemini/answer/16598625?hl=en&co=GENIE.Platform%3DDesktop)、[Customize your Gemini chats experience](https://support.google.com/gemini/answer/18736938?hl=en)（本文未確認）
- **プラン・提供範囲**: 指示の追加は全員。事実を覚えさせる機能は 18 歳以上・Google AI プラン・個人アカウント・Memory オン・米国のみで段階展開中。根拠: 16598625
- **注意**: 保存した項目と指示には保持期限がある（本文参照）。2026-10-13 のリリースノートで、回答の仕方とアプリ・スキルの設定が左メニューの［カスタマイズ］にまとまった

## 調査

### Deep Research

- **概要**: 調査計画を立てて多数のソースを読み、レポートを作る。ソースに Gmail・Drive、アップロードしたファイル、NotebookLM のノートブックを加えられる
- **入口**: **Sources** でソースを選ぶ → 計画を確認（**Edit plan**）→ **Start research** → **Open**。完成したレポートから Audio Overview や Canvas での可視化（**Create**）
- **公式ページ**: [Use Deep Research in Gemini Apps](https://support.google.com/gemini/answer/15719111?hl=en&co=GENIE.Platform%3DDesktop)。概要 https://gemini.google/overview/deep-research/
- **プラン・提供範囲**: 18 歳以上・サインイン。全員が使えるが、日次の件数・同時実行数に上限があり、Pro・Ultra は上限が高く Pro モデルを選べる。図表・シミュレーター入りのレポートは Ultra のみ。根拠: 15719111・16275805
- **注意**: Gmail・Drive をソースにするには Google Workspace アプリの接続が必要。過去のレポートを探すには Keep Activity オン。skills とは併用できない

## 作成物

### Canvas

- **概要**: ドキュメント・アプリ・スライド・コードを作って編集する作業領域。作ったものから Audio Overview・クイズ・スライド等を作れる
- **入口**: 右の Canvas パネル。コードは **Code**、派生物は **Create**
- **公式ページ**: [Create docs, apps & more with Canvas](https://support.google.com/gemini/answer/16047321?hl=en&co=GENIE.Platform%3DDesktop)、[Canvas safety & security](https://support.google.com/gemini/answer/16419134?hl=en)（本文未確認）。概要 https://gemini.google/overview/canvas/
- **プラン・提供範囲**: サインイン必須。アプリへの AI 機能の追加と、ドキュメントからの派生物の作成は 18 歳以上。根拠: 16047321
- **注意**: アプリを公開リンクで共有すると、リンクを知る人がアプリのデータを閲覧・編集できる。skills とは併用できない

### Images (Nano Banana)

- **概要**: 画像の生成・編集（モデル名 Nano Banana）
- **公式ページ**: [Generate & edit images with Gemini Apps](https://support.google.com/gemini/answer/14286560?hl=en)、[Manage watermark settings](https://support.google.com/gemini/answer/17405358?hl=en)、[Verify AI-generated images, videos, and audio](https://support.google.com/gemini/answer/16722517?hl=en)
- **プラン・提供範囲**: 上限は 16275805（個人）・14620100（Workspace）
- **注意**: 本文未確認。UI のツール名は未確認

### Create video

- **概要**: 動画の生成。2026-05-19 のリリースノートで Gemini Omni（テキスト・写真・動画から生成・編集、自分のアバター）が加わった
- **入口**: ツール名 "Create video"（17094296 の併用不可ツール一覧での表記）
- **公式ページ**: [Generate videos with Gemini Apps](https://support.google.com/gemini/answer/16126339?hl=en)、[Create and use an avatar](https://support.google.com/gemini/answer/16984474?hl=en)。概要 https://gemini.google/overview/video-generation/
- **プラン・提供範囲**: リリースノートでは Gemini Omni は Google AI 加入者（18 歳以上）向けで地域差あり。詳細は 16275805
- **注意**: 本文未確認

### Create music

- **概要**: 音楽の生成
- **入口**: ツール名 "Create music"（17094296 の表記）
- **公式ページ**: [Generate music with Gemini Apps](https://support.google.com/gemini/answer/16901237?hl=en)
- **注意**: 本文未確認

### Storybook

- **概要**: 挿絵入りの絵本を作る
- **公式ページ**: [Create an illustrated storybook in Gemini Apps](https://support.google.com/gemini/answer/16434396?hl=en)
- **注意**: 本文未確認

## エージェント・自動化

### Tasks

- **別名**: Tasks in Gemini
- **概要**: バックグラウンドで複数ステップの作業をさせる。Connected Apps・skills・ログイン済みサイト・Personal Intelligence 等を使い、ブラウザ操作（ローカルの Chrome またはクラウドの remote browser）もする。結果はファイル（PDF・スライド等）にもできる
- **入口**: テキストボックスの下の **Task**。タスクスレッドで進行・確認
- **公式ページ**: [Manage your tasks & workflows in Gemini Apps](https://support.google.com/gemini/answer/17094507?hl=en&co=GENIE.Platform%3DDesktop)、[Find & manage your tasks](https://support.google.com/gemini/answer/17094196?hl=en)（本文未確認）、[Manage browser & app permissions for tasks](https://support.google.com/gemini/answer/18766567?hl=en)（本文未確認）
- **プラン・提供範囲**: 記事本文（tav 経由で取得）は 18 歳以上・個人アカウント・**Google AI Pro または Ultra**・Keep Activity オン、EEA・ナイジェリア・スイス・英国を除く、とする。一方 2026-11-17 のリリースノートは「米国・インド・カナダ・オーストラリア・日本・韓国で無料で展開」とする。根拠: 17094507・リリースノート
- **注意**: **公式どうしの食い違い（要確認）**。記事が未更新か取得した版が古い可能性がある。回答では両方を示し、`page` で記事を取り直すか実画面で確かめるよう促す。メール（gemini@google.com）・テキストメッセージ・Google Pay 決済・電話の代行は 2026-11-17 時点で米国・英語・個人アカウント（18 歳以上）のみ（記事 18745518・18941404・18891937・18336420 は本文未確認）

### Schedules

- **概要**: 2 種類ある。(1) タスクのスケジュール: 時刻・Gmail の受信・トピック監視をきっかけにタスクを実行する。(2) チャットのスケジュール: 決めた時刻に回答を用意する（日次ダイジェスト等）
- **入口**: (1) **Task** で会話的に作る、または Scheduled ページで時刻ベースだけ手動作成。(2) プロンプトに時刻と頻度を書く。完了はサイドバーの未読と Scheduled ページで分かる
- **公式ページ**: (1) [Create & manage schedules for tasks in Gemini](https://support.google.com/gemini/answer/17094710?hl=en&co=GENIE.Platform%3DDesktop)、(2) [Schedules in Gemini Apps](https://support.google.com/gemini/answer/16316416?hl=en&co=GENIE.Platform%3DDesktop)
- **プラン・提供範囲**: (1) は Tasks と同じ条件＋Personal Intelligence へのオプトイン（記事本文）。(2) は個人アカウントまたは対象 Workspace エディションの仕事・学校アカウント、Keep Activity オン、段階展開中。根拠: 17094710・16316416
- **注意**: どちらのスケジュールかを先に確かめる。(1) の条件は [Tasks](#tasks) と同じ食い違いがある

### Auto browse (Gemini in Chrome)

- **概要**: Chrome のサイドパネルの Gemini に、複数ステップのウェブ操作（比較・予約・カート追加等）をさせる。gemini.google.com の WEB 版ではなく Chrome の機能
- **入口**: Chrome で Gemini in Chrome を開いて依頼 → 計画を確認 → **Start Task**。**Take over task**／**Resume**（**Give back task**）
- **公式ページ**: [Ask Gemini in Chrome to complete tasks for you with auto browse](https://support.google.com/gemini/answer/16821166?hl=en&co=GENIE.Platform%3DDesktop)、[Use Gemini in Chrome](https://support.google.com/gemini/answer/16283624?hl=en)（本文未確認）、[Gemini in Chrome availability](https://support.google.com/gemini/answer/17140089?hl=en)（本文未確認）
- **プラン・提供範囲**: 18 歳以上・米国・端末の言語が英語・個人アカウントで Google AI Plus／Pro／Ultra。仕事用アカウントは管理者の許可が必要、学校アカウントとシークレットモードは不可。段階展開中。根拠: 16821166
- **注意**: Tasks のブラウザ操作でもローカルの Chrome auto browse が使われる（17094507）

### Gemini Spark

- **概要**: 代わりに作業を進める常駐の個人エージェント（リリースノートの説明）。アプリメニューの Spark タブ
- **公式ページ**: リリースノート 2026-05-19（https://gemini.google/release-notes/ ）。ヘルプ記事は 2026-11-18 の記事一覧に無い
- **プラン・提供範囲**: リリースノート時点で trusted testers と、米国の Google AI Ultra（18 歳以上）向けベータ
- **注意**: Spark の条件を Tasks や custom apps の質問に流用しない

## 音声

### Gemini Live

- **概要**: リアルタイムの音声会話（カメラ・画面共有を含む）。2026-05-19 のリリースノートでチャットに統合され、音声と文字入力を切り替えられるようになった（Android・iOS）
- **公式ページ**: [Talk naturally with Gemini Live - Android](https://support.google.com/gemini/answer/15274899?hl=en)（モバイル）、[Go Live with Gemini in Chrome](https://support.google.com/gemini/answer/16363185?hl=en)（デスクトップの Chrome）。概要 https://gemini.google/overview/gemini-live/
- **注意**: 本文未確認。gemini.google.com の WEB 版で Live が使えるかは確認できていない。デスクトップでは Gemini in Chrome の Live の記事を見る

### Audio Overviews

- **概要**: ファイル・Deep Research レポート・Canvas の内容から、2 人のホストが話すポッドキャスト風の音声を作る
- **公式ページ**: [Generate Audio Overviews in Gemini Apps](https://support.google.com/gemini/answer/16047373?hl=en)
- **プラン・提供範囲**: 上限は 16275805（個人）・14620100（Workspace）
- **注意**: 本文未確認。Gemini Notebook（旧 NotebookLM と思われる）の同名機能とは別ヘルプ

## 共有・チーム管理

### Share a chat

- **概要**: チャット全体の公開リンク（`g.co/gemini/share`）を作る。受け取った人は読める・再共有できる・自分で続きを話せる
- **入口**: チャットの共有から公開リンクを作成。リンクの一覧と一括削除は https://gemini.google.com/sharing （**Delete all links**）。受け手は **Continue this chat**
- **公式ページ**: [Share your chats from Gemini Apps](https://support.google.com/gemini/answer/13743730?hl=en&co=GENIE.Platform%3DDesktop)、書き出しは [Export responses from Gemini Apps](https://support.google.com/gemini/answer/14184041?hl=en)（本文未確認）
- **プラン・提供範囲**: サインイン必須。続きを話す機能は 18 歳未満不可。Google AI 加入者が作ったチャットは加入者だけが続けられる。根拠: 13743730
- **注意**: リンクを知る人は誰でも読める。アップロードした画像もダウンロードできる。Gem を使ったチャットは指示を含めるか選べ、受け手は続きを話せない

### Share a Gem

- **概要**: Gem を特定の人（Viewer／Editor、期限付き可）やリンクで共有する。Gem は Drive のフォルダに保存される
- **入口**: **Gems** → 共有。一般アクセスは Public／Anyone with the link／Your organization／Private
- **公式ページ**: [Share a Gem from Gemini Apps](https://support.google.com/gemini/answer/16504957?hl=en&co=GENIE.Platform%3DDesktop)
- **プラン・提供範囲**: サインイン必須。仕事・学校アカウントは組織の Drive 共有設定に従い、Public／リンク共有が出ないことがある。根拠: 16504957
- **注意**: 個人アカウントでは 2026-11-17 に Gems が読み取り専用、12-17 に削除（[Gems](#gems)）。skills の共有は未提供で、18560919 の FAQ が「数週間のうちに（in the coming weeks）共有・Drive ファイル・notebooks を追加する」とする（2026-11-18 時点）。移行した Gem の共有権限は skill に引き継がれ、共有を受けた側は Skills ページの "All" に無効の状態で出て、受け入れの通知が来る。それまでの代替は skill の Download（.zip）と Upload だが、公式が共有手段として案内しているわけではない。NotebookLM のノートブックは共有 Gem のソースにできない

### Work and school accounts

- **概要**: Workspace ライセンスで gemini.google.com を使う場合。使える機能・上限・データの扱いはエディションで決まる
- **公式ページ**: [Use Gemini Apps with a work or school Google Account - Business / Enterprise](https://support.google.com/gemini/answer/14620100?hl=en)（学校向けは本文のリンク `co=DASHER._Family=Education`）、[Use apps connected to Gemini with a work or school Google Account](https://support.google.com/gemini/answer/14959807?hl=en)（本文未確認）
- **プラン・提供範囲**: 18 歳以上。エディション別の表が 14620100 にある。根拠: 14620100
- **注意**: custom apps・Memory・Personal Intelligence・Tasks・skills は 2026-11-18 時点で個人アカウントのみ（各記事）。個人向け上限（16275805）と混ぜない

## プランと上限

### Plans and limits

- **概要**: 無料と、Google AI Plus・Google AI Pro・Google AI Ultra の有料プラン。モデル別のプロンプト数・コンテキスト長・機能ごとの上限
- **公式ページ**: [Gemini Apps limits & feature availability](https://support.google.com/gemini/answer/16275805?hl=en)（本文未確認）、[Manage your Google AI plan from Gemini Apps](https://support.google.com/gemini/answer/14517446?hl=en)（本文未確認）、[Get Started with Gemini Go](https://support.google.com/gemini/answer/17079170?hl=en)（本文未確認。どのような提供形態かは未確認）、料金 https://gemini.google/subscriptions/
- **注意**: 16275805 は `tav extract` で旧モデル名の古い版が返った前例がある。`page` かブラウザで取る。Ultra は複数の価格帯がある（2026-05-19 のリリースノート）。学生向けの無料提供はリリースノート参照（2026-08-19）

### Models

- **概要**: モデルピッカーで選ぶ（Fast・Thinking・Pro 等。2026-10-13 に Pro・Ultra 向けの Gemini 4 Argon、Ultra 向けの Deep Think モード）
- **公式ページ**: [About Gemini models](https://support.google.com/gemini/answer/18648722?hl=en)（本文未確認）、リリースノート
- **注意**: モデル名は数か月で変わる。記憶で答えず、18648722 とリリースノートの先頭を見る

## 廃止・終了した機能

### Gems from Google Labs and Opal

- **概要**: Google Labs のミニアプリ・ワークフロー作成（Gems from Google Labs）と Opal
- **公式ページ**: [Create & manage AI mini-apps or custom workflows as Gems from Google Labs](https://support.google.com/gemini/answer/16802014?hl=en)（本文未確認）、[About the transition from Gems to skills](https://support.google.com/gemini/answer/18560919?hl=en)
- **注意**: 18560919 によると、Gems の移行と同じ 2026 年 11 月に終了する（Opal の FAQ は developers.google.com/opal/faq）

### Extensions

- **概要**: Connected Apps の旧称（拡張機能、Bard 拡張機能）。リリースノートの古い項目に残る
- **注意**: 現在の名前は [Connected Apps](#connected-apps)

### Gemini Advanced

- **概要**: 旧有料プラン名。Google AI Pro に改名（リリースノート）
- **注意**: 同様に「過去のチャット」は Memory に改名（[Memory](#memory)）、Gems は skills に移行中（[Gems](#gems)）
