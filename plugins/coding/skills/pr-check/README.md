# PR確認・管理スキル

## フロントマター

- `allowed-tools` により、 `gh`・`git` コマンドおよびカスタムスクリプト（Python製）の使用を許可する
  - これにより、PRの詳細情報やCIチェック状態など、必要に応じて追加で情報を取得できるようにする

## スキルの説明

- PRの一覧取得は自動で実行する
  - ほぼ必ず実行する一覧取得コマンドを省略することで効率化
- コンテキストを大幅に消費しそうな内容は、自動埋め込みせずに、コマンドの実行を任せる
- PR詳細・レビューは同時に取得する需要があると考えてまとめて実行するためのカスタムスクリプトを用意

## 必要ツール

- Shellコマンドが使える環境
- GitHub CLI（`gh` コマンド）
- Gitコマンド（`git` コマンド）
- Github Copilotレビュー機能が有効になっている（レビュー機能を活用したい場合）

##　詳細メモ

### Copilotレビュー依頼の制約（リグレッション防止メモ）

- **個人アカウントのリポジトリでは、GitHub Copilot を Collaborator として追加できない**ため、`gh pr edit <N> --add-reviewer copilot-pull-request-reviewer` や `POST /repos/{owner}/{repo}/pulls/<N>/requested_reviewers` による**正規のレビュアー指定は不可**（422 Unprocessable Entity になる）。
- 代替として `gh pr comment <N> --body "@copilot review"` のように PR コメントで `@copilot review` メンションする方式を使う。これは Organization 契約なしの個人アカウントでも Copilot Pro/Pro+ があれば動作する公式サポート経路。
- 以前「ghコマンドでレビュアー追加 → 422で失敗 → ユーザーに設定確認を促す」という挙動にしていたが、これは**個人アカウントでは原理的に解決不可能**なので、最初から `@copilot review` コメント方式を案内する。ghコマンドで無理やりレビュー依頼しようとしない。

#### 参考リンク

- [Using GitHub Copilot code review](https://docs.github.com/en/copilot/concepts/code-review/code-review)
- [Requesting a code review from Copilot](https://docs.github.com/en/copilot/how-tos/use-copilot-agents/request-a-code-review/request-a-review)
- [Copilot が利用可能なプラン（個人アカウントは Copilot Pro/Pro+ が前提）](https://docs.github.com/en/copilot/get-started/plans)
