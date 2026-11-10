# スキルを作る・配布する

Cursor向けスキルの作成・配置・配布の手順。使い方は [using.md](using.md)、フロントマター全フィールドなどの詳細仕様は [reference.md](reference.md) を参照。組み込みスキル `/create-skill` でスキャフォールドすることもできるが、ここでは手動で作る手順を説明する。

## 作成手順

1. **配置場所を決める**

   | 置き場所                                                     | 適用範囲                           |
   | ------------------------------------------------------------ | ---------------------------------- |
   | `.cursor/skills/<name>/` または `.agents/skills/<name>/`     | このプロジェクトのみ               |
   | `~/.cursor/skills/<name>/` または `~/.agents/skills/<name>/` | 自分の全プロジェクト（グローバル） |
   | プラグインに同梱                                             | 他人へ配布したい場合（後述）       |

   互換目的で `.claude/skills/`・`.codex/skills/`（およびホーム側）からも読み込まれるが、Cursor用に新規作成するなら `.cursor/` か `.agents/` を使う。モノレポではパッケージ配下の `.cursor/skills/` も自動で拾われ、そのディレクトリ配下のファイルに自動スコープされる（詳細は [reference.md](reference.md)）。

2. **ディレクトリと `SKILL.md` を作る** — スキルは「`SKILL.md` を含むフォルダ」。`name` はフォルダ名と一致させ、小文字英数字とハイフンのみにする。

   ```markdown
   ---
   name: my-skill
   description: Short description of what this skill does and when to use it.
   ---

   # My Skill

   Detailed instructions for the agent.
   ```

3. **`description` を発動条件として書く** — Agentは `description` を見て関連性を判断する（自動発動のインターフェース）。「何をするか」+「いつ使うか」を具体的に書く。

4. **本文は焦点を絞り、詳細は別ファイルへ** — スキルのリソースは必要時にオンデマンドでロードされる（progressive）。`SKILL.md` を簡潔に保ち、重い参照資料は `references/`、テンプレート等の静的リソースは `assets/`、実行可能コードは `scripts/` に置き、本文からスキルルート相対パスで参照する。

5. **必要なら発動を制御する**

   - 特定ファイルを扱うときだけ表面化: `paths` にglobを指定（例: `paths: "**/*.py, scripts/**/*.py"`。リスト形式も可）
   - 手動呼び出し専用にする: `disable-model-invocation: true`

6. **動作確認する** — **Customize** → **Skills** に表示されるか確認し、`/skill-name` で呼び出してみる。認識されない場合は `name` とフォルダ名の一致・配置場所を確認し、ウィンドウをリロードする。

## スクリプトを同梱する

`scripts/` に実行可能コードを置き、本文から相対パスで参照する（言語不問: Bash・Python・JavaScriptなど、エージェント実装がサポートする実行形式）。

```markdown
Run the deployment script: `scripts/deploy.sh <environment>`
Before deploying, run the validation script: `python scripts/validate.py`
```

スクリプトは自己完結にし、有用なエラーメッセージを出し、エッジケースを適切に処理すること。

## プラグインとして配布する

複数スキルの同梱や他人への配布はプラグインにする。プラグインは `.cursor-plugin/plugin.json` マニフェスト（必須は `name` のみ）を持つディレクトリで、コンポーネントは既定ディレクトリ（スキルなら `skills/`）から自動発見される（マニフェストでカスタムパス指定も可能）。

```text
my-plugin/
├── .cursor-plugin/
│   └── plugin.json
├── rules/
│   └── coding-standards.mdc
├── skills/
│   └── code-reviewer/
│       └── SKILL.md
└── mcp.json
```

- **ローカルテスト**: `~/.cursor/plugins/local/<plugin-name>/` に配置（シンボリックリンク可）してCursorを再起動、または **Developer: Reload Window** を実行し、Customizeでルール・スキル等の読み込みを確認する
- **公開**: https://cursor.com/marketplace/publish から審査に提出する（全プラグインが手動レビュー対象・オープンソース必須）。マルチプラグインリポジトリは `.cursor-plugin/marketplace.json` を置く
- このリポジトリでは `cursor-plugins/meta/` がプラグイン（`.cursor-plugin/plugin.json` あり）で、既存スキル（cursor-cli-docs 等）は公式既定の `skills/` ではなくプラグインルート直下に置かれている。ここに追加する場合は既存配置に倣いつつ、CursorのCustomize画面で実際に認識されるかを確認すること

## レビュー時のチェックリスト

- [ ] Cursor向けの仕様であり、他ツール固有のフロントマターフィールド・記法を混ぜていない
- [ ] `name` がフォルダ名と一致し、小文字英数字とハイフンのみ
- [ ] `description` に「何をするか」「いつ使うか」がある
- [ ] `SKILL.md` が焦点を絞り、常時必要でない資料を `references/` 等に分離している
- [ ] ファイル限定にしたい場合は `paths`、手動専用にしたい場合は `disable-model-invocation: true` を設定している
- [ ] **Customize** → **Skills** で表示され、`/skill-name` で呼び出せることを実機確認した
