# サブエージェント/CLI分離でのテスト手法

hook・settings・skill・OTel設定などの変更が「実際に効いているか」を検証するための2つの手法（サブエージェントでの検証、Claude CLIによる完全分離テスト）をまとめる。全て実地検証（Windows 11 / Claude Code v2.1.215）で実際に動かした結果に基づく。

## 目次

- [この文書の対象外](#この文書の対象外)
- [サブエージェントでの検証（適用範囲と限界）](#サブエージェントでの検証適用範囲と限界)
- [Claude CLIでの完全分離テスト](#claude-cliでの完全分離テスト)
  - [`CLAUDE_CONFIG_DIR`だけでは足りない](#claude_config_dirだけでは足りない)
  - [認証情報の扱い](#認証情報の扱い)
  - [実際に動作確認済みの分離実行コマンド](#実際に動作確認済みの分離実行コマンド)
  - [`--debug-file`での記録とStep9・10への橋渡し](#--debug-fileでの記録とstep910への橋渡し)
- [使い分けの決定表](#使い分けの決定表)
- [参照](#参照)

## この文書の対象外

`writing-skill-complex`スキルの`testing-skills-with-subagents.md`にも「サブエージェントでのテスト」という言葉が出てくるが、目的が全く異なる。

|          | `writing-skill-complex`の対象                                             | この文書の対象                                                 |
| -------- | ------------------------------------------------------------------------- | -------------------------------------------------------------- |
| 検証対象 | **スキル文書自体**が圧力下でも遵守されるか（RED-GREEN-REFACTOR）          | **hookや設定変更**が実際に発火・適用されるかという動作確認     |
| 手法     | 同じシナリオをスキルあり/なしで比較し、合理化（言い訳）の文言を潰していく | 設定を実際に仕込み、ログ・生成物・応答内容で発火有無を確認する |

内容は転記せず、目的の違いだけをここに明記する。スキル文書のコンプライアンス検証がしたい場合は`writing-skill-complex`側を見ること。

## サブエージェントでの検証（適用範囲と限界）

Agent toolでサブエージェントを起動し、実際にツールを呼ばせて挙動を見る方法。素早く試せるが、**親セッションの設定・hookを完全に共有する**という限界がある点を先に理解しておくこと。

> **実地検証**: 本番プロジェクトの`.claude/settings.local.json`に一時的なPreToolUse+Bashログhookを仕込み、`general-purpose`サブエージェントに単純なBashコマンド（`echo`）だけを実行させて確認した。
>
> - 親セッションのhookが**そのまま発火**した。
> - 発火したhookのstdin JSONには`agent_id`・`agent_type`フィールドが追加される一方、**`session_id`と`transcript_path`は親セッションと完全に同一**だった。サブエージェントは別セッションとして分離されていない。

つまりサブエージェントでの検証は、次のような場合に向いている。

- 「今のセッションの設定のままで、この操作をエージェントにやらせたらどう動くか」を素早く見たいとき

逆に、次のような場合には向かない（完全分離が必要）。

- hookや設定を新規追加・変更した後、**クリーンな状態から本当に動くか**を確認したいとき
- 「そもそもこのhookが正しく登録されているか」自体を疑っているとき（親のhookをそのまま引き継ぐため、親側の設定ミスも一緒に引き継いでしまい切り分けにならない）

完全分離が必要な場合は、次節のClaude CLI分離テストを使う。

## Claude CLIでの完全分離テスト

`claude-cli-use`スキルの`-p`/`--print`単発実行をベースに、`CLAUDE_CONFIG_DIR`・`--safe-mode`・`--tools`/`--permission-mode`を組み合わせて「現在のセッションの設定・hookから実際に切り離されたテスト環境」を作る。

### `CLAUDE_CONFIG_DIR`だけでは足りない

⚠️ **落とし穴（実地検証で確認）**: 「`CLAUDE_CONFIG_DIR`を一時ディレクトリにすれば設定・hookから完全に切り離せる」という理解は誤り。

| 分離対象                                                                       | `CLAUDE_CONFIG_DIR`だけ                        | `--safe-mode`併用                                       |
| ------------------------------------------------------------------------------ | ---------------------------------------------- | ------------------------------------------------------- |
| ユーザースコープ設定（`~/.claude/settings.json`相当）・認証情報・`projects/`等 | 分離される                                     | 分離される（`CLAUDE_CONFIG_DIR`側の効果）               |
| プロジェクトスコープの`.claude/settings.json`（hook等）                        | **分離されない**（そのまま読み込まれ発火する） | 無効化される                                            |
| managed policy設定のhook                                                       | 分離されない                                   | **`--safe-mode`でも無効化されない**（管理者制御のため） |

実測: プロジェクト直下に`.claude/settings.json`でPreToolUse+Bashのログhookを仕込んだテスト用プロジェクトで、`CLAUDE_CONFIG_DIR`を一時ディレクトリに向けて`claude -p`を実行したところ、hookは**そのまま発火**した。`--debug-file`のログにも `Watching for changes in setting files <一時CLAUDE_CONFIG_DIR>\settings.json, <プロジェクト>\.claude\settings.json, <プロジェクト>\.claude\settings.local.json...` という行があり、プロジェクト側`settings.json`が監視・読み込み対象に含まれていることが確認できる。同じ設定のまま`--safe-mode`を追加すると、hookは発火しなくなった（`--debug-file`に `Skipping plugin hooks - safe mode disables plugins (managed settings-file hooks still run)` という行が出る）。

**結論**: 「プロジェクトの設定・hookも含めて本当にまっさらな状態から検証したい」場合は、`CLAUDE_CONFIG_DIR`単独では不十分で、必ず`--safe-mode`を併用する（またはプロジェクトディレクトリの外、かつ`.claude/settings.json`が存在しない場所で実行する）。逆に「ユーザースコープの設定だけ気にせずプロジェクトのhookは効かせたまま試したい」場合は`CLAUDE_CONFIG_DIR`単独で十分。

### 認証情報の扱い

`CLAUDE_CONFIG_DIR`を完全にクリーンな一時ディレクトリにすると、`~/.claude/.credentials.json`相当の認証情報も見えなくなる。

> **実地検証**: 認証情報を用意しない状態で`CLAUDE_CONFIG_DIR`分離実行を試したところ、`[ERROR] API error (attempt 1/11): Could not resolve authentication method. Expected one of apiKey, authToken, credentials, config, or profile to be set...` でAPI呼び出し自体が失敗し、`Not logged in · Please run /login`と表示された。この状態ではツール呼び出し（Bash等）が一度も発生しないため、**hookが発火する機会自体がない**（＝「hookが発火しなかった」ことと「そもそもモデルが動かなかった」ことを混同しないよう注意）。

分離環境で実際にタスクを完走させて検証したい場合は、どちらかの方法で認証を用意する。

1. **`~/.claude/.credentials.json`を一時`CLAUDE_CONFIG_DIR`にコピーする**（推奨）。元のファイルは変更しないコピー操作だが、認証情報を扱うためClaude Code自身の権限確認（auto modeの分類器）で止められることがある。その場合はユーザーに明示確認を取ってから実行し、**検証が終わったら一時ディレクトリごと削除する**。
2. `ANTHROPIC_API_KEY`環境変数を一時的に渡す（OAuthクレデンシャルには一切触れずに済む）。

### 実際に動作確認済みの分離実行コマンド

いずれも実際に実行し、狙った挙動を確認済み。`<一時CLAUDE_CONFIG_DIR>`と`<一時プロジェクト>`はスクラッチ領域配下に作成し、`~/.claude`や本番プロジェクトの`.claude/settings.json`には触れないこと。

**1. `CLAUDE_CONFIG_DIR`分離（プロジェクトのhookは効いたままにしたい場合）**

```bash
cd <一時プロジェクト> && \
CLAUDE_CONFIG_DIR=<一時CLAUDE_CONFIG_DIR> claude -p "<タスクの説明>" \
  --model haiku \
  --debug-file <ログ出力先パス> \
  --no-session-persistence
```

**2. `--safe-mode`併用（プロジェクトのhookも含めて完全にクリーンにしたい場合）**

```bash
cd <一時プロジェクト> && \
CLAUDE_CONFIG_DIR=<一時CLAUDE_CONFIG_DIR> claude -p "<タスクの説明>" \
  --model haiku \
  --safe-mode \
  --debug-file <ログ出力先パス> \
  --no-session-persistence
```

**3. 権限を絞った読み取り専用実行**

```bash
cd <一時プロジェクト> && \
CLAUDE_CONFIG_DIR=<一時CLAUDE_CONFIG_DIR> claude -p "<タスクの説明>" \
  --model haiku \
  --tools Read,Grep,Glob \
  --permission-mode plan \
  --debug-file <ログ出力先パス> \
  --no-session-persistence
```

> **実地検証**: 3のコマンドでファイル作成を指示したところ、実際にファイルは作成されず、応答は「I don't have access to a Write tool in this session, so I can't create the plan file required by plan mode. Could you enable file-writing tools, or let me know how you'd like to proceed?」だった。**`plan`モード自体が計画提示にWrite系ツールを要求するため、`--tools`でWriteを完全に外すと計画の提示すらできず、理由付きで差し戻される**という組み合わせの挙動が確認できた。単に「拒否されて終わり」ではない点に注意。

いずれも`--dangerously-skip-permissions`は使わない。共通で`--model haiku`を使っているのは、事実確認レベルの単純タスクでの検証コストを抑えるため（`claude-cli-use`のモデル選択基準を参照）。

### `--debug-file`での記録とStep9・10への橋渡し

`--debug-file <path>`は上記いずれのコマンドにも付けられる。`grep`で `Watching for changes in setting files` / `safe mode` / `API error` などの行を後から追えるため、分離実行の切り分けにはほぼ必須。取得したログが大きくなった場合は `${CLAUDE_SKILL_DIR}/scripts/extract_log.py` で必要な部分だけを抜き出せる（詳細はスクリプトの`--help`を参照）。

## 使い分けの決定表

| したいこと                                                                             | 使うもの                                                      |
| -------------------------------------------------------------------------------------- | ------------------------------------------------------------- |
| 今のセッションの設定のままで、ある操作をエージェントにやらせた場合の挙動を素早く見たい | サブエージェント（Agent tool）                                |
| hookや設定を新規追加・変更した後、クリーンな状態から本当に動くか確認したい             | Claude CLI分離テスト（`CLAUDE_CONFIG_DIR` + `--safe-mode`）   |
| 設定ファイル（`settings.json`）由来の問題かhook由来の問題かを切り分けたい              | `--safe-mode`（管理者制御のhookだけは無効化されない点に注意） |
| 書き込み権限を封じて読み取り専用の動作を試したい                                       | `--tools Read,Grep,Glob --permission-mode plan`               |
| 分離実行のログを後から機械的に追いたい                                                 | `--debug-file` + `${CLAUDE_SKILL_DIR}/scripts/extract_log.py` |

## 参照

- `claude-cli-use`スキル — `-p`/`--print`単発実行の基本形、モデル選択基準、`--dangerously-skip-permissions`を既定で付けない方針
- `claude-cli-docs`スキル — `--safe-mode`/`--debug-file`/`--tools`/`--permission-mode`等CLIフラグの正確な文言
- `writing-skill-complex`スキルの`testing-skills-with-subagents.md` — スキル文書自体のコンプライアンス検証（本文書とは目的が異なる。上記「この文書の対象外」参照）
- [logs-and-settings.md](logs-and-settings.md) — `CLAUDE_CONFIG_DIR`・settingsスコープの基本的な仕組み
- [hooks-logging.md](hooks-logging.md) — hookの発火条件・デバッグ方法の詳細
