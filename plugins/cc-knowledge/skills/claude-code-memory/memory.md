# メモリについて

<!-- claude_code/memory.md と同内容。更新する場合は両方に反映すること -->

Claude Codeの各セッションは空のコンテキストから始まる。過去の知見をセッションをまたいで引き継ぐ仕組みが2つある。

|                | `CLAUDE.md`                                    | Auto memory                                          |
| -------------- | ---------------------------------------------- | ---------------------------------------------------- |
| 書く人         | 自分（人間）                                   | Claude自身                                           |
| 内容           | 指示・ルール                                   | 学んだこと・パターン                                 |
| スコープ       | Project / User / Managed                       | リポジトリ単位（worktree間で共有）                   |
| 読み込まれ方   | 毎セッション全文                               | 毎セッション（`MEMORY.md`の先頭200行 or 25KBまで）   |
| 向いている内容 | コーディング規約・ワークフロー・アーキテクチャ | ビルドコマンド・デバッグの知見・Claudeが気付いた好み |

どちらもコンテキストとして注入されるだけで、強制力のある設定ではない（Claudeが従わない可能性がある）。強制したい場合は`PreToolUse`フックを使う。

## メモリの保存場所

`./CLAUDE.md`・`./.claude/CLAUDE.md`・`./.claude/rules/*.md`・`~/.claude/projects/<project>/memory/`
これらは全てセッション開始時に自動的に読み込まれる（rulesは`paths`指定がある場合は該当ファイルを開いたときのみ）。

## `CLAUDE.md`

- インポート機能
  - `@path/to/import`を使い自動的に他のパスのファイル内容をインポートすることが出来る（相対パスはインポート元のファイル基準、最大4階層まで再帰可能）
  - コードブロック内やバッククォートで囲んだ`` `@README` ``はインポートされず、文字列として扱われる
  - 初回インポート時は承認ダイアログが出る。拒否すると以後インポートは無効になり、ダイアログも再表示されない
- Claude Codeが探す範囲
  - CWDからルートまでさかのぼって`CLAUDE.md`・`CLAUDE.local.md`を探し、**全て連結して**コンテキストに載せる（上書きではない）
  - 順序はルートに近いものから先、CWDに近いものが後（＝後に読んだ方が優先されやすい）。同一階層では`CLAUDE.md`の後に`CLAUDE.local.md`
  - サブディレクトリの`CLAUDE.md`は起動時には読み込まれず、Claudeがそのディレクトリ配下のファイルを読んだタイミングで読み込まれる
  - https://code.claude.com/docs/en/memory#how-claude-looks-up-memories
- 保存先スコープ（読み込み順＝広い→狭い）

  | スコープ       | 保存先                                                                      | 用途                                             | 共有範囲          |
  | -------------- | --------------------------------------------------------------------------- | ------------------------------------------------ | ----------------- |
  | Managed policy | OSごとの管理者用パス（例: Windows `C:\Program Files\ClaudeCode\CLAUDE.md`） | 組織全体のポリシー                               | 組織全員          |
  | User           | `~/.claude/CLAUDE.md`                                                       | 個人の全プロジェクト共通の好み                   | 自分のみ          |
  | Project        | `./CLAUDE.md` または `./.claude/CLAUDE.md`                                  | チーム共有のプロジェクト指示                     | チーム（Git管理） |
  | Local          | `./CLAUDE.local.md`                                                         | 個人用のプロジェクト固有設定（`.gitignore`推奨） | 自分のみ          |

- `AGENTS.md`との共存
  - Claude Codeは`AGENTS.md`を直接読まない。`CLAUDE.md`に`@AGENTS.md`とインポートしてから、下にClaude固有の指示を追記する運用が推奨
  - シンボリックリンクでも代用可（Windowsでは管理者権限 or 開発者モードが必要なため`@AGENTS.md`インポートの方が無難）
- 書き方のコツ
  - 1ファイル200行未満を目安にする（長いと読み込みトークンが増えるだけでなく、遵守率も下がる）
  - Markdownの見出し・箇条書きで構造化する
  - 「コードを整形して」でなく「インデントは半角スペース2つ」のように検証可能な粒度で書く
  - モノレポで他チームの`CLAUDE.md`が無関係な場合は設定の`claudeMdExcludes`で除外できる
- 活用方法
  - `CLAUDE.md`に内容をべた書きせず、ファイル分割することで、共有・メンテナンスを簡単にする
  - 階層ごとに`CLAUDE.md`を配置することで、階層ごとに異なるメモリを適用することができる

## RULESファイル（`./.claude/rules/*.md`）

https://code.claude.com/docs/en/memory#modular-rules-with-claude/rules/

