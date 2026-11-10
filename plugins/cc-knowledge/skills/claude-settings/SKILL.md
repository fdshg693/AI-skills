---
name: claude-settings
description: Claude Codeの設定ファイル（settings.json / settings.local.json / 環境変数）を追加・変更する際に使う。permissionsルールの追加、hooksの登録、サンドボックス設定、環境変数の設定、スコープ（User/Project/Local/Managed）選びで迷った時に使う。
meta:
  tag: []
  requires_repo_tools: none
  requires_env: none
  dependencies: none
  requires_install: none
  requires_hooks: none
  requires_skills: claude-code-docs, writing-hooks, writing-skill
  status: stable
  description: no description
  version: 1.0.0
---

# Claude Code設定ファイルの編集

`settings.json`（と環境変数）を編集する際の**手順とチェックリスト**をまとめる。キー一覧・スコープ表・permission/sandboxの構造など詳細リファレンスは同梱の [settings.md](settings.md) を参照。

## 編集手順

1. **スコープを決める** — 個人の好みなら`~/.claude/settings.json`（User）、チーム全員に効かせたいなら`.claude/settings.json`（Project、gitにコミットされる）、自分だけ・このプロジェクト限定なら`.claude/settings.local.json`（Local、gitignore対象）。判断に迷ったら settings.md の「どのスコープを使うべきか」を確認。
2. **既存ファイルを読んでから編集する** — 各scopeのファイルは無ければ新規作成、あれば既存のJSONを壊さないようマージする形で編集する。
3. **キーを確認する** — settings.md の「よく使う設定キー」表に無いキーは、Claude Codeの学習データが古い可能性があるため**claude-code-docsスキル**で公式ドキュメントを確認してから使う（CLAUDE.mdのルールで必須）。
4. **permissionsを追加する場合** — `allow`/`ask`/`deny`のどれに入れるか、ルール構文（`Tool`または`Tool(specifier)`）を settings.md で確認。評価順は**deny → ask → allow**。
5. **hooksを追加する場合** — 本スキルの範囲外。**writing-hooksスキル**を使う（イベント選定・安全な書き方のチェックリストあり）。
6. **JSONとして妥当か確認する** — 編集後は該当ファイルをパースできるか確認する。User/Project/Local設定は不正なJSONだと**ファイル全体が拒否**される（Managed設定だけ該当エントリのみ無視される寛容な挙動）。
7. **反映タイミングを伝える** — `permissions`/`hooks`/`env`などは再起動不要で反映される。`model`と`outputStyle`は次回起動（または`model`は`/model`、`outputStyle`は`/clear`）まで反映されない。ユーザーに再起動が必要か伝える。

## チェックリスト

- [ ] Project scope (`.claude/settings.json`)に書く前に、チーム全員に影響することを認識しているか確認する（個人設定ならUser/Local）
- [ ] `defaultMode: "auto"`はProject/Local設定から書いても無視される（User設定`~/.claude/settings.json`に置く必要がある）
- [ ] permissionsルールは複数スコープに書くと**マージされる**（他の設定キーのような上書きではない）
- [ ] 秘密情報（APIキー・トークン）は`env`に直書きせず、`apiKeyHelper`等のヘルパースクリプト経由か、シェル側の環境変数を使う
- [ ] Windows環境（このマシン）でシェル系フックやコマンドを設定に書く場合、パスの区切りやクオートに注意（詳細は writing-hooksスキルのWindows注意点を参照）
- [ ] `.claude/settings.local.json`を手動で作成した場合は、自分で`.gitignore`に追加する（Claude Codeが自動作成した場合は自動でgitignoreされる）
- [ ] サンドボックス（`sandbox.*`）や`disableBypassPermissionsMode`などセキュリティに関わる設定は、変更前にユーザーに意図を確認する

## 困ったときは

1. まず同梱の [settings.md](settings.md)（スコープ表・permissions構文・sandbox構造・よく使う設定キー・環境変数の抜粋）を確認する。
2. それでも解決しない、載っていないキーを使いたい、または仕様が変わっている可能性がある場合は**claude-code-docsスキル**で最新の公式ドキュメント（`code.claude.com`）を参照する。
3. hooksの作成・編集は**writing-hooksスキル**、スキル自体の作成は**writing-skillスキル**を使う。
