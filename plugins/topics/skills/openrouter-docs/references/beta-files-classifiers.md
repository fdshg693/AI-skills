# Beta機能: Files と Classifiers

## Files

Source: `client-sdks/*/sdks/files/README`, Server Toolsの`openrouter:files`（[server-tools.md](server-tools.md)参照。Server Tools自体がBeta）

ワークスペーススコープのファイルストレージ。SDKで以下のCRUDを提供する。

- `files.list()` — ワークスペース内のファイル一覧
- `files.upload()` — ファイルアップロード（上限100MB）
- `files.retrieve(fileId)` — メタデータ取得
- `files.delete(fileId)` — 削除（不可逆）
- `files.download(fileId)` — 生バイト列を取得。**サーバー側で生成されたファイルのみ対象**で、アップロード済みファイルをdownloadすると400になる

これと組み合わせて、Server Toolの`openrouter:files`を使うとモデルがリクエスト中にワークスペースファイルを読み書き・編集・一覧できる。

## Custom Classifiers

Source: `guides/features/classifiers`

ワークスペース内の全生成を応答後に非同期でタグ付けする機能（応答自体のレイテンシは増加しない）。

- **プリセット**: Department / Audience / Engineering work / Agent complexity / Capitalizable software expense
- **自前定義**: 最大8軸のタクソノミーを定義可能
- **分類フロー**: リクエスト完了 → 分類ジョブをキューイング → 分類モデルが構造化出力でタグ付け → Logs/Activityに記録
- **モデル選択**: 安価なモデル（Haiku/Flash等）の使用が推奨される
- **課金**: 分類トークンは通常の生成同様課金。classifierを設定した管理者に課金され、個別APIキーには課金されない
- **失敗時**: 分類が失敗してもAPIレスポンス自体には影響しない（タグが付かないだけ）
- **確認場所**: [Logs](https://openrouter.ai/logs) / [Activity](https://openrouter.ai/activity)
- **スコープ**: ワークスペースごと。作成・管理はワークスペースのadminのみ

両機能とも仕様変更が入りやすいBetaに近い扱いのため、断定的に答える前に上記Sourceパスを`extract_doc_section.py`で再取得して裏取りすること。
