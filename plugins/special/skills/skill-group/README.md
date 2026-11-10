# スキルグループ管理スキル

## 目的

複数のSKILLを束ねたスキルを公開する

- AIはスキルを全て読み込む必要がなくなり、初期コンテキストを抑えられる

## ユースケース

- AIから見て
  - 初期は、グループスキルがあるということだけを知る
  - SKILL実行時
    - 引数なし・または`groups`
      - `sub_skills.yaml` に定義されたスキルグループの名前を取得（Descriptionを表示しないことで、コンテキスト節約）
    - `list <group>`
      - 指定グループ配下のスキルの名前一覧を取得（同様にDescriptionは表示しない）
    - `show <name> [<name>...]`
      - 各引数に対応するスキルの以下の内容を取得（グループ横断で検索するため、グループ名の指定は不要）
        - スキルの名前・スキルの説明・スキルの場所
- 同階層にBashコマンドを作成
  - 引数を受け取って上のような挙動を行うスクリプトにする
    - SKILL側でそれを !`command args` の形で埋め込む
    - SKILLでは $ARGUMENTS の形で引数を参照できる機能を利用して引数をシェルスクリプトに渡す
  - SKILLは `.claude/skills/skill-group/sub_skills.yaml` に定義された各グループの `path` から動的に取得
    - `sub_skills.yaml` は `name` / `description` / `path` を持つフラットなリスト
    - 各グループの `path`（`list-skills.py` からの相対パス）配下を全てのサブフォルダ（直下に限らない）まで探索して、`SKILL.md`を探して、フロントマターから名前・説明を探す

- ユーザー
  - AIに使うように指示することで、AIにSKILL発見を任せる

## フロントマター

- `disable-model-invocation: false` / `user-invocable: true` により、ユーザーからのスラッシュコマンド呼び出しとモデル自動起動の双方を許可
  - 「どんなサブスキルが利用できるか」を確認したい場面で気軽に呼び出せるようにする

## スキルの説明

- グループ一覧取得は SKILL.md 内の `!`...`` 記法で自動実行する
  - スキル起動時に毎回手動で `list-skills.py` を叩く手間を省くため
- サブスキル詳細はコンテキストを消費するため、自動で全件埋め込まず、必要なものだけ `list-skills.py show <name>` で取得する設計
- サブスキルは「スキルとしての呼び出し」はできないため、SKILL.md を直接 Read して内容を参照する運用にしている
  - ネストしたスキル登録は Claude Code の仕様上できないので、グループ化はあくまで参照用

## 必要ツール

- `python` が使える環境（標準ライブラリのみで動作、追加パッケージ不要）
  - `sub_skills.yaml` の解析も PyYAML 等には依存せず、本スキルが必要とする単純なスキーマ（フラットなリスト）専用の簡易パーサーを自前で実装している

## ディレクトリ構成

```
skill-group/
├── SKILL.md              # スキル本体（ユーザー/モデルから呼び出される）
├── README.md             # このファイル（スキル設計メモ）
├── list-skills.py         # グループ/サブスキル一覧・詳細出力スクリプト
├── sub_skills.yaml        # スキルグループ定義（name/description/path のリスト）
├── sub_skills/               # デフォルトのスキルグループ（sub_skills.yaml の "default" エントリが指す先）
│   └── <skill_name>/SKILL.md
└── tests/
    └── test_list_skills.py   # list-skills.py のユニットテスト（stdlib unittest）
```

他フォルダのスキル群を追加したい場合は、`sub_skills.yaml` に `name` / `description` / `path` を持つエントリを追加するだけでよい（`path` は `list-skills.py` からの相対パス）。同じ `name` のエントリを複数書けば、それらの `path` はまとめて1つのグループとして扱われる（`list <group>` は該当する全 `path` を再帰探索した結果を統合して返す）。

## 詳細メモ

### サブスキル探索の仕様（リグレッション防止メモ）

- `list-skills.py` は `sub_skills.yaml` に定義された各グループの `path` 配下を **再帰探索**して `SKILL.md` を収集する
  - サブディレクトリでの分類（カテゴリ別フォルダなど）にも対応するため
- スキル名はフロントマターの `name` フィールドを正としてsource of truthとする（ディレクトリ名ではない）
  - ディレクトリ名と `name` が食い違っても、ユーザー視点では `name` で識別する方が自然なため
- `show` はグループを横断して検索する（スキル名は全グループを通じて重複しない想定）
  - グループ名を指定しなくても目的のスキルに辿り着けるようにするため
- 存在しないグループ名・スキル名を引数に渡しても **エラー終了せず stderr に警告を出して継続**する
  - 複数スキル名を一括指定したときに、1件のtypoで全体が落ちないようにするため

### メンテナンス用: スキル名の重複チェック

`show` や `list` はスキル名（フロントマターの `name`）が全グループを通じて重複しないことを前提にしている。`sub_skills.yaml` にグループを追加・変更した際は、以下のコマンドで重複がないか確認する。

```bash
python list-skills.py check-unique
```

- 重複がなければ `OK: all skill names are unique` を出力して終了コード0
- 重複があれば該当する `name` と衝突している `SKILL.md` のパス一覧を stderr に出力し、終了コード1
- 同じフォルダが複数グループ（同名 `path` の重複登録など）から参照されているだけの場合は、同一ファイルとして扱われ重複扱いにはならない
- AI（SKILL経由の自動起動）からは呼び出されない、人間向けのメンテナンスコマンド

### テスト

`list-skills.py` の挙動（グループのマージ・重複排除・`check-unique` の判定など）は `tests/test_list_skills.py` で検証する。依存は標準ライブラリのみ（`pytest` 不要）。`sub_skills.yaml` / `SKILL.md` はテストごとに一時ディレクトリ（`tempfile.TemporaryDirectory()`）内に生成するため、リポジトリ本体の `sub_skills.yaml` やスキルフォルダを汚さない。

```bash
# リポジトリルートから
python -m unittest discover -s skills/plugins/special/skills/skill-group/tests -v
```

### サブスキル呼び出しの制約

- Claude Code のスキル機構は `.claude/skills/` 直下のみを認識し、ネストしたスキルディレクトリ（`sub_skills.yaml` の各 `path` 配下の `<name>/SKILL.md`）は **スキルとして自動登録されない**
- そのため、サブスキルを使いたい場合は SKILL.md を直接 Read して指示内容を取り込む運用にする
- スラッシュコマンドや Skill ツール経由の呼び出しは不可なので、サブスキル側で外部コマンドの自動許可（`allowed-tools`）を設定しても無効になる点に注意

#### 参考リンク

- [Claude Code Skills](https://docs.claude.com/en/docs/claude-code/skills)
