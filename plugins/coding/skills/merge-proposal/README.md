# merge-proposal スキル

## 概要

- 現在のブランチに別ブランチを取り込む(マージする)**前に**、マージを試算して提案を作るスキル
- `git merge-tree --write-tree` でマージ結果を計算するため、ブランチ・インデックス・作業ツリーは一切変わらない(一時的な blob/tree がオブジェクトDBに書かれるだけで、どの ref からも参照されない)
- スクリプトが入力を2ファイル、エージェントが提案を最大3ファイル出す

| 誰が         | ファイル                   | 内容                                                                      |
| ------------ | -------------------------- | ------------------------------------------------------------------------- |
| スクリプト   | `CONFLICTS.md`             | コンフリクト一覧(種別・両側の変更・zdiff3 マーカー付きのコンフリクト箇所) |
| スクリプト   | `INCOMING.md`              | 取り込み内容(コミット一覧・両側の変更ファイル一覧・取り込み側の diff)     |
| エージェント | `1-conflict-resolution.md` | コンフリクト解消案                                                        |
| エージェント | `2-incoming-review.md`     | 取り込み内容のレビューと修正案                                            |
| エージェント | `3-follow-up.md`           | 取り込みを受けて現在のブランチが行うべき追従修正案                        |

- 3つの提案はユーザーが絞れる(例: 「コンフリクト解消案だけ」)
- 提案までで止まる。実際の merge・解消の適用・コミットなど、その後の作業は扱わない
- レビューだけしたい場合は `review` スキル(マージ先を指定したブランチ間差分レビュー)を使う。こちらは「取り込む側」に立った提案に特化している

## ディレクトリ構成

```
skills/merge-proposal/
├── SKILL.md             # 手順(実施項目の決定 → レポート生成 → 提案ファイル作成 → 報告)
├── output-formats.md    # 3つの提案ファイルの書式と観点
├── merge_report.py      # CONFLICTS.md / INCOMING.md を生成するスクリプト(標準ライブラリのみ)
├── .diffignore.example  # INCOMING.md の差分本文から除外するパターンの例
└── .gitignore           # .diffignore をコミット対象外にする

testing/
└── setup_merge_fixture.py  # 動作確認用の使い捨てリポジトリを testing/merge-fixture-repo/ に作る
```

## 使い方

Claude Code に自然文で依頼する。

- 「main を取り込む前にマージ提案を出して」
- 「develop をマージしたらどうなるか、コンフリクト解消案だけ出して」
- 「origin/main の取り込みについて、レビューは要らないので解消案と追従修正だけ」

スクリプトを直接実行する場合:

```bash
python skills/merge-proposal/merge_report.py <incoming-branch> [--current <branch>] [--repo <path>] [--output-dir <dir>]
```

## 依存関係

- git 2.38 以上(`merge-tree --write-tree`)
- `.diffignore` にパターンを書く場合のみ `pathspec`(`pip install pathspec`)

## スキルのテスト方法

`testing/` ディレクトリで実行する。フィクスチャは毎回作り直される(`testing/.gitignore` で除外済み)。

```bash
cd skills/plugins/coding/skills/testing
python setup_merge_fixture.py
python ../merge-proposal/merge_report.py main --repo merge-fixture-repo
```

フィクスチャは `feature` をチェックアウトした状態で、`main` を取り込む想定。確認ポイント:

- `CONFLICTS.md` に `calc.py`(content、ハンク1件)と `config.txt`(modify/delete、マーカー無し)が出ること
- `INCOMING.md` の表で `shared.txt` が「両側変更」あり・コンフリクト無しになること
- `api.py` の `greet` → `say_hello` 改名は、コンフリクトにならないが `app.py`(feature で追加)に追従修正が要る。エージェントに提案させたとき `3-follow-up.md` に拾われること
- サマリ表の「開始行」が各セクション見出しの行番号と一致すること
- 実行後も `git -C merge-fixture-repo status` がクリーンで、ブランチが `feature` のままであること

異常系:

- 取り込み先と同じブランチを指定 → 「取り込む内容はありません」
- 存在しないブランチを指定 → エラー
- 既に取り込み済みの祖先ブランチを指定 → 「既に取り込まれています」
