# gh-pr

## フロントマター

- `allowed-tools` により、 `gh`・`git` コマンドおよびカスタムスクリプト（Python製）の使用を許可する
  - これにより、PRの詳細情報やCIチェック状態など、必要に応じて追加で情報を取得できるようにする

## スキルの説明

- PRの一覧取得は自動で実行する
  - ほぼ必ず実行する一覧取得コマンドを省略することで効率化
- コンテキストを大幅に消費しそうな内容は、自動埋め込みせずに、コマンドの実行を任せる
- PR詳細・レビューは同時に取得する需要があると考えてまとめて実行するためのカスタムスクリプトを用意
- Actions の失敗原因の調査は `skills/plugins/cicd/skills/diagnosing-actions` に任せる。このスキルの `pr-actions.py` は run の一覧・詳細・手動実行・追跡が主で、`failed` は軽い確認用

## 必要ツール

- Shellコマンドが使える環境
- GitHub CLI（`gh` コマンド）
- Gitコマンド（`git` コマンド）
- Python（スクリプトは標準ライブラリのみ。配布先に uv があるとは限らないので `python` で呼ぶ）

## 詳細メモ

### 対象リポジトリの決まり方

- `gh` はカレントディレクトリの git remote から対象を決める。サブモジュールの中では親ではなくサブモジュールのリポジトリになる
- `-R OWNER/REPO` は環境変数 `GH_REPO` に入れて `gh` に渡す。`gh repo view` だけは `GH_REPO` を見ないので、`pr_common.py` の `repo_name_with_owner()`・`default_branch()` で個別に扱う
- `pr-create.py` は push 先がカレントの `origin` なので `-R` を持たない
