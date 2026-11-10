## このフォルダの責務

- tools に依存しない汎用の Claude Code スキルを、プラグイン単位（`plugins/<plugin>/`）で置く。他 AI ツールの使い方の知識も、普通の SKILL.md として `plugins/ai-tools-knowledge/` に置く。
- 本文が `tools/<name>` の CLI のインストールを必須にするスキルはここに置かない（`tools/_plugin/my-tools/`）。このリポジトリの保守にしか意味がないスキルも置かない（アンブレラの `maintenance/plugin/`）。判定基準は [repo-layout](../maintenance/docs/repo-layout.md#置き場所の判定基準)。
- スキルを書く・直すときの手引きは `plugins/cc-knowledge/skills/writing-skill/` にある。このフォルダの中なので Junction では見せていない。スキルとして起動されないため、ファイルとして読む。
- プラグインの公開（マーケットプレイス・スキル公開サイト）は `_umbrella/registry/ai-tools.yaml` で決まる。プラグインを足したり消したりしたら、アンブレラ側で先にそこを更新する。

## このフォルダだけを開いたとき

アンブレラ（fdshg693/AI）の `skills/` として clone されている前提。共通の手順（Junction・フックの作り方、`_umbrella/` の扱い、2 段階コミット）は [repo-layout](../maintenance/docs/repo-layout.md#サブモジュールを単体で開く)。
