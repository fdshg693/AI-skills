---
name: cursor-plugin-use
description: Use when installing, creating, managing, or distributing Cursor plugins (the AI code editor) — plugin structure, the `.cursor-plugin/plugin.json` manifest, bundled components (rules, skills, agents, commands, MCP servers, hooks), local testing from `~/.cursor/plugins/local`, publishing to the Cursor Marketplace, team and Enterprise marketplaces, plugin installation modes, and managing installed plugins from Customize. Not for Agent Skills authoring details (use cursor-skill-use) or general Cursor features (use cursor-docs).
meta:
  tag: []
  requires_repo_tools: none
  requires_env: none
  dependencies: none
  requires_install: none
  requires_hooks: none
  requires_skills: cursor-docs, cursor-skill-use
  status: experimental
  description: no description
  version: 1.0.1
---

# Cursor プラグインの使い方

Cursor（AIコードエディタ）のプラグインを**使う・作る・配布する・管理する**ためのスキル。プラグインは rules・skills・agents・commands・MCP servers・hooks を配布可能なバンドルにまとめる仕組みで、Customize 画面や Cursor Marketplace からインストール・管理する。

プラグインに同梱されるスキルの `SKILL.md` の書き方詳細は **cursor-skill-useスキル**、Cursor全般の最新公式情報は **cursor-docsスキル** を使う。このスキルはスナップショットベースで陳腐化しうるため、最新情報はそちらを優先する。

## 公式ドキュメントを先に確認する

実装、レビュー、デバッグの開始時に、必ず最新の公式情報を確認する。マニフェストの完全スキーマ、コンポーネント形式、提出チェックリストは公式の Plugins reference が一次情報である。

1. **cursor-docsスキル** を使い、`cursor.com/docs` の Plugins ページおよび Plugins reference ページの最新本文を取得する。
2. 公式ページの取得に失敗した場合は失敗を明示し、本スキルが依拠するスナップショット（2026-07-20 取得、[../cursor-skill-use/references/plugins.md](../cursor-skill-use/references/plugins.md)）を使う。取得失敗時は変動しうる点（マニフェストの省略可能フィールド、ディレクトリ名、URL 等）を断定しない。
3. ローカルの記憶や古いサンプルだけで、マニフェストフィールド、コンポーネントの既定ディレクトリ、インストール手順を決めない。

> **取得状況（2026-07-29）**: `https://cursor.com/docs/plugins.md` および `https://cursor.com/docs/reference/plugins.md` は本環境から 404 で取得できなかった。以下は 2026-07-20 時点のスナップショットに基づく。公式参照を試みたうえで、変動しうる点はスナップショットの記述範囲にとどめる。

## プラグインの構成要素

プラグインは以下のコンポーネントを任意の組合せでバンドルできる。

| コンポーネント  | 説明                                                  |
| --------------- | ----------------------------------------------------- |
| **Rules**       | 恒久的なAIの指針・コーディング規約（`.mdc` ファイル） |
| **Skills**      | 複雑なタスク向けの特殊なエージェント能力              |
| **Agents**      | カスタムエージェント設定とプロンプト                  |
| **Commands**    | エージェント実行可能なコマンドファイル                |
| **MCP Servers** | Model Context Protocol 連携                           |
| **Hooks**       | イベント駆動の自動化スクリプト                        |

プラグインは **canvases**（共有セットアップテンプレート）を同梱することもできる（例: Hex Canvas・Atlassian Canvas）。インストール済みプラグインから Customize で開き、ゼロから設定せずに開始できる。

## プラグインの構造とマニフェスト

プラグインは `.cursor-plugin/plugin.json` マニフェストを持つディレクトリ。コンポーネントは既定ディレクトリから自動発見される。公式テンプレート（`github.com/cursor/plugin-template`）から始めるか、ゼロから作る。

```text
my-plugin/
├── .cursor-plugin/
│   └── plugin.json
├── rules/
│   └── coding-standards.mdc
├── skills/
│   └── code-reviewer/
│       └── SKILL.md
└── mcp.json
```

マニフェストで必須なのは `name` のみ。`description`・`version`・`author.name` は省略可能。コンポーネントは既定ディレクトリから自動発見されるが、マニフェストでカスタムパスを指定することもできる（完全スキーマ・カスタムパス指定は公式 Plugins reference を確認すること）。

```json
{
  "name": "my-plugin",
  "description": "Custom development tools",
  "version": "1.0.0",
  "author": { "name": "Your Name" }
}
```

