---
# 同梱のplugin.mdは参照用のリファレンス（プラグイン機構そのものの解説）。このファイル自体はプラグインを実際に書く際のベストプラクティス集
name: writing-plugins
description: Use when creating, structuring, or distributing a Claude Code plugin (.claude-plugin/plugin.json, skills/agents/hooks/mcp/lsp bundling, or a marketplace.json) — choosing plugin vs standalone .claude/, manifest fields, directory layout, versioning, and avoiding common pitfalls.
meta:
  tag: []
  requires_repo_tools: none
  requires_env: none
  dependencies: none
  requires_install: none
  requires_hooks: none
  requires_skills: claude-code-docs, writing-subagents, writing-hooks
  status: stable
  description: no description
  version: 1.0.0
---

# プラグイン作成のベストプラクティス

新しいClaude Codeプラグインを作る・既存プラグインの構成を見直す際の**実際に書く手順とチェックリスト**をまとめる。
プラグイン機構そのもの（フォルダ構造・`plugin.json`全フィールド・各コンポーネントの詳細・マーケットプレイス配布・バージョン解決など）の詳細は同梱の [plugin.md](plugin.md) を参照。

## 作成手順

1. **プラグイン化が本当に必要か確認する** — 個人利用・単一プロジェクト限定なら`.claude/skills/`や`.claude/agents/`のスタンドアロン配置で十分（短い`/hello`名で呼べる）。チーム・複数プロジェクト・コミュニティへの共有が必要になった時点でプラグイン化を検討する。
2. **既存のプラグインで代用できないか確認する** — このリポジトリの`plugins/`配下や公式マーケットプレイス（`/plugin`のDiscoverタブ）に近い役割のものが無いか探す。
3. **配置場所を決める** — `--plugin-dir`での試作なら任意のディレクトリ、チーム共有ならマーケットプレイス経由（`plugins/<name>/`をこのリポジトリの`.claude-plugin/marketplace.json`に登録）、個人の常用なら`claude plugin init <name>`で`~/.claude/skills/<name>/`に`@skills-dir`プラグインとして作る。
4. **`name`を決める** — kebab-case（英数字とハイフンのみ）。この名前がスキル・エージェントの名前空間プレフィックス（`<name>:skill-name`）になる。
5. **マニフェストを書く（必要な場合）** — `<plugin>/.claude-plugin/plugin.json`に`name`（必須）・`description`・`version`・`author`を書く。単一コンポーネントしか無くデフォルトパスで足りるなら、マニフェスト自体を省略してもよい。
6. **コンポーネントをプラグイン直下に配置する** — `skills/`, `agents/`, `hooks/hooks.json`, `.mcp.json`, `.lsp.json`など。**`.claude-plugin/`の中に置くのは禁止**（`plugin.json`以外は全てプラグインルート直下）。
7. **バージョン戦略を選ぶ** — 内部・開発中のプラグインは`version`を省略してgitコミットSHA方式に任せる。公開・安定版として配るなら`version`を明示し、変更のたびに必ず値を上げる（コミットを積むだけでは配信されない）。
8. **`--plugin-dir`でローカル検証する** — `claude --plugin-dir ./my-plugin`で起動し、スキル・エージェント・フックを個別に動作確認。編集後は`/reload-plugins`で反映。
9. **共有前に`claude plugin validate ./my-plugin --strict`を通す** — マニフェストのJSON構文・frontmatter・`hooks.json`の妥当性、未知フィールドの警告まで含めてチェックする。
10. **配布する** — チーム共有ならリポジトリの`marketplace.json`にエントリを追加（このリポジトリでは`maintenance/scripts/plugin_meta/generate/generate_marketplace.py`で`plugins/*/.claude-plugin/plugin.json`から自動生成される）。コミュニティ配布ならAnthropicの審査フォームから申請する。

## チェックリスト（ベストプラクティス）

- [ ] `name`はkebab-case（英数字・ハイフンのみ）。マーケットプレイスエントリの`name`と`plugin.json`の`name`が異なる場合、ユーザー向けの識別子（`enabledPlugins`や`/plugin`）はマーケットプレイス側が優先される点を理解している
- [ ] `commands/`・`agents/`・`skills/`・`hooks/`等を`.claude-plugin/`の中に置いていない（最頻出のミス）
- [ ] スキルが1つだけなら`skills/`ディレクトリを省略して`SKILL.md`をプラグイン直下に置く選択も検討した（frontmatterに`name`を明記して呼び出し名を固定する）
- [ ] フック・MCP・LSPの設定でプラグイン内ファイルを参照する際は絶対パスではなく`${CLAUDE_PLUGIN_ROOT}`を使っている（プラグインはキャッシュにコピーされるため、プラグイン外への相対参照`../shared-utils`は動かない）
- [ ] 更新をまたいで永続化したい状態（`node_modules`等）は`${CLAUDE_PLUGIN_ROOT}`ではなく`${CLAUDE_PLUGIN_DATA}`に置いている
- [ ] `version`を明示する場合、公開のたびに値を上げる運用を理解している（上げ忘れると既存ユーザーに配信されない）
- [ ] 秘密情報を扱う設定値は`userConfig`で`sensitive: true`にしている（ユーザーに手動で`settings.json`を編集させていない）
- [ ] チームへ配布する場合、`.claude/settings.json`の`extraKnownMarketplaces`/`enabledPlugins`で自動導入できるよう設定した
- [ ] 共有前に`claude plugin validate --strict`を実行し、警告も含めて確認している

## 困ったときは

1. まず同梱の [plugin.md](plugin.md)（詳細リファレンス: フォルダ構造、`plugin.json`全フィールド、Agents/Hooks/MCP/LSP/Monitors/Themesの各コンポーネント仕様、マーケットプレイススキーマ、バージョン解決順序、CLIコマンド一覧など）を確認する。
2. それでも解決しない、あるいは仕様が変わっている可能性がある場合:
   - `claude --debug`でプラグインのロード詳細（読み込まれたコンポーネント・エラー）を確認する
   - Claude Codeの仕様そのものについて最新の公式ドキュメントに基づく回答が必要な場合は**claude-code-docsスキル**
   - サブエージェント・フックそれぞれの詳細な作り方は**writing-subagentsスキル**・**writing-hooksスキル**
