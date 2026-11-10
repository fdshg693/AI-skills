# ona-docs

## 補足

- `ona.com`は会社概要用の`llms.txt`/`llms-full.txt`、`ona.com/docs`は技術ドキュメント用の`llms.txt`/`llms-full.txt`をそれぞれ独立に公開している。どちらもファイル名が同じ(`llms.txt`/`llms-full.txt`)ため、取得元がわかるよう`output/company/`(会社概要)と`output/docs/`(技術ドキュメント)のサブディレクトリに分けて保存している。前者はページ単位マーカーの無い連続ドキュメント、後者は`# タイトル`/`Source: URL`が繰り返される全文ダンプという異なる形式なので、セクション抽出(`extract_doc_section.py`)は`docs/llms-full.txt`にのみ適用する
- Ona は旧社名 Gitpod からのリブランドで、学習データには古い社名・機能名が混ざっている可能性が高い。回答時は必ず取得した最新コンテンツの表記(社名、リーダーシップ、機能名)を優先する