> このリポジトリでは `cursor-plugins/meta/` がプラグイン（`.cursor-plugin/plugin.json` あり）。既存スキル（cursor-cli-docs 等）は公式既定の `skills/` ではなくプラグインルート直下に置かれている点に注意。ここへ追加する場合は既存配置に倣いつつ、Cursor の Customize 画面で実際に認識されるか確認する。

## プラグインのインストール

プラグインはマーケットプレースからインストールし、プロジェクトスコープまたはユーザーレベルで使える。

- **公式マーケットプレース**: [cursor.com/marketplace](https://cursor.com/marketplace) で公式プラグインを発見・インストール。プラグインは Git リポジトリとして配布され、一つ一つ手動レビューを経て掲載される。
- **コミュニティ**: コミュニティプラグインや MCP サーバーは [cursor.directory](https://cursor.directory) を参照。
- **Customize**: サイドバーの Customize からキーワード検索でインストールできる。
- **MCP Apps deeplinks**: MCP サーバー設定をインストールリンクで共有できる（`cursor://anysphere.cursor-deeplink/mcp/install?...` 形式。詳細は公式 MCP install links ドキュメント）。

## プラグインの作成

1. `.cursor-plugin/plugin.json` マニフェスト（必須は `name` のみ）を持つディレクトリを作る。
2. バンドルしたいコンポーネント（rules・skills・agents・commands・hooks・MCP サーバー）を既定ディレクトリに配置する。
3. コンポーネントは既定ディレクトリから自動発見される。既定以外の場所に置きたい場合はマニフェストでカスタムパスを指定する（詳細は公式 Plugins reference）。

スキルの `SKILL.md` の書き方（frontmatter の `name`/`description`/`paths`/`disable-model-invocation`、発見場所、スコーピング）は **cursor-skill-useスキル** を参照。プラグインに同梱するスキルも同じ仕様に従う。

## ローカルテスト

公開前に `~/.cursor/plugins/local` から読み込ませる。

1. プラグイン用フォルダを作る: `~/.cursor/plugins/local/my-plugin`
2. プラグインファイルをコピーし、`.cursor-plugin/plugin.json` がプラグインルートにあることを確認する。
3. Cursor を再起動、または **Developer: Reload Window** を実行する。
4. Customize でルール・スキル・MCP サーバー等の読み込みを確認する。

高速なイテレーションにはシンボリックリンクを使う。

```bash
ln -s /path/to/my-plugin ~/.cursor/plugins/local/my-plugin
```

## 公開

準備ができたら [cursor.com/marketplace/publish](https://cursor.com/marketplace/publish) から審査に提出する。全プラグインがオープンソース必須・手動レビュー対象で、更新時も掲載前にレビューされる。

マルチプラグインリポジトリの場合は `.cursor-plugin/marketplace.json` を置く。完全なマニフェストスキーマ・コンポーネント形式・提出チェックリストは公式 Plugins reference を参照。

## チーム・エンタープライズマーケットプレース

チームマーケットプレースは Teams および Enterprise プランで利用可能（Teams: 最大1つ、Enterprise: 無制限）。**Dashboard → Plugins** で管理する（Enterprise では管理者のみ追加可能）。

### Default チームマーケットプレース

**Default** チームマーケットプレースは共有プラグインと MCP サーバーを Cursor 全体で連携する。管理者は Cloud Agents で利用可能な Team MCP サーバーを追加し、同じサーバーをチームメイトが Agent Window・IDE・CLI でインストール・設定できるようにできる。ただし Default マーケットプレースに追加しても全開発者に自動インストール・有効化されるわけではない（管理者がマーケットプレースのアクセスとインストールモードを制御し、各開発者は MCP プロバイダで認証が必要な場合がある）。

### 既存 Team MCP の移行

管理者はスタンドアロンの Team MCP サーバーを Default マーケットプレースへリンクできる: **Dashboard → Integrations & MCP → Team MCP Servers → Add to Team Marketplace**、その後 **Dashboard → Plugins** で確認。マーケットプレースからリンクした MCP プラグインを削除、またはマーケットプレースを削除すると Team MCP サーバーが削除されることがある（確認メッセージを確認してから続行する）。

### マーケットプレースのアクセス制御

チームマーケットプレースは既定でチーム全員が利用可能。**Marketplace Settings → Marketplace Access** で選択した Organization Group に制限できる（チームのメンバーかつ選択グループ所属のユーザーのみアクセス、チーム管理者は常にアクセスを保持）。Organization Group のメンバーシップは SCIM で IdP から同期できる。

### プラグインのインストールモード

対象オーディエンスごとに配布方式を選ぶ。

- **Default Off**: 開発者がプラグインを見つけて自分でインストールするか選べる。
- **Default On**: 既定でインストールされるが、開発者はオプトアウトできる。
- **Required**: 常にインストールされ、アンインストール不可。

### チームマーケットプレースの追加

GitHub リポジトリをチームマーケットプレースとしてインポートする流れ: **Dashboard → Plugins → Team Marketplaces → Add Marketplace** でゼロから作成、または "Import from Repo" で GitHub からインポート。その後 "Add to Marketplace" でプラグインを追加・レビューし、**Marketplace Settings** でアクセス・Auto Refresh を設定する。

### プラグインの最新保持

GitHub からインポートした場合、初回インポート時にプラグインがインデックスされる。更新方法は2つ。

- **自動**: Enable Auto Refresh をオンにすると、マーケットプレースが追跡するブランチに push があるたび自動更新される（[Cursor GitHub App](https://cursor.com/docs/integrations/github.md) のインストールが必要。最大10分に1回再インデックスされ、連続 push は最新コミットにバッチ化される）。
- **手動**: "Refresh" をクリックする。

Auto Refresh は既にマーケットプレース内にあるプラグインの更新のみ行う。リポジトリに新規追加されたプラグインは自動で拾われないため、リポジトリ URL を再インポートする。

## インストール済みプラグインの管理

サイドバーの **Customize** を開き、プラグイン・MCP サーバー・ルール・スキルを1ページで管理する。user・workspace・team スコープでフィルタし、何がインストールされているか確認できる。

- **MCP サーバー**: Customize で各サーバーのトグルを on/off する。無効化したサーバーは読み込まれず、チャットにも現れない。
- **Rules と Skills**: Customize で管理する。ルールは Always / Agent Decides / Manual を切り替えられる。スキルは Agent Decides セクションに現れ、チャットで `/skill-name` で手動呼び出しもできる。

### workspaceOpen フックでの動的プラグイン読み込み

`workspaceOpen` フックがプラグインパスを返すと、ワークスペースを開いたときにそのプラグインを読み込める。読み込むプラグインセットがワークスペース自身に依存する場合に有用（詳細は公式 Hooks リファレンス）。

## デバッグと検証

1. プラグインが Customize に表示されない場合は、`.cursor-plugin/plugin.json` がプラグインルートにあるか、`name` フィールドがあるか、配置場所（`~/.cursor/plugins/local/<name>/`）を確認し、**Developer: Reload Window** で再読み込みする。
2. ローカルテストはシンボリンクリンクで高速イテレーションし、各コンポーネント（ルール・スキル・MCP サーバー）が期待通り読み込まれるか Customize で個別に確認する。
3. スキルが認識されない場合は `name` とフォルダ名の一致・配置場所を確認する（詳細は cursor-skill-useスキル）。
4. MCP サーバーが動かない場合は OAuth 必要な local MCP の前提（Cursor アプリでの事前認証）や、cloud と local で `headers`/`auth`/`env` の到達先の違いを確認する（詳細は cursor-docs / 公式 MCP ドキュメント）。
5. 公開前に、テンプレートリポジトリの構成と自分のプラグイン構成を見比べ、コンポーネントが既定ディレクトリ（またはマニフェストのカスタムパス）に置かれているか確認する。

## 関連ドキュメント

- [Plugins](https://cursor.com/docs/plugins.md) — プラグインの使い方・作り方・マーケットプレース（本スキルのスナップショット一次情報）
- [Plugins reference](https://cursor.com/docs/reference/plugins.md) — マニフェスト完全スキーマ・コンポーネント形式・提出チェックリスト
- [Marketplace security](https://cursor.com/help/security-and-privacy/marketplace-security.md) — プラグインのレビュー・セキュリティ
- [MCP install links](https://cursor.com/docs/mcp/install-links.md) — MCP サーバー設定の共有リンク
- [Cursor Marketplace](https://cursor.com/marketplace) — 公式プラグインの発見・インストール
- [cursor.directory](https://cursor.directory) — コミュニティプラグイン・MCP サーバー
- [plugin template repository](https://github.com/cursor/plugin-template) — 公式プラグインテンプレート
- スキルの `SKILL.md` の書き方・発見場所・フロントマターは **cursor-skill-useスキル**、Cursor全般の最新公式情報は **cursor-docsスキル** を使う
