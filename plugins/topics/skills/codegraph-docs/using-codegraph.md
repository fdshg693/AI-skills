# CodeGraph を使う

公式ドキュメントの再掲ではない。MCP / CLI を実際に叩いたときに判断が割れやすい点と、実行前に押さえておくと無駄打ちが減る点だけ書く。製品仕様の根拠が必要なら [SKILL.md](SKILL.md) の公式ドキュメント手順へ戻る。フラグ名・正確な呼び出し形は [cli-help.md](cli-help.md)。

## 目次

- [実行前](#実行前)
- [概要・地図を取る](#概要地図を取る)
- [デフォルトは explore 1本](#デフォルトは-explore-1本)
- [クエリの書き方](#クエリの書き方)
- [返ってきた出力の扱い](#返ってきた出力の扱い)
- [グラフに載らないもの](#グラフに載らないもの)
- [explore より狭い検索](#explore-より狭い検索)
- [索引の鮮度](#索引の鮮度)
- [やらないこと](#やらないこと)

## 実行前

**索引の有無を先に見る。** `codegraph status` で足りる。未初期化なら `codegraph init`（`.codegraph/` 作成と初回索引が一体）。既に索引があるプロジェクトで `init` や `index --force` から始めない。

**MCP が見えるとは限らない。** 設定ファイルに `codegraph` サーバがあっても、そのセッションのツール一覧に載らないことがある（未接続・起動失敗・セッション開始後の追加）。一覧に `codegraph:codegraph_explore` が無ければ、接続修復に手を出さず CLI の `codegraph explore` に即切る。出力は同じ。

**`codegraph serve --mcp` は手で起動しない。** エージェント側が立ち上げる。索引が無いワークスペースではサーバは自分を inactive にしてツールを出さない。壊れているのではなく、索引は人間側の判断のまま、という仕様。

**Cursor だけ cwd がずれる。** Cursor は MCP 子プロセスの作業ディレクトリをプロジェクトルートにしないことがある。手で配線するなら `args` に `--path` で対象ルートを渡す。インストーラ経由なら既に入っていることが多い。

**Python から CLI を呼ぶときは `shutil.which("codegraph")` のパスを使う。** Windows の npm グローバルは `codegraph.cmd` で、素の `"codegraph"` を `CreateProcess` すると失敗する。

## 概要・地図を取る

新しいリポジトリ、または「どこに何があるか」だけが欲しいときは **explore しない**。広い問い（「このプロジェクトはどう動く」「構成を教えて」）は、クエリ語に似たシンボル名（`project_*` / `config` / `main`）へ寄り、アーキテクチャは返らない。

先にこの 2 本。両方合わせて数秒で足りることが多い。

1. `codegraph status` — 言語構成・ノード数・索引の健康
2. `codegraph files --max-depth 2` — 索引に載っているファイルの木。filesystem の `ls` より安い

MCP の `codegraph_files` / `codegraph_status` はデフォルト非表示。地図を取るときは CLI を使う。`--json` は flat な全ファイル一覧になり、`--max-depth` は tree 形式にしか効かない。

特定ディレクトリだけ見るなら `codegraph files --filter <dir> --max-depth 3`。`--filter` は前方一致なので、`tools` は `tools/` に加え `tools` で始まる別パスも含む。`site/tools-site` は `site` 側であり、`tools` では含まれない。

索引の木はディスクの全ファイルではない。対応言語以外（典型は `.md`）と除外パスは出ない。地図に無いトップレベルは README を `Read` する。フォルダ名が分かってから、そのパスを混ぜて explore する。

## デフォルトは explore 1本

地図のあとに、名前の付いた流れ・シンボルを追うならこれだけ。

- MCP: `codegraph:codegraph_explore`
- CLI: `codegraph explore "<query>"`

自然言語の質問でも、シンボル名・ファイル名の袋でもよい。返るのは関連シンボルの**行番号付きソース**（`Read` と同じ形）と、それらの間の呼び出し経路、変更時の blast radius。1回で足りることが多い。

他の MCP ツール（`codegraph_node` / `codegraph_search` / `codegraph_callers` 等）は存在するが、デフォルトでは非表示。explore の応答に同じ情報が既に載る。`CODEGRAPH_MCP_TOOLS` で増やす必要は通常ない。

## クエリの書き方

具体的なシンボル名やファイルパスを混ぜた短い質問が強い。ファイル名を入れるとそのファイルが pin される。

```text
codegraph explore "how does login work"
codegraph explore "handleRequest auth.ts"
```

広すぎる問い（「このプロジェクトはどう動く」）は、関係の薄い数ファイルに寄ることがある。先に [概要・地図を取る](#概要地図を取る)。分かっている名前は `codegraph query <name>` で拾ってから explore する方が安い。

言語は問わない。英語でもそれ以外でも、ヒットするシンボルさえあれば同じ形で返る。

CLI で応答が大きすぎるときは `--max-files` でソース件数を落とす。

```text
codegraph explore --max-files 2 "handleRequest auth.ts"
```

## 返ってきた出力の扱い

応答はだいたい次の順。

1. **Blast radius** — 触ると影響するシンボルと、近くにテストがあるか
2. **Relationships** — `calls` / `references` / `instantiates` など
3. **Source Code** — ファイルごとに行番号付きの現行ディスク内容
4. **Not shown above** — 関連だがソース未掲出の名前
5. **Explore budget** — このプロジェクト規模での追加 explore 回数の目安

ソースブロックは「いま読んだ `Read`」として扱う。掲出済みファイルを読み直さない。大きいファイルは `... (gap) ...` で中抜きされる。gap の行だけが必要なら、その範囲を `Read` するか、そのシンボル名でもう一度 explore する。

未掲出が必要なら、budget の範囲で **名前を指定した 2 回目の explore** を先に使う。grep / `Read` の巡回より安い、という前提で書かれている。

Shell 経由の CLI は、エージェント側の出力上限で途中切断されることがある。切れたらクエリを狭めるか `--max-files`、1 シンボルなら `codegraph node <symbol>`。MCP が生きていればそちらを優先する（同じ内容をツール応答として受け取れる）。

## グラフに載らないもの

索引は**対応言語の拡張子**のソースだけ。公式が挙げていない拡張子（典型は `.md`）はファイル一覧にも出ない。ドキュメント本文を explore しても、名前がコード側シンボルに偶然似ている結果だけが返ることがある。

YAML など設定ファイルは言語として載ってもシンボル 0 件のことがある。キーやコメントの中身はグラフの仕事ではない。設定の意味は `Read` する。

`node_modules` / `dist` / `.gitignore` 対象 / 1 MB 超はデフォルトで除外。欲しいファイルが無いときは、言語対象外か除外かを疑う。`codegraph.json` はゼロコンフィグのままでよく、除外・非標準拡張子が本当に必要なときだけ足す。

## explore より狭い検索

名前や影響範囲だけ欲しくてソースが要らないとき。リポジトリの地図なら上の [概要・地図を取る](#概要地図を取る) が先。それ以外は最初の一手にはしない。

| 欲しいもの                      | CLI（MCP は同名が非表示）                        |
| ------------------------------- | ------------------------------------------------ |
| 索引上のファイル木              | `codegraph files [--max-depth N] [--filter dir]` |
| 索引の健康・言語構成            | `codegraph status`                               |
| シンボル名の候補                | `codegraph query <name>`                         |
| 1 シンボルの本体と caller trail | `codegraph node <symbol>`                        |
| 呼び出し元だけ                  | `codegraph callers <symbol>`                     |
| 変更の影響だけ                  | `codegraph impact <symbol>`                      |

`query` / `callers` / `callees` / `impact` は `--json` が使える。単純な関数は callee が空のことがある（組み込みや辞書アクセスだけ、など）。無いこと自体は異常ではない。

## 索引の鮮度

MCP の `serve --mcp` が生きていれば、ネイティブのファイル監視が debounce 付きで incremental sync する。編集直後の短い窓では、応答先頭に stale バナーが付く。バナーに名前があるファイルだけ `Read` し、それ以外はグラフを信じてよい。

MCP が居ない CLI セッションでは watcher も居ない。自分や他プロセスがファイルを書いたあとで調べるなら、先に `codegraph status`。pending がある、または明らかに古いと感じたら `codegraph sync`。フル作り直しの `index --force` は普段使わない。

## やらないこと

- `codegraph serve --mcp` を手で起動する
- 索引があるのに `init` や `index --force` から始める
- リポジトリ全体の概要を explore の広い問いで取ろうとする（`status` と `files` が先）
- 接続されていない MCP を何ターンも診断する（CLI に切る）
- デフォルトの 1 ツールを `CODEGRAPH_MCP_TOOLS` でメニューに戻す
- `.codegraph/` を git 管理する（マシンローカルの SQLite。再生成できる）
- Windows と WSL から同じ `.codegraph/` を共有する（ロックと SQLite が OS 依存。片方で `CODEGRAPH_DIR` を別名にする）