- 以下のようにfrontmatterでRULEを適用するパスを指定できる。
  - `paths`を指定しない場合は、`CLAUDE.md`と同じ優先度で毎回読み込まれる。
  - 除外するパスの指定はできない
  - パスに一致した場合は、Claudeがそのファイルを実際に読んだタイミングで読み込まれる（ツール呼び出しのたびにではない）

### 備考

- `Symlinks`が使える（共有ルールセットを複数プロジェクトにリンクする用途に便利）
- `/rules`配下であれば、直下でなくてもRULEファイルをサポートする（サブディレクトリで整理可能）
- `~/.claude/rules/`はユーザー全プロジェクト共通のルールになり、プロジェクトのrulesより先に（＝優先度は低く）読み込まれる

### 例

```markdown
---
paths:
  - "test/**/*.*"
  - "test2/test.txt"
---

# API Development Rules

- All API endpoints must include input validation
- Use the standard error response format
- Include OpenAPI documentation comments
```

## Auto memory

Claudeが自分自身の判断で気付いたこと（ビルドコマンド・デバッグの知見・アーキテクチャメモ・コーディング上の好み等）をメモしていく仕組み。人間が書く`CLAUDE.md`とは対照的に、Claudeが「将来のセッションで役立つ」と判断した内容だけを都度書き足す（Claude Code v2.1.59以降）。

### 保存場所

`~/.claude/projects/<project>/memory/`（`<project>`はGitリポジトリ単位。worktreeやサブディレクトリが違っても同一リポジトリなら共有される。Gitリポジトリ外ではプロジェクトルート単位）。

```text
~/.claude/projects/<project>/memory/
├── MEMORY.md          # 索引ファイル。毎セッション読み込まれる
├── debugging.md        # デバッグ手法の詳細メモ（トピックファイル）
├── api-conventions.md  # APIの設計判断など
└── ...                 # Claudeが必要に応じて作成するトピックファイル
```

- `MEMORY.md`は索引で、**先頭200行 or 25KBのどちらか早い方まで**が毎セッション自動読み込みされる（超えた部分は読み込まれない）
- トピックファイル（`debugging.md`等）は起動時には読み込まれず、Claudeが必要なときに通常のファイル読み込みツールで参照する
- `CLAUDE.md`にはこの200行/25KB制限はなく、常に全文読み込まれる（ただし短い方が遵守率は高い）
- 保存先はマシンローカル。同一リポジトリのworktree/サブディレクトリ間では共有されるが、別マシン・クラウド環境とは共有されない
- サブエージェントも専用のauto memoryを持てる

### 有効化・保存先の変更

デフォルトで有効。無効化・保存先変更は以下のいずれか。

```json
// settings.json
{
  "autoMemoryEnabled": false,
  "autoMemoryDirectory": "~/my-custom-memory-dir"
}
```

```shell
# 環境変数での無効化
CLAUDE_CODE_DISABLE_AUTO_MEMORY=1
```

`autoMemoryDirectory`は絶対パスか`~/`始まりが必須。プロジェクトの`.claude/settings.json`/`settings.local.json`で設定する場合は、ワークスペース信頼ダイアログを承認して初めて有効になる（hooksと同じゲート）。

### `/memory`コマンド

セッション内で読み込まれている`CLAUDE.md`・`CLAUDE.local.md`・rulesファイルの一覧表示、auto memoryのON/OFF切り替え、auto memoryフォルダを開くリンクの提供を行う。ファイルを選ぶとエディタで開ける。

「常に`npm`でなく`pnpm`を使って」のように口頭で頼むとauto memoryに保存される。`CLAUDE.md`に書かせたい場合は「これを`CLAUDE.md`に追加して」と明示するか、`/memory`から自分で編集する。

## トラブルシューティング

- **指示に従ってくれない**
  - `/memory`で該当ファイルが読み込まれているか確認する（一覧に無ければClaudeから見えていない）
  - 指示をより具体的にする（曖昧・矛盾した指示は無視されがち）
  - 特定のタイミングで必ず実行させたい処理（コミット前など）はメモリでなく[フック](https://code.claude.com/docs/en/hooks-guide)にする
- **`CLAUDE.md`が肥大化した**
  - 200行を超える場合はパス限定の`.claude/rules/`に切り出す。`@`インポートは整理には役立つが、起動時に全文読み込まれる点は変わらないためコンテキスト削減にはならない
- **`/compact`後に指示が消えたように見える**
  - プロジェクトルートの`CLAUDE.md`は`/compact`後に再読込されるが、サブディレクトリの`CLAUDE.md`はそのディレクトリのファイルを再度読むまで再読込されない
- **auto memoryが何を保存したか分からない**
  - `/memory`からauto memoryフォルダを開いて確認する。全てプレーンなMarkdownなので自由に編集・削除できる

## 参考文献

- https://code.claude.com/docs/en/memory
- https://code.claude.com/docs/en/claude-directory
