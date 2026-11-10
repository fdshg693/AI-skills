# Dynamic Workflows 詳細リファレンス

[SKILL.md](SKILL.md)のベストプラクティスから参照される詳細資料。公式ドキュメント([code.claude.com/docs/en/workflows](https://code.claude.com/docs/en/workflows))の内容に基づく。最新版との差異が疑われる場合は**claude-code-docsスキル**で再確認すること。

## 他機構との比較

「誰が次に何を実行するかを決めるか」が機構ごとに異なる。

|                          | Subagent                | Skill                  | Agent teams                  | Workflow                       |
| :----------------------- | :---------------------- | :--------------------- | :--------------------------- | :----------------------------- |
| 実体                     | Claudeが起動するworker  | Claudeが従う手順書     | 複数セッションを束ねるリード | ランタイムが実行するスクリプト |
| 次に何をするか決めるのは | Claude(ターンごと)      | Claude(手順書に従って) | リードagent(ターンごと)      | スクリプト自身                 |
| 中間結果の置き場所       | Claudeのcontext window  | Claudeのcontext window | 共有タスクリスト             | スクリプト変数                 |
| 再現可能なもの           | worker定義              | 手順書                 | チーム定義                   | オーケストレーションそのもの   |
| 規模の目安               | 1ターンで数件のdelegate | subagentと同程度       | 数体の長時間稼働peer         | 1runで数十〜数百体             |
| 中断時の挙動             | ターンがrestart         | ターンがrestart        | teammateは動き続ける         | 同一セッション内でresume可能   |

Workflowは「計画」そのものをコードに移す機構。分岐・ループ・中間結果の保持をスクリプトが持つため、Claudeのcontextには最終結果だけが残る。これにより「独立したagent同士に相互検証させる」「複数角度から草案を作って比較する」といった、精度を上げる定型パターンを毎回同じ形で繰り返せる。

## 起動方法

- **バンドル済み**: `/deep-research <question>` — 複数の切り口でWeb検索をfan-outし、出典を相互照合してから引用付きレポートを返す。`WebSearch`ツールが使える環境が前提。
- **プロンプトで依頼**: 自分の言葉で「ワークフローを使って」「run a workflow」と頼む、またはプロンプトに`ultracode`というキーワードを含める。キーワードはこのプロンプトの構造化の仕方だけを選ぶもので、実行中のagentのツール呼び出しは通常通りセッションの[permission mode](https://code.claude.com/docs/en/permission-modes)・sandboxingに従う。
  - キーワードが効くのは自分でタイプしたプロンプト(対話プロンプト・IDE拡張パネル・Remote Controlクライアント・人間入力としてスタンプされたAgent SDK入力)のみ。`-p`で渡したプロンプト、Agent SDKが人間入力としてスタンプしていない入力、スケジュールされたタスク、webhook/PRコメント経由の入力では起動しない。
  - 誤起動した場合はmacOSで`Option+W`、Windows/Linuxで`Alt+W`でハイライトを解除できる。`/config`でキーワード自体を無効化することも可能。
- **セッション全体で有効化**: `/effort ultracode`(`xhigh`相当の推論努力+自動ワークフロー化を組み合わせた設定)。`claude --effort ultracode`で起動時から有効化もできる。オンの間はタスクごとに複数回workflowが走ることがあり、通常より時間・トークンを消費する。ルーティン作業に戻る際は`/effort high`に落とす。

## 承認フロー

CLIでは実行前に計画されたフェーズと選択肢(`Yes, run it` / `Yes, and don't ask again for <name> in <path>` / `View raw script` / `No`)が表示される。`Ctrl+G`でスクリプトをエディタで開ける。

| Permission mode                            | プロンプトされるタイミング                                                         |
| :----------------------------------------- | :--------------------------------------------------------------------------------- |
| Default, accept edits                      | 毎回(そのworkflow・そのプロジェクトで`Yes, and don't ask again`を選んでいない限り) |
| Auto                                       | 初回起動時のみ。以降は確認なし(ultracode有効時は完全にスキップ)                    |
| Bypass permissions, `claude -p`, Agent SDK | プロンプトなし。即実行                                                             |

workflowが起動するsubagent自体は、セッションのpermission modeに関わらず常に`acceptEdits`モードで動き、セッションのtool allowlistを引き継ぐ(ファイル編集は自動承認)。allowlistに無いshellコマンド・web fetch・MCPツールはrun中にプロンプトされうるので、長時間runの前に必要なコマンドをallowlistへ追加しておくとよい。

## 保存場所

`/workflows`で該当runを選び保存すると、次の2箇所から選べる。

- `.claude/workflows/`(プロジェクト): リポジトリをcloneした全員と共有
- `~/.claude/workflows/`(ホーム): 自分の全プロジェクトで使えるが自分専用。`CLAUDE_CONFIG_DIR`を設定している場合はそのディレクトリ配下の`workflows/`

保存すると以後`/<name>`として呼び出せる。モノレポで`.claude/`が複数階層にある場合、プロジェクト側の保存は作業ディレクトリからリポジトリルートまでの間で最も近い既存の`.claude/workflows/`に書き込まれる(無ければリポジトリルート)。読み込みもその経路上の全`.claude/workflows/`から行われ、同名が複数あれば作業ディレクトリに最も近いものが使われる。プロジェクト側とホーム側で同名がある場合は常にプロジェクト側が優先される。

> **調査時点(2026-07-19)の情報**: workflowはプラグインのコンポーネントとして同梱できない。[Plugins reference](https://code.claude.com/docs/en/plugins-reference)のプラグインディレクトリ構造・File locations referenceが挙げるコンポーネントは`skills/` `commands/` `agents/` `output-styles/` `themes/` `hooks/hooks.json` `.mcp.json` `.lsp.json` `monitors/monitors.json` `bin/` `settings.json`のみで、`workflows/`は含まれない。`claude plugin init --with`が受け付けるコンポーネント一覧(`skills, agents, hooks, mcp, lsp, output-style, channel`)にも`workflow`は無い。チーム共有したいworkflowは、プラグイン化ではなく`.claude/workflows/`にコミットして配布するのが現行の唯一の手段。この状況は将来のバージョンで変わりうるため、プラグイン同梱を検討する際は**claude-code-docsスキル**で最新仕様を再確認すること。

## argsによる入力

保存済みworkflowはグローバル`args`経由で入力を受け取れる。呼び出し例:

```text
Run /triage-issues on issues 1024, 1025, and 1030
```

配列・オブジェクトが構造化データとしてそのまま渡されるため、スクリプト側でJSON文字列としてパースする必要はない。`args`が渡されなければスクリプト内では`undefined`になる。

## 実行時の制約

| 制約                                                         | 理由                                                                                                                  |
| :----------------------------------------------------------- | :-------------------------------------------------------------------------------------------------------------------- |
| run中にユーザー入力を挟めない                                | 一時停止できるのはagentのpermissionプロンプトのみ。ステージ間で承認を挟みたいなら各ステージを別workflowとして分割する |
| スクリプト自身は直接ファイルシステム・shellにアクセスしない  | 読み書き・コマンド実行はagentが行い、スクリプトはagentの調整役に徹する                                                |
| 同時実行agentは最大16体(CPUコアが少ない環境ではさらに少ない) | ローカルリソース使用量の上限                                                                                          |
| 1 runあたり最大1,000 agent                                   | 暴走ループの防止                                                                                                      |

## 管理(`/workflows`)

| キー          | 動作                                                                              |
| :------------ | :-------------------------------------------------------------------------------- |
| `↑` / `↓`     | フェーズ・agentの選択                                                             |
| `Enter` / `→` | フェーズ→agentへドリルダウン。agentのプロンプト・直近のツール呼び出し・結果を確認 |
| `Esc` / `←`   | 1階層戻る                                                                         |
| `j` / `k`     | agent詳細のスクロール                                                             |
| `f`           | ステータスでagent一覧をフィルタ(再押下でサイクル)                                 |
| `p`           | runの一時停止/再開                                                                |
| `x`           | 選択中agentの停止、runにフォーカスしている場合はrun全体の停止                     |
| `r`           | 選択中の実行中agentを再起動                                                       |
| `s`           | runのスクリプトをコマンドとして保存                                               |

### resume

停止したrunは再開できる。完了済みagentはキャッシュされた結果を返し、残りだけが実際に走る。停止時に実行中だったagentは保存されず再開時にやり直しになるため、大きなagent1体より小さなagentに分けたworkflowの方が進捗を多く保持できる。resumeは同一セッション内でのみ有効で、Claude Codeを終了すると次のセッションではworkflowは最初から走る。

### コスト管理

1 runで多数のagentを起動するため、同じタスクを会話で進めるより多くのトークンを消費しうる。大規模タスクにかける前に、1ディレクトリ・狭い問いなど小さい範囲でまず走らせてコスト感を掴む。`/workflows`で各agentのトークン使用量を確認でき、いつでも停止して完了済み分は保持できる。

`/config`の「Dynamic workflow size」設定で、Claudeが書くスクリプトの既定規模にガイドラインを与えられる(プロンプトで別規模を明示すればそちらが優先される)。

| 値             | Claudeへのガイダンス |
| :------------- | :------------------- |
| `unrestricted` | ガイドラインなし     |
| `small`        | 5 agent未満を目指す  |
| `medium`(既定) | 15 agent未満を目指す |
| `large`        | 50 agent未満を目指す |

既定値は`medium`(v2.1.219未満は`unrestricted`が既定)。`/config workflowSizeGuideline=small`のように`/config`から変更できるほか、v2.1.219以降は`workflowSizeGuideline`設定キーとしてどの設定ファイル(`settings.json`等)からでも指定でき、その場合は`/config`側の値より優先され`/config`の行自体が非表示になる。

runがスケジュールしたagentが25体を超える、または見込みトークン総量が150万を超えると、進捗表示に`Large workflow`警告が出る(runの一時停止・停止は`/workflows`から)。ultracode有効時はこの警告が出ない(既に大規模runへの同意済みとみなされるため)。

セッションのモデルが各agentにも使われる。ステージごとに異なるモデルを使わせたい場合はスクリプト側でルーティングするか、`CLAUDE_CODE_SUBAGENT_MODEL`環境変数で上書きする。

### 無効化設定

- `/config`の「Dynamic workflows」トグル(セッションを跨いで永続)
- `~/.claude/settings.json`に`"disableWorkflows": true`(永続)
- 起動時に読まれる`CLAUDE_CODE_DISABLE_WORKFLOWS=1`環境変数
- 組織全体では managed settings の`"disableWorkflows": true`、または管理コンソールのトグル

無効化するとバンドル済みworkflowコマンドが使えなくなり、`ultracode`キーワードは反応しなくなり、`/effort`メニューから`ultracode`が消える。

## スクリプトAPI

Workflow運用時にランタイムへ渡る主なフィールド(Agent SDKの`Workflow`ツール入力型に基づく)。

| フィールド        | 型        | 説明                                                                                                                                                                                                                  |
| :---------------- | :-------- | :-------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `script`          | `string`  | インラインスクリプト。`export const meta = { name, description }`のリテラルで始まり、続けて`agent()` / `parallel()` / `pipeline()` / `phase()`を使った本体を書く。`meta.phases`配列で進捗画面上のステージ分けができる |
| `name`            | `string`  | バンドル済み、または`.claude/workflows/`に保存済みのworkflow名。スクリプトに解決される                                                                                                                                |
| `scriptPath`      | `string`  | ディスク上のスクリプトファイルへのパス。`script`/`name`より優先。呼び出しごとにスクリプトが永続化されパスが返るので、そのファイルを編集して同じ`scriptPath`で再実行すればイテレーションできる                         |
| `args`            | `unknown` | スクリプト内でグローバル`args`として公開される入力値。配列・オブジェクトはJSON文字列化せずそのまま渡す                                                                                                                |
| `resumeFromRunId` | `string`  | 再開したい過去runのID。入力が変わっていない`agent()`呼び出しはキャッシュされた結果を返し、変わった/新規の呼び出しだけが実際に走る。同一セッション内のみ有効                                                           |

スクリプト本体で使える主な関数:

- `agent(prompt, options?)` — 1体のsubagentを起動。`options.schema`(JSON Schema)で構造化出力を受け取れる。`options.label`は進捗画面上の表示名。
- `pipeline(list, item => agent(...))` — リストの各要素に1体ずつagentを起動し、結果配列を返す(fan-out)。
- `parallel()` — 複数の非同期呼び出しをまとめて並列実行する。
- `phase()` — 進捗画面上でagent群を名前付きステージにグルーピングする。

これらの正確なシグネチャ・オプション全量は仕様変更の影響を受けやすいため、手でスクリプトを書く際はClaudeに生成・解説を依頼するか、Agent SDKリファレンス(`/docs/en/agent-sdk/typescript`の`Workflow`ツール項)を都度参照するのが安全。
