# 実験用サイトが要るとき

外部サイトを叩く前に、認証不要・ローカル完結のテストサイトで済まないか見る。
外部サイトは相手のあるアクション（[site-recon.md](site-recon.md) §7 の R1〜R7）で、回数にも内容にも制約がかかる。

## fdshg693/AI リポジトリの中で作業しているとき

`tools/browser/test-sites/` に自作の静的サイト 11 種がある（このスキルを別の場所へ持ち出した先には無い。無ければこの節は飛ばす）。

- 一覧と「目的から引く」逆引き表は `tools/browser/test-sites/README.md`
- 起動はリポジトリのルートで `just test-sites`。全サイトが `http://localhost:8080` に並ぶ（`/catalog/`・`/tables/`・`/frames/`・`/auth/` など）
- サイトを追加・変更するときの規約（role-based ロケータ、静的 HTML のみ、更新が必要な箇所）は `tools/browser/test-sites/AGENTS.md`

## テストサイトが無いとき

- 確かめたいことが 1 つの挙動（iframe・ダイアログ・遅延表示など）なら、最小の HTML を一時ディレクトリに書き、`playwright-cli open file:///...` で開く
- 外部サイトを使うなら、先に [site-recon.md](site-recon.md) の §0 と §7 を読む。`localhost`・社内・非公開ホストの URL は外部サービスに渡さない
