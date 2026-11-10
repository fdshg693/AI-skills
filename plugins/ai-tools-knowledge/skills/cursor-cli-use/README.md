# cursor-cli-use（メンテナ向けREADME）

`SKILL.md` はエージェントが実行時に読む判断・手順のみを書いており、設計意図や理由は書いていない（`writing-skill`スキルの方針: 判断根拠を本文に書くとClaudeがその理屈に固執したり、逆に本文を読み飛ばして理屈だけで独自判断したりする揺れが出るため、実行手順とは分離する）。このファイルは人間のメンテナ・および理由を知りたい場合向けの設計ドキュメント。

## スコープ

- **非対話（`-p`/`--print`）の単発実行のみ**を対象にした。対話的なREPL利用（`agent`をそのまま起動して会話する使い方）は別物として意図的に除外している。理由: このスキルはClaude Codeが「他のCLIエージェントに一撃タスクを委譲する」ためのものであり、対話セッションの管理（履歴・`/model`切り替え等）はスコープが異なるため。対話的な利用（複数ターンの文脈を保った会話、スラッシュコマンド操作等）が必要な場合は、汎用の対話CLI駆動ラッパーである**interactive-cli-wrapper**スキル（[SKILL.md](../../../../../tools/_plugin/my-tools/skills/interactive-cli-wrapper/SKILL.md)）を使う。
- モデル指定・料金・デバッグ・権限まわりの一次情報は `memos/` にまとめてある（`cursor-cli-docs`/`cursor-docs`スキルを使って2026-07-09時点で調査したもの）。

## モデル選択の理由（`SKILL.md`には書かない部分）

