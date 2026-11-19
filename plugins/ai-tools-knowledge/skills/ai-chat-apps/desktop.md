# デスクトップアプリ機能マップ（ChatGPT・Gemini・Claude）

最終確認日: 2026-11-18 ／ 対象: 3 アプリの Windows・macOS（・Linux）向けデスクトップアプリの、**WEB 版との差分だけ**

WEB 版と同じ機能は各機能マップ（[chatgpt.md](chatgpt.md)・[gemini.md](gemini.md)・[claude-ai.md](claude-ai.md)）を見る。ここに書くのは、デスクトップにしか無い機能・入手と動作環境・WEB 版と挙動が違う点・管理者による配布。上限・料金の具体値は書かない（取り方は [SKILL.md](SKILL.md)）。OS の要件は記事どうしで食い違うことがあるので、回答では記事の本文で確かめる。

## 目次

- [提供 OS と入手方法](#提供-os-と入手方法)
- [ChatGPT デスクトップ](#chatgpt-デスクトップ) — New desktop app / ChatGPT Classic / Chat Bar / Appshots / Work with Apps / Screenshots / Built-in browser (ChatGPT) / Site tools / Computer use (ChatGPT) / Local work sync / Desktop-only plugins / Computer History / Voice in Desktop / ChatGPT desktop deployment
- [Gemini デスクトップ](#gemini-デスクトップ) — Gemini for Mac / Gemini for Windows / Global shortcut (Gemini) / Share window / Speak to Window / Task on Mac / Remote control of Mac / Antigravity in the Gemini app
- [Claude Desktop](#claude-desktop) — Install and release channel / Quick entry / Deep links / Desktop extensions (Desktop) / Cowork on Desktop / Computer use (Claude) / Built-in browser (Claude) / Dispatch / Code tab / Claude Desktop deployment / Claude Desktop on a cloud provider
- [モバイルアプリ](#モバイルアプリ)

## 提供 OS と入手方法

| アプリ  | Windows                                             | macOS                                            | Linux                                                          | 公式ページ                                                                                                                                                                                                                                                                           |
| ------- | --------------------------------------------------- | ------------------------------------------------ | -------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| ChatGPT | あり（Microsoft Store。x64・arm64）                 | あり（Apple silicon・Intel）                     | public preview（2026-08-14〜。リリースノートのみ）             | [chatgpt.com/download](https://chatgpt.com/download)、[Downloading the ChatGPT macOS app](https://help.openai.com/en/articles/9275200-downloading-the-chatgpt-macos-app)、[Using the ChatGPT Windows app](https://help.openai.com/en/articles/9982051-using-the-chatgpt-windows-app) |
| Gemini  | あり（2026-09-10〜。`GeminiSetup.exe`。x64・ARM64） | あり（2026-04-15〜。Apple silicon のみ。`.dmg`） | なし                                                           | [gemini.google/desktop](https://gemini.google/us/desktop/?hl=en)、[Use the Gemini app on Mac](https://support.google.com/gemini/answer/17011627?hl=en)、[Use the Gemini app for Windows](https://support.google.com/gemini/answer/18263854?hl=en)                                    |
| Claude  | あり（MSIX。x64・arm64）                            | あり（Universal。`.pkg`）                        | beta（apt リポジトリ推奨。computer use・dictation は使えない） | [claude.com/download](https://claude.com/download)、[Install Claude Desktop](https://support.claude.com/en/articles/10065433-install-claude-desktop)                                                                                                                                 |

- 3 つとも無料プランで入れられる。デスクトップ固有の機能の多くはプラン・OS で絞られる（各節）
- **ネイティブ機能の OS 差が大きい。** Gemini の Windows 版は WEB 版とほぼ同じ「専用ウィンドウ」で、画面共有・Speak to Window・Task のローカルファイル操作は Mac だけ（「順次 Windows にも」と製品ページ）。ChatGPT の Work with Apps・Record・Meetings・Computer History も macOS だけ。Claude の Quick entry は記事上 macOS のみ
- 同じアカウントなら履歴は WEB 版と同期する。例外: ChatGPT のローカルの Work 会話と Codex の履歴、Claude の Team・Enterprise のローカル Cowork セッションと [cloud provider 版](#claude-desktop-on-a-cloud-provider) は端末に残る

## ChatGPT デスクトップ

情報源: **新アプリの正は ChatGPT Learn（`https://learn.chatgpt.com/docs/`）**。OpenAI 公式のドキュメントサイトで、デスクトップアプリ・Work・Codex・plugins・企業向け配布を扱う。索引は `https://learn.chatgpt.com/llms.txt`（リダイレクトする）、各ページは URL に `.md` を付けると Markdown 版が取れる。どちらも `curl -sL` で取る（`page` は text/markdown で失敗する）。ヘルプセンターの索引（`webref_cli.py search`）には載らない。ヘルプの記事に加え、[ChatGPT release notes](https://help.openai.com/en/articles/6825453-chatgpt-release-notes) をデスクトップ・macOS・Windows で grep する。旧アプリ向けの [macOS app release notes](https://help.openai.com/en/articles/9703738-chatgpt-macos-app-release-notes)・[Windows app release notes](https://help.openai.com/en/articles/10003026-windows-app-release-notes) もある。**macOS・Windows の個別記事の多くは旧アプリ（Classic）時代の内容のまま**で、新アプリでの動作は書かれていない。回答では、記事が旧アプリの話かもしれないと添える。

### New desktop app

- **概要**: 2026-07-09 に作り直したアプリ。Chat・Work・Codex を 1 つにまとめた。Work は許可を得てローカルファイル・デスクトップアプリを使う。クラウドで動く Work の会話は web・モバイルと同期し、ローカルの会話は手元にだけ残る。Codex は web では選べない（モバイルの **Remote** タブから見られる）
- **入口**: メニューで ChatGPT か Codex を選び、ChatGPT では入力欄の上の Chat / Work のトグル。短い質問は New chat の右の Quick chat アイコン
- **公式ページ**: [ChatGPT desktop app](https://learn.chatgpt.com/docs/app)、[for Windows](https://learn.chatgpt.com/docs/windows/windows-app)（Store・`winget`、Windows sandbox・WSL2）、[for Linux](https://learn.chatgpt.com/docs/linux/linux-app)（preview。対応ディストリビューションとパッケージ）、[Moving to the new ChatGPT desktop app](https://help.openai.com/en/articles/20001276-moving-to-the-new-chatgpt-desktop-app)、リリースノート（2026-07-09・07-16）
- **プラン・提供範囲**: macOS・Windows の全プラン（2026-07-16）。Work は Plus・Pro・Business・Enterprise。根拠: 20001276・6825453・chatgpt.com/download
- **注意**: Windows の Store ID は新アプリが `9PLM9XGG6VKS`（ChatGPT Learn）、記事 9982051 に書かれた `9NT1R1C2HH7J` は旧アプリ側。9982051 は今も「有料プラン向けの early version」と書き、リリースノートの「all plans」と食い違う。Codex の中身は ChatGPT アプリの機能マップの範囲外（`codex-docs`）

### ChatGPT Classic

- **概要**: 作り直し前のデスクトップアプリの新しい名前。残して使い続けられ、モデル更新・修正・セキュリティ更新は続くが、新しいエージェント機能は来ない
- **公式ページ**: [Moving to the new ChatGPT desktop app](https://help.openai.com/en/articles/20001276-moving-to-the-new-chatgpt-desktop-app)
- **注意**: Chat Bar・Work with Apps・スクリーンショット・Record の記事は Classic の記述。macOS（旧アプリ）の Voice は 2026-01-15 に終了

### Chat Bar

- **別名**: Companion window（Windows と古いリリースノート）
- **概要**: どの画面からでも呼べる小さな入力ウィンドウ。質問・ファイル添付・スクリーンショット・写真撮影
- **入口**: macOS は ⌥+Space かメニューバーのアイコン（変更は "ChatGPT -> Settings -> Keyboard Shortcut"）。Windows は Alt + Space（アプリ起動中のみ。変更は "Settings > App > Companion window hotkey"）
- **公式ページ**: [How to launch the Chat Bar](https://help.openai.com/en/articles/9295241-how-to-launch-the-chat-bar)、[Using the ChatGPT Windows app](https://help.openai.com/en/articles/9982051-using-the-chatgpt-windows-app)
- **プラン・提供範囲**: macOS・Windows。プランの記載なし。根拠: 9295241・9982051
- **注意**: ヘルプの記事は Classic の記述。ChatGPT Learn には Chat Bar・Alt + Space の記述が無く（2026-11-18、llms.txt と app・windows-app のページで確認）、新アプリでは画面を渡すのは下の Appshots、短い質問は Quick chat。新アプリで Chat Bar が残っているかは未確認と明示する

### Appshots

- **概要**: 最前面のウィンドウを今のチャットか新しいチャットに送る。ウィンドウの画像と、アプリが出しているテキスト（見えていないスクロール範囲を含むことがある）が入る。添付と同じ扱い
- **入口**: macOS は両方の Command キー、Windows は両方の Alt キー（設定でカスタムのキーにできる）。送り先は設定の **Appshot destination**（Automatic / Current chat / New chat）
- **公式ページ**: [Appshots](https://learn.chatgpt.com/docs/appshots)
- **プラン・提供範囲**: macOS・Windows のデスクトップアプリ。プランの記載なし。組織が Appshots を許可している必要がある。根拠: learn.chatgpt.com/docs/appshots
- **注意**: macOS は Screen & System Audio Recording と Accessibility の許可が要る。Google Docs・Gmail などでは見えている画像しか渡らないことがある。Windows ではメインのアプリの画面に開く。Gemini の [Share window](#share-window)（Mac のみ）に当たる

### Work with Apps

- **概要**: IDE・ターミナル・メモアプリの内容（開いているペインの末尾か選択範囲）を読み取って会話に付ける。IDE では差分を作って直接適用もできる
- **入口**: Chat Bar の "Work with Apps"、"ChatGPT > Settings > Work with Apps > Manage Apps"。macOS の Accessibility 許可が要り、VS Code 系は拡張 `openai.chatgpt` が要る
- **公式ページ**: [Work with Apps on macOS](https://help.openai.com/en/articles/10119604-work-with-apps-on-macos)（対応アプリの一覧あり）、[How to install the Work with Apps Visual Studio Code extension](https://help.openai.com/en/articles/10128592-how-to-install-the-work-with-apps-visual-studio-code-extension)
- **プラン・提供範囲**: **macOS のみ**。Enterprise・Edu は管理者が無効にできる。根拠: 10119604
- **注意**: Classic 時代の記述。新アプリでは Work（ローカル）がアプリ操作を担う

### Screenshots

- **概要**: ウィンドウ・画面のスクリーンショット、カメラの写真を添付する
- **入口**: macOS は "Plus icon > Take Screenshot"（ショートカットあり）。Windows は Snipping Tool 経由
- **公式ページ**: [ChatGPT macOS app - Screenshot Tool](https://help.openai.com/en/articles/9295245-chatgpt-macos-app-screenshot-tool)、[File Uploads and Photos](https://help.openai.com/en/articles/9295234-chatgpt-macos-app-file-uploads-and-photos)、保持は [How is data retained in the macOS app](https://help.openai.com/en/articles/9268871-how-is-data-retained-in-the-macos-app)
- **プラン・提供範囲**: macOS・Windows。根拠: 9295245・10003026
- **注意**: 添付はクラウドに保存され、保持期間は web と同じ

### Built-in browser (ChatGPT)

- **概要**: アプリ内の Chromium ベースのブラウザ。ユーザーと ChatGPT が同じページで作業する。タブ・ダウンロード・サインイン・パスワード管理・拡張機能・Annotation mode
- **入口**: Work・Codex のチャットのツールバー、または ⌘+Shift+B（Windows は Ctrl+Shift+B）。許可サイト・Cookie・履歴はアプリの Settings
- **公式ページ**: [Using the built-in browser in the ChatGPT desktop app](https://help.openai.com/en/articles/20001277-using-the-built-in-browser-in-the-chatgpt-desktop-app)
- **プラン・提供範囲**: macOS・Windows（Linux もリリースノートで対応）。プランと workspace 設定次第。根拠: 20001277
- **注意**: Chrome のプロファイルとは別。手元の Chrome のログイン状態を使うなら ChatGPT browser extension（web からも使える）。リモートで動く cloud browser（[ChatGPT Work](chatgpt.md#chatgpt-work)）とも別物。ChatGPT Atlas（終了済み）の Cookie・パスワードはここへ移せる

### Site tools

- **概要**: 内蔵ブラウザで開いたサイトが WebMCP でツールを出していれば、ChatGPT が直接使う
- **入口**: アドレスバーの矢印。無効化は "Browser settings > Permissions > Enable site tools"
- **公式ページ**: [Using site tools in the ChatGPT desktop app](https://help.openai.com/en/articles/20001423-using-site-tools-in-the-chatgpt-desktop-app)
- **プラン・提供範囲**: デスクトップの内蔵ブラウザのみ（Chrome 拡張では不可）。根拠: 20001423

### Computer use (ChatGPT)

- **概要**: Work・Codex が許可を得てローカルファイル・デスクトップアプリを操作する
- **入口**: **Settings > Computer Use**
- **公式ページ**: [Computer Use](https://learn.chatgpt.com/docs/computer-use)（利用者向け）、[Manage browser and computer use in your Enterprise workspace](https://help.openai.com/en/articles/20001510-manage-browser-and-computer-use-in-your-enterprise-workspace)、リリースノート（2026-05-29・07-09）
- **プラン・提供範囲**: 対応地域で、macOS・Windows の Work と Codex。Linux は他アプリを操作できない。Windows は登場時 EEA・英国・スイスで使えなかった（現状は本文とリリースノートで確かめる）。根拠: learn.chatgpt.com/docs/computer-use・20001510・6825453
- **注意**: Windows はアクティブなデスクトップで前面で動き、同じセッションで他の作業をしながらバックグラウンドでは動かせない。macOS はバックグラウンドで動かせる

### Local work sync

- **概要**: デスクトップで始めた Work のタスクを web・モバイルから続ける。ローカルの手順はパソコンがオンラインのときだけ動き、オフラインなら次のターンはクラウドで動く
- **入口**: 管理者が "Workspace settings > Permissions & roles" で Local / Cloud の Work を有効にし、Work permissions で local work sync をオン
- **公式ページ**: [Agent Security and local work sync in ChatGPT](https://help.openai.com/en/articles/20001548-agent-security-and-local-work-sync-in-chatgpt)
- **プラン・提供範囲**: Enterprise・Edu の記事。段階展開。ZDR は非対応。根拠: 20001548

### Desktop-only plugins

- **概要**: **Desktop only** の plugin と、local MCP apps を含む plugin はデスクトップアプリでしか動かない（アカウントに保存しても web・モバイルでは使えない）
- **公式ページ**: [Plugins in ChatGPT](https://help.openai.com/en/articles/20001256-plugins-in-chatgpt)。plugin 全般は [chatgpt.md の Plugins](chatgpt.md#plugins)
- **関連する Mac 専用の plugin**: Meetings（新アプリ・ベータ。[The Meetings plugin in ChatGPT](https://help.openai.com/en/articles/20001546-the-meetings-plugin-in-chatgpt)、Windows・モバイルは "coming soon"）、Apple Messages（Apple silicon の Mac。リリースノート 2026-08-20 のみ）。旧アプリの Record は [chatgpt.md の ChatGPT Record](chatgpt.md#chatgpt-record)

### Computer History

- **概要**: 選んだアプリ・サイトでの操作イベントを記録し、ChatGPT と Codex が参照する。スクリーンショット・録音は残さない。既定でオフ、Memory が前提
- **公式ページ**: リリースノート（2026-08-13・08-20）のみ。ヘルプ記事は無い（2026-11-18、索引を computer history で検索）
- **プラン・提供範囲**: macOS、Pro・Business・Enterprise（Business・Enterprise は管理者の許可が要る）。EEA・英国・スイスは Pro のみ。根拠: 6825453

### Voice in Desktop

- **概要**: 声でタスクを始め、進捗を聞き、複数のエージェントに指示する
- **公式ページ**: [ChatGPT Voice](https://help.openai.com/en/articles/20001274-chatgpt-voice)、リリースノート（2026-07-23）。Voice 全般は [chatgpt.md の ChatGPT Voice](chatgpt.md#chatgpt-voice)
- **プラン・提供範囲**: macOS・Windows。料金・上限はデスクトップ用に別建て。根拠: 20001274
- **注意**: Voice in Chat の提供先は web・iOS・Android と書かれている

### ChatGPT desktop deployment

- **概要**: Windows は Microsoft Store 版を Intune 等の MDM や `winget` で配る。内蔵ブラウザは Chrome の Enterprise ポリシーを受け付ける（デバイス単位のみ）。macOS のアプリ許可リスト用に Team ID・証明書の値が公開されている。Work・Codex の使用量は "Settings > Usage & billing"
- **公式ページ**: [Deploy the Windows app and Codex CLI](https://learn.chatgpt.com/docs/enterprise/windows-deployment)（Store・Intune のオフラインパッケージ・SCCM）、[Manage app updates](https://learn.chatgpt.com/docs/enterprise/manage-app-updates)（アプリ内の自動更新を止めて MDM で配る）、[Managing ChatGPT desktop browser policies with MDM](https://help.openai.com/en/articles/20001535-managing-chatgpt-desktop-browser-policies-with-mdm)、[How to add OpenAI apps to your macOS application allowlist](https://help.openai.com/en/articles/20001159-how-to-add-openai-apps-to-your-macos-application-allowlist)、[Using the ChatGPT Windows app](https://help.openai.com/en/articles/9982051-using-the-chatgpt-windows-app)、[Reviewing Work and Codex usage…](https://help.openai.com/en/articles/20001478-reviewing-work-and-codex-usage-and-using-personal-analytics-in-chatgpt-desktop)
- **プラン・提供範囲**: Enterprise・Edu。根拠: 上記
- **注意**: ポリシーのパス・識別子には「Codex」の名前が残っている（本文の値をそのまま示す）

## Gemini デスクトップ

情報源: ヘルプ記事に Mac・Windows 専用のプラットフォームタブは無い。専用記事（下記）と、Computer タブ内の「On a Mac, you can also open the Gemini app」という注記に散らばっている。製品ページ [gemini.google/desktop](https://gemini.google/us/desktop/?hl=en) の FAQ と [release notes](https://gemini.google/release-notes/) も根拠になる。support.google.com の取り方・429 の扱いは SKILL.md に従う。

### Gemini for Mac

- **概要**: 2026-04-15 公開のネイティブアプリ。チャット・Workspace 連携・画像・動画生成・Deep Research など WEB 版の機能に加え、下の Mac 専用機能がある
- **入口**: gemini.google/mac の **Download for Mac**（`.dmg`）。更新は **Gemini > Check for Updates**
- **公式ページ**: [Use the Gemini app on Mac](https://support.google.com/gemini/answer/17011627?hl=en)（動作要件あり）、[The Gemini app is now on Mac](https://blog.google/innovation-and-ai/products/gemini-app/gemini-app-now-on-mac-os/)
- **プラン・提供範囲**: Gemini アプリの対応国・言語、無料。個人アカウントと、管理者が Gemini を有効にした仕事・学校アカウント。macOS 15 以上・Apple silicon。根拠: 17011627・リリースノート 2026.04.15
- **注意**: WEB 版との機能差の一覧は公式に無い。既知の差: Notebooks は Mac アプリでは一部のみ（[gemini.md](gemini.md)）。**Gemini Live がデスクトップアプリで使えるかは未確認**（Live の記事 15274899 は Desktop を指定しても Android の内容になり、「web app では使えない」と書く）

### Gemini for Windows

- **概要**: 2026-09-10 公開。ショートカットで呼べる専用ワークスペースで、中身は WEB 版とほぼ同じ。Mac のネイティブ機能は「順次」
- **入口**: gemini.google/desktop の **Download**（`GeminiSetup.exe`）。タスクバー・システムトレイのアイコン。更新は起動時の通知の **Click Restart to update**
- **公式ページ**: [Use the Gemini app for Windows](https://support.google.com/gemini/answer/18263854?hl=en)（動作要件あり）、[The Gemini app is now on Windows](https://blog.google/innovation-and-ai/products/gemini-app/gemini-app-now-on-windows/)
- **プラン・提供範囲**: Windows 10 以上、無料、アカウント条件は Mac と同じ。根拠: 18263854
- **注意**: skills の提供面について食い違いがある。リリースノート 2026.10.13 は「Windows・macOS のデスクトップアプリ、全ティア」、skills の記事 17094296 は「モバイル・Mac・web」で Windows が無い（17094296 は tav extract で取れた版で、古い可能性がある）

### Global shortcut (Gemini)

- **概要**: どのアプリの上からでも Gemini を呼ぶ
- **入口**: Mac は Option + Space（製品ページでは Option + Shift + Space で full chat も）、Windows は Alt + Space。キーの変更方法は Windows の記事 18263854 に書かれていない（2026-11-18）
- **公式ページ**: [Use the Gemini app on Mac](https://support.google.com/gemini/answer/17011627?hl=en)、[Use the Gemini app for Windows](https://support.google.com/gemini/answer/18263854?hl=en)、製品ページ
- **プラン・提供範囲**: Mac・Windows、全ユーザー。根拠: 17011627・18263854
- **注意**: ChatGPT の Windows 版も Alt + Space を使う（両方入れると衝突しうる。ChatGPT の記事は「他のアプリが同じキーを登録していると動かない」と書く）

### Share window

- **概要**: 開いているウィンドウを共有し、その内容を前提に答えさせる
- **入口**: ヘルプは "Add files and tools > Share window"。製品ページは両方の ⌘ キー（⌘ + ⌘）
- **公式ページ**: [Use the Gemini app on Mac](https://support.google.com/gemini/answer/17011627?hl=en)、製品ページ
- **プラン・提供範囲**: **Mac のみ**。macOS の Screen & System Audio Recording と Accessibility の許可が要る。根拠: 17011627
- **注意**: ⌘ + ⌘ はヘルプに無い。継続配信か 1 回のスナップショットかは公式に記載なし

### Speak to Window

- **概要**: 他のアプリの中で、音声で入力・書き換え・ファイル要約・画像生成をする。結果はカーソル位置かアクティブなウィンドウに入る。アプリ内のマイク入力とは別
- **入口**: `fn` を押したまま話す、または `fn` を 2 回タップ。設定は **Gemini > Settings > Speak to Window**
- **公式ページ**: 17011627、リリースノート 2026.07.29
- **プラン・提供範囲**: **Mac のみ**、英語、段階展開。根拠: 17011627

### Task on Mac

- **概要**: Connected folders に追加した Mac のフォルダのファイルを分析・編集・整理し、文書化・メール送信まで行う。作業中は一時バックアップを作る
- **入口**: テキストボックス下の **Task** → **Connected folders** の Add Mac folder
- **公式ページ**: [Assign tasks in the Gemini app on Mac](https://support.google.com/gemini/answer/17208717?hl=en)、リリースノート 2026.06.30・2026.11.17
- **プラン・提供範囲**: Mac、「tasks が使える地域」。2026.06.30 時点は英語・Google AI Ultra・18 歳以上。2026.11.17 に Tasks in Gemini が日本を含む 6 か国で無料展開（Mac のローカルファイル操作にも及ぶかは書かれていない）。根拠: 17208717・リリースノート
- **注意**: 「Gemini Spark」と「Tasks in Gemini」の関係（改名か）は明記されていない。タスク一般は [gemini.md の Tasks](gemini.md#tasks) を見る。クラウド同期フォルダを入れたときのデータ共有の注意が記事にある

### Remote control of Mac

- **概要**: スマホなど別の端末から、Mac 上の Gemini にタスクを頼む
- **入口**: 別の端末で **Task** → Add Computer → Mac を選ぶ
- **公式ページ**: [Assign tasks in the Gemini app on Mac](https://support.google.com/gemini/answer/17208717?hl=en)
- **プラン・提供範囲**: Mac で Gemini が起動中、handoff の規約に同意、同じアカウント、同じ Wi-Fi か Bluetooth。根拠: 17208717
- **注意**: リリースノート 2026.06.30 は web・モバイルからの操作を "Coming soon" と書いており、記事と時間差がありうる

### Antigravity in the Gemini app

- **概要**: Mac アプリから Google Antigravity（コーディングエージェント）を起動する。中身は Gemini アプリの範囲外
- **入口**: Mac の Gemini アプリ上部の Antigravity
- **公式ページ**: リリースノート 2026.10.13
- **プラン・提供範囲**: Mac のみ、英語、18 歳以上、Antigravity の対応地域。根拠: リリースノート

## Claude Desktop

情報源: ヘルプの "Claude Desktop" 節（`webref_cli.py search desktop --source claude`）と、[release notes](https://support.claude.com/en/articles/12138966-release-notes)（Desktop を含む 1 本）。設定画面は新レイアウト（`Settings > Desktop app` にまとまる）と旧レイアウト（`Settings > System`・`Settings > Extensions`・`Settings > Developer`）を併記した記事が多い。診断は `Help > Troubleshooting`。

### Install and release channel

- **概要**: 入手・動作要件・プラン別にできること（Chat は全プラン、Cowork・Code は有料）・Linux の制限。更新の系統を Stable（既定）と Latest から選べる
- **入口**: claude.ai/download。系統は `Settings > Desktop app` の **Release channel**。手動更新は `Claude > Check for Updates`（Mac）・`Help > Check for Updates`（Windows）
- **公式ページ**: [Install Claude Desktop](https://support.claude.com/en/articles/10065433-install-claude-desktop)、リリースノート（2026-11-17）
- **プラン・提供範囲**: Mac・Windows・Linux（beta）。Release channel は Linux・Microsoft Store 版・ポリシー管理下の端末・cloud provider 版では出ない。根拠: 10065433
- **注意**: Windows は管理者権限なしでも入るが、その場合 Cowork は使えない（12622703）。Linux は apt で更新する（`.deb` 直入れは自動更新されない）

### Quick entry

- **概要**: どのアプリからでも呼べる入力欄。範囲のスクリーンショットやウィンドウを添付できる。Caps Lock 等で dictation（音声入力。voice mode とは別）
- **入口**: 既定は Option の 2 回押し。`Settings > Desktop app`（旧 `Settings > System`）の **Quick access shortcut**・**Voice shortcut**
- **公式ページ**: [Use quick entry with Claude Desktop on Mac](https://support.claude.com/en/articles/12626668-use-quick-entry-with-claude-desktop-on-mac)
- **プラン・提供範囲**: 全プラン、macOS（Screen recording・Accessibility・Speech recognition の許可が要る）。根拠: 12626668
- **注意**: 対応 OS が記事で食い違う。12626668 は「macOS のみ、Windows では使えない」、10065433 とダウンロードページは Linux（X11）で Quick Entry のホットキーが動くと書く。必要な macOS の版も 12626668 とアプリ本体の要件で違う。Windows の dictation の記事は無い

### Deep links

- **概要**: `claude://` の URL で Desktop の新規チャット・既存のチャットやプロジェクト・Code・Cowork を開く
- **公式ページ**: [Open Claude Desktop with a link](https://support.claude.com/en/articles/14729294-open-claude-desktop-with-a-link)（形式の一覧あり）
- **プラン・提供範囲**: Mac・Windows・Linux。根拠: 14729294
- **注意**: リンクで渡したフォルダは毎回確認ダイアログが出る

### Desktop extensions (Desktop)

- **概要**: ローカル MCP の詳細は [claude-ai.md の Desktop extensions](claude-ai.md#desktop-extensions)。ここでは差分だけ: Node.js 同梱、機密の設定値は OS の資格情報ストア（Keychain・Credential Manager・Linux のキーチェーン）に暗号化して保存、自作は "Advanced settings" → **Extension Developer** → "Install Extension…"、接続状態は Extensions ページの **Local MCP servers**（旧 `Settings > Developer`）
- **公式ページ**: [Getting Started with Local MCP Servers on Claude Desktop](https://support.claude.com/en/articles/10949351-getting-started-with-local-mcp-servers-on-claude-desktop)、管理者の許可リストは [Enabling and using the desktop extension allowlist](https://support.claude.com/en/articles/12592343-enabling-and-using-the-desktop-extension-allowlist)、配布は [Deploying enterprise-grade MCP servers with desktop extensions](https://support.claude.com/en/articles/12702546-deploying-enterprise-grade-mcp-servers-with-desktop-extensions)
- **プラン・提供範囲**: Desktop の全ユーザー。許可リストは Team・Enterprise の Owner（"Block all desktop extensions" は Enterprise）。根拠: 10949351・12592343
- **注意**: 許可リストを有効にすると、許可されていない拡張は端末から削除される。端末のポリシーが許可リストより優先。記事どうしで表記が違う: 管理画面のパスは 12592343 が "Organization settings > Connectors"、12622667 が "Organization settings > Plugins > Connectors"。自作の拡張の入れ方も、個人の端末に入れるなら 10949351 の Extension Developer、組織に配るなら 12592343 の "Desktop" タブの "Add custom extension"（Owner）と別の手順

### Cowork on Desktop

- **概要**: Cowork 全般は [claude-ai.md の Claude Cowork](claude-ai.md#claude-cowork)。Desktop ではローカルフォルダ・ローカル connectors・ブラウザ操作・computer use が使え、web・モバイルからこれらを使うときも Desktop の起動が前提
- **公式ページ**: [Use Claude Cowork on web, desktop, and mobile](https://support.claude.com/en/articles/15520349-use-claude-cowork-on-web-desktop-and-mobile)、[Use Claude Cowork on Team and Enterprise plans](https://support.claude.com/en/articles/13455879-use-claude-cowork-on-team-and-enterprise-plans)、要件は [Install Claude Desktop](https://support.claude.com/en/articles/10065433-install-claude-desktop)、EDR は [Run your EDR sensor in Claude Cowork](https://support.claude.com/en/articles/17828685-run-your-endpoint-detection-and-response-edr-sensor-in-claude-cowork-on-claude-desktop)
- **プラン・提供範囲**: 全有料プラン。Mac・Windows（Virtual Machine Platform が要る）・Linux（beta。KVM が要る）。根拠: 10065433・15520349
- **注意**: **どこで動くかが記事で食い違う。** 10065433 は「手元の VM で動く」。15520349 は、2026-10-06 以降の Pro・Max・Ultra の新しいタスクはすべてクラウドで動き、"Only on your computer" は廃止、手元で動かすなら Desktop の Claude Code へ（"Download task data" → `/port-task-data`）と書く。Team・Enterprise は今もローカルのセッションがあり、クラウド実行は組織設定（Team は既定オン、Enterprise は既定オフ）。ローカルセッションの履歴は端末に残り、管理者がまとめて消せない

### Computer use (Claude)

- **概要**: スクリーンショットを撮り、クリック・入力でデスクトップアプリを操作する。connector → ブラウザ → 画面操作の順に手段を選ぶ。アプリごとの許可とブロックリスト
- **入口**: `Settings > Capabilities` → **Computer use**（無ければ `Settings > System`）
- **公式ページ**: [Let Claude use your computer in Cowork](https://support.claude.com/en/articles/14128542-let-claude-use-your-computer-in-cowork)
- **プラン・提供範囲**: beta。**Pro・Max・Ultra のみ**（本文に "Team and Enterprise plans don't have access to computer use at this time." とある）。Desktop の Cowork と Claude Code、Mac・Windows（Linux 不可）。根拠: 14128542・10065433
- **注意**: パソコンが起きていて Desktop が開いている必要がある

### Built-in browser (Claude)

- **概要**: Desktop に内蔵したブラウザ。Cowork のセッションをまたいでログイン状態が残る。他のブラウザから Cookie を取り込める（取り込める元は OS で違う。Safari は不可）
- **入口**: 既定のブラウザは `Settings > Cowork` → **Preferred browser**
- **公式ページ**: [Use the built-in browser in Claude Cowork](https://support.claude.com/en/articles/16607400-use-the-built-in-browser-in-claude-cowork)
- **プラン・提供範囲**: Pro・Max・Ultra。Team・Enterprise は Owner がオフにしていなければ。Mac・Windows・Linux（beta）。根拠: 16607400
- **注意**: [claude-ai.md の Cloud browser](claude-ai.md#cloud-browser) とは別物。自分の Chrome を操作させるのは [Claude in Chrome](claude-ai.md#claude-in-chrome)（Desktop からは "Customize" → "Connectors" → **Claude in Chrome**。[Get started with Claude in Chrome](https://support.claude.com/en/articles/12012173-get-started-with-claude-in-chrome)）

### Dispatch

- **概要**: スマホから送った指示を手元の Desktop で実行させる 1 本の続いたスレッド
- **入口**: Cowork の左パネル → "Dispatch" → "Get started"
- **公式ページ**: [Assign tasks from anywhere in Claude Cowork](https://support.claude.com/en/articles/13947068-assign-tasks-from-anywhere-in-claude-cowork)
- **プラン・提供範囲**: 一部の Pro・Max・Ultra の限定 beta で、新規ユーザーは使えない。根拠: 13947068
- **注意**: ダウンロードページは今も宣伝している。新しく始めるならクラウドの Cowork が代わり

### Code tab

- **概要**: Desktop の中の Claude Code。詳細は `claude-code-docs` スキル
- **プラン・提供範囲**: 有料プラン。ポリシー `isClaudeCodeForDesktopEnabled` で無効にできる。根拠: 10065433・12622667

### Claude Desktop deployment

- **概要**: Mac は `.pkg`（推奨）を Jamf・Kandji・Intune 等で、Windows はユーザー単位の MSIX を Intune・SCCM・GPO 等で配る。アプリの挙動は端末のポリシー（macOS の構成プロファイル、Windows のレジストリ）で制御し、Enterprise は一部を Organization settings からも設定できる（beta）
- **公式ページ**: [Deploy Claude Desktop for macOS](https://support.claude.com/en/articles/12611117-deploy-claude-desktop-for-macos)、[Deploy Claude Desktop for Windows](https://support.claude.com/en/articles/12622703-deploy-claude-desktop-for-windows)、[Enterprise configuration for Claude Desktop](https://support.claude.com/en/articles/12622667-enterprise-configuration-for-claude-desktop)（ポリシーのキーの一覧）
- **プラン・提供範囲**: Team・Enterprise の管理者（Organization settings からの設定は Enterprise）。根拠: 12611117・12622703・12622667
- **注意**: 端末のポリシーが Organization settings より優先。ポリシーを 1 つでも置くと Release channel が消え Stable に固定。Windows の Cowork は VDI やネストした仮想化の無い VM では動かない。macOS の記事は他より更新が古い

### Claude Desktop on a cloud provider

- **概要**: 推論を Bedrock・Vertex・Foundry や自社ゲートウェイに向ける Desktop 専用の構成。履歴・プロジェクト・メモリは端末に保存。claude.ai の web 版もモバイル版も無く、共有もできない
- **公式ページ**: [Move from Claude Enterprise to Claude Desktop on a cloud provider](https://support.claude.com/en/articles/18426225-move-from-claude-enterprise-to-claude-desktop-on-a-cloud-provider)。詳細手順は claude.com/docs/third-party/claude-desktop/
- **プラン・提供範囲**: Enterprise からの移行向け。Mac・Windows・Linux（beta）。根拠: 18426225

## モバイルアプリ

機能マップは作っていない。WEB 版の各節の「プラン・提供範囲」にモバイルの可否が書いてあればそれを使い、無ければ次の情報源から探す。

- ChatGPT: 専用の記事は少ない（[ChatGPT iOS and Android app FAQ](https://help.openai.com/en/articles/8142208-chatgpt-ios-and-android-app-faq) ほか数本）。モバイルの差分は主にリリースノートと各機能の記事の中
- Gemini: 記事のプラットフォームタブで分かれる。`co=GENIE.Platform%3DAndroid`・`%3DiOS` を付けて取る
- Claude: ヘルプに "Claude Mobile apps" 節がある（`webref_cli.py search mobile --source claude`）
