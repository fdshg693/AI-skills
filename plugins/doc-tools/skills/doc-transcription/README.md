# doc-transcription

PDF と PowerPoint から選択できる文字を Markdown に書き出すスキル。実行時の手順は [SKILL.md](SKILL.md)。こちらは人間のメンテナ向けで、Claude は参照しない。

## なぜこの形か

プラグインだけをよそへ移しても動くように、スクリプトと `uv.lock` をスキルフォルダに同梱する。ルートの uv workspace の `members` には入れない。持ち出し先に `tools/` が無い前提である。

出力ファイル名は ASCII だけにする。日本語のファイル名を標準出力に出すと、Windows のコードページで化けてエージェントが開けなくなるため。stem の英数字以外は捨て、空なら `document` とし、正規化した絶対パスの SHA-256 先頭 8 桁を付ける。同じ入力の再実行は上書きする。元のファイル名は Markdown の先頭行に残す。

非表示スライドは除き、件数だけ先頭に書く。残したスライドの番号はデッキ内の位置のまま（詰めない）。オプションは第一版には無い。

## 依存

PDF だけ `pypdf[crypto]>=6.13.0`。下限は日本語 CMap（`90ms-RKSJ` / `UniJIS-UTF16`）が入った版。`crypto` extra（`cryptography`）は、AES の PDF を空のユーザーパスワードで開くために要る。パスワードの解除はしない。

PPTX は標準ライブラリの zip と XML で読む。表示順は `ppt/presentation.xml` の `sldIdLst`。`python-pptx`、`markitdown`、PyMuPDF、poppler、Tesseract は、表や図の再現と OCR が第一版の範囲を超えるため入れない。

## 第一版の対象外

スキャン PDF、画像だけのスライド、図・グラフ・SmartArt・チャートの中の文字、数式、フッター・日付・スライド番号の図形、`.ppt` / `.doc` / `.docx` / `.xlsx`、パスワードの解除、縦書きの読み順の修正、見出し推定、段組み、表の整形。文字化けや余計な空白は直さない。

## 手元での確認

リポジトリルートから。テストはパスを指定する。引数なしだと他のワークスペースのテストまで収集される。

```text
uv run --project skills/plugins/doc-tools/skills/doc-transcription pytest skills/plugins/doc-tools/skills/doc-transcription/tests
uv run ruff format --check skills/plugins/doc-tools/skills/doc-transcription
uv run --project skills/plugins/doc-tools/skills/doc-transcription doc-transcription "<file.pdf または file.pptx>"
```

成功時の標準出力は、カレントディレクトリ基準の `temp/doc-transcription/` に書いたファイルの絶対パス 1 行。`temp/` は gitignore 済み。