`SKILL.md`のモデル選択表は以下の理屈で決めている。根拠は [cursor.com/docs/models-and-pricing](https://cursor.com/ja/docs/models-and-pricing)（[memos/02-pricing-billing.md](memos/02-pricing-billing.md)にも要約あり）。

Cursorの個人プランには毎月リセットされる独立した2つの使用量プールがある:

1. **First-party models pool**: Auto / Composer 2.5 / Grok 4.5 専用。含まれる使用量が多い
2. **API pool**: それ以外のモデルを選んだ時に消費される、モデルのAPI単価そのままの少なめのプール（個人プランは最低$20/月分）

このため:

- **Composer 2.5・Grok 4.5のみをFirst-party poolの範囲内で使う** — 単純作業の大量処理はComposer 2.5、ある程度の判断力が要る作業はGrok 4.5に振ることで、Cursor CLIに委譲するタスクはFirst-party pool内で完結させる
- **First-party poolのモデルでは力不足な最難関タスク（設計判断・難しいバグ・セキュリティ・正確性が問われるもの）ではCursor側のAPI poolには踏み込まない** — 2026-07-09の変更で、以前はGLM 5.2・Claude Sonnet 5をAPI pool経由で使う運用にしていたが撤回した。代わりにCursor CLI自体を使わず、Claude Code側の`Agent`ツールでClaude Sonnet 5 / Opusのサブエージェントに直接委譲する方針にした。理由: Cursor CLIへの委譲は「他のCLIエージェントへの一撃委譲」がスコープであり（本ファイル冒頭の「スコープ」節参照）、最難関タスクではその委譲自体のオーバーヘッドやAPI pool消費を避け、委譲元であるClaude Code自身の力を使う方が単純だと判断したため

この理屈自体は`SKILL.md`には書いていない。`SKILL.md`は「タスクの性質→使うモデル／委譲先」という結果だけのトップダウンな表にして、エージェントが実行のたびに料金構造を再考しなくて済むようにしている。

**メンテナンス注意**: モデルの価格・ラインナップは変わりやすい。上記の理屈が古くなっていないか、`models-and-pricing.md`を再取得して定期的に見直すこと（[memos/README.md](memos/README.md)の未解決事項も参照）。モデル一覧が変わったら`SKILL.md`のモデル選択表も合わせて更新する。

## `--model`に渡すIDの確度とメンテ手順

`SKILL.md`のモデル選択表には`--model`に渡す実際のIDを直書きしている。実行のたびに`agent models`で確認させるのはオーバーヘッドなので、**IDを最新に保つ責務はエージェントではなくスキルのメンテナ側が負う**という方針にした（実行時は表をそのまま信用してよく、`model not found`エラーが出たときだけ`SKILL.md`側を参照して修正する運用）。

Cursor公式ドキュメントはモデルをdisplay name（例: "Claude Sonnet 5", "GLM 5.2"）で表記することが多く、CLIの`--model`に渡す実際のID文字列は必ずしも一致しない。2026-07-09時点で`agent models`の実機出力（バージョン`2026.07.08-0c04a8a`、認証済みアカウントで実行）を確認したところ以下の通り:

| Display name | 記載したID       | 確度               | 根拠                                                                                                                                                                                                                                                                                                                                              |
| ------------ | ---------------- | ------------------ | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Composer 2.5 | `composer-2.5`   | 確認済み           | `agent models`の出力に`composer-2.5 - Composer 2.5`としてそのまま存在                                                                                                                                                                                                                                                                             |
| Grok 4.5     | `grok-4.5-xhigh` | 確認済み（要注意） | プレーンな`grok-4.5`というIDは存在しない。`agent models`ではreasoning effort別に`grok-4.5-medium`（表示名「Grok 4.5 Low」）/`grok-4.5-high`（表示名「Grok 4.5 Medium」）/`grok-4.5-xhigh`（表示名「Grok 4.5」）等に分かれており、表示名とID中のeffortサフィックスが一致しない点に注意。「Grok 4.5」という無印表示名に対応するのは`grok-4.5-xhigh` |

このスキルを実際に使い始めて`model not found`等のエラーに遭遇したら、`agent models`（または`--list-models`）で正式なIDを確認し、上表と`SKILL.md`のモデル選択表を更新すること。旧バージョン（`2026.03.30-a5d3e17`）では同じアカウントで`agent models`が「No models available for this account」を返しており実機確認できなかったが、`2026.07.08-0c04a8a`では正常に一覧取得できた。CLIやアカウント状態次第で再び取得できなくなる可能性はあるため、この表もいずれ再検証が必要になりうる。

**注**: Kimi K2.7 Code・GLM 5.2・Claude Sonnet 5のID（`kimi-k2.7-code`／`glm-5.2-high`／`claude-sonnet-5-high`）も2026-07-09時点で実機確認済みだったが、2026-07-09の方針変更で`SKILL.md`のモデル選択表から外した（本ファイル上部の「モデル選択の理由」節参照）。Cursor CLI経由でこれらを再度使う判断になった場合は、上記の実機確認履歴が参考になる。

## `agent status`の自動チェックに関する注意

`SKILL.md`は起動時に`!`agent status`を動的コンテキスト注入で実行し、未認証ならユーザーに知らせる設計にしている。ローカル検証時、未認証状態で`status`を実行すると単に「未認証」と返るのではなく`Starting login process...`というブラウザ経由の認証フローを自動的に開始した（この挙動はドキュメントに明記されていない）。意図せずブラウザが開くのを避けるため、`NO_OPEN_BROWSER=1`を付けて実行している。

`status --format json`は、当初検証したバージョン`2026.03.30-a5d3e17`では`error: unknown option '--format'`となっていたが、2026-07-09時点の最新バージョン`2026.07.08-0c04a8a`では正常に動作し、`{"status": "authenticated", "isAuthenticated": true, ...}`のようなJSONを返すことを確認した（`agent about --format json`も同様に動作する）。

## なぜCursor側のカスタムSubagent委譲を勧めないことにしたか

**注**: ここでいう「Subagent」はCursor CLI独自の機構（`.cursor/agents/*.md`）であり、上の「モデル選択の理由」で触れたClaude Code側`Agent`ツールのSonnet/Opusサブエージェントとは無関係の別物。

当初は「同じ種類のタスクを2回以上頼むなら`.cursor/agents/<name>.md`にSubagent化する」という運用を`SKILL.md`に書いていたが、2026-07-09の実機検証（`temp/cursor-cli-use-basic-test/SUMMARY.md`）で撤回した。

- 自然文でのSubagent委譲（`agent -p --force "Use the bulk-reader subagent to ..."`）を実測したところ、同じ「ファイル1個への書き込み試行」というタスクで、直接実行（23.3s）に対し382.4s（約16倍）かかった。出力トークンも6,006と単発実行の10倍以上
- レスポンス内容から、時間の大半が「Subagent定義を探す→関連スキルを読む→過去の実行ログを確認する」という探索・自己文書化のオーバーヘッドに費やされていることが分かった
- `agent -p --help`を確認したが、Subagentを直接指定する専用フラグ（例: `--agent bulk-reader`）はCLIに存在せず、自然文委譲がサポートされる唯一の呼び出し方法。このオーバーヘッドはCLI側の制約であり、プロンプト設計での軽減には限界がある

このため`SKILL.md`では「Subagentに委譲せず、Claude Code側から`agent -p`を必要な回数だけ直接呼び出す」という方針に統一した。読み取り専用の強制についても、当初はSubagentの`readonly: true`を勧めていたが、`--force`を付けない（変更は提案のみで書き込まれない）、または`permissions.deny`（`cli-config.json`/`<project>/.cursor/cli.json`）でより確実に禁止する、という非Subagentの手段に置き換えている（[memos/04-tools-permissions.md](memos/04-tools-permissions.md)）。

Subagent自体の設計判断（Rules・Skillsとの使い分けなど）を深掘りする調査は [memos/05-reusable-agents-pointer.md](memos/05-reusable-agents-pointer.md) に残してあり、将来的に別スキルとして切り出す余地はある。ただし現時点の`cursor-cli-use`は「単発委譲」に徹し、Subagent運用は範囲外とする。

## なぜCLAUDE.md自動遵守の注意書きを追加したか

同じ検証で、依頼していないのにも関わらず`agent`がプロジェクトルートの`CLAUDE.md`（「実行結果サマリをログに残す」「積極的にスキル改善提案を行う」という指示）を自律的に発見・遵守し、`execution-log.md`を勝手に作成する副作用が確認された。明示的に「変更しないこと」と指示した回では自制されたため、指示の優先順位付け自体は機能している。

委譲元のClaude Code自身も同じ`CLAUDE.md`の指示に従う運用のため、素朴に委譲すると**ログ・成果物が二重生成される**リスクがある。`SKILL.md`にこの前提を明示し、厳密に副作用ゼロにしたい場合はプロンプト内で無効化を指示するよう案内することにした。

## なぜ`disable-model-invocation: true`にしたか

`agent -p --force`は実際にファイル書き込み・シェルコマンド実行を行い、かつ外部サービスの課金が発生する。`writing-skill`スキルのガイドラインでは副作用があり実行タイミングをユーザーが握りたい処理には`disable-model-invocation: true`を使うとされており、これに従った。Claudeが会話の流れだけで自動的に外部CLIへ課金付きタスクを投げないよう、明示呼び出し（`/cursor-cli-use`）に限定している。

## 関連

- [memos/](memos/) — 事前調査メモ本体（モデル指定・料金・デバッグ・権限・subagent仕様）
- [eval-logs/README.md](eval-logs/README.md) — モデル性能ログのフォーマット
- 別スキルとして切り出す予定の「Cursor subagent作成方法」は [memos/05-reusable-agents-pointer.md](memos/05-reusable-agents-pointer.md) にToDoとしてまとめてある（今回は範囲外）
