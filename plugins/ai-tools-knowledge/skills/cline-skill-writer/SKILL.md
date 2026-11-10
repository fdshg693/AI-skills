---
# 詳細仕様は同階層の skills-reference.md を必要時だけ読む。最終フォールバックは cline-docs スキルで公式 docs.cline.bot を確認する。
name: cline-skill-writer
description: Cline 用スキルを新規作成・編集するためのメタスキル。Use when designing or updating Cline SKILL.md files, skill descriptions, supporting docs/scripts/templates, or deciding whether an instruction belongs in a Skill vs Rule.
user-invocable: true
disable-model-invocation: false
meta:
  tag: []
  requires_repo_tools: none
  requires_env: none
  dependencies: none
  requires_install: none
  requires_hooks: none
  requires_skills: cline-docs, cline-rule-writer
  status: stable
  description: no description
  version: 1.0.1
---

# Cline Skill Writer

Cline 用の `SKILL.md` を作る・直すときの実践ガイド。Cline は基本的な Markdown や YAML は理解している前提で、ここでは**落とし穴と判断基準**だけを優先する。

詳細仕様（配置場所、公式フィールド、ロード順、補助ファイル、例）は必要になった時だけ [skills-reference.md](skills-reference.md) を読む。仕様変更が疑わしい場合の最終フォールバックは **cline-docs スキル**で `https://docs.cline.bot/customization/skills` を確認する。

## まず判断すること

1. **Skill にすべきか**
   - 繰り返し使う「手順・判断プロセス・専門ワークフロー」なら Skill。
   - 常に守る永続指示やプロジェクト規約なら Rule（必要なら `cline-rule-writer`）。
   - 一回限りの依頼、単なるメモ、巨大な仕様書の丸写しは Skill にしない。
2. **既存スキルで足りるか**
   - `.agents/skills/`、必要に応じて `.cline/skills/` / `.clinerules/skills/` / `.claude/skills/` を確認する。
   - 似たスキルがあるなら新規より統合・分割・description 改善を優先する。
3. **読み込みコストを分けるか**
   - `SKILL.md` は実行時に読む短い判断・手順。
   - 詳細、表、長い例、トラブルシュートは同階層の別ファイルへ逃がす。

## 作成・編集フロー

1. **名前を決める**
   - `name` はディレクトリ名と完全一致。小文字 kebab-case。
   - `helper`、`misc`、`tools` のような用途不明名は避ける。
2. **description を書く**
   - 「何をするか」+「いつ使うか」を具体的に書く。
   - Cline の自動起動判断に使われるため、ユーザーが言いそうな語句・対象ファイル・ドメインを含める。
   - ただし本文の手順要約を詰め込みすぎない。長い description は誤起動と読み飛ばしの原因。
3. **本文を前倒しで書く**
   - Cline は順に読む。最重要の判断基準・共通ケースを先に置く。
   - 「必要なら調べる」ではなく、**いつ何を読むか**を明記する。
4. **補助ファイルに逃がす**
   - 5k tokens を超えそうな本体、100行を超えるリファレンス、詳細な例は別ファイル。
   - 参照先は `skills-reference.md` のように内容が分かる名前にする。
5. **検証する**
   - description で想定どおり起動しそうか。
   - `name` とディレクトリ名が一致しているか。
   - 参照リンクが同階層から解決できるか。
   - Rule にすべき内容を Skill に混ぜていないか。

## ベストプラクティス

- **Cline に自明なことを書かない**: Markdown の書き方、一般論、過剰な精神論は削る。
- **迷う箇所だけ固定する**: 成果物、優先順位、禁止事項、フォールバック先を明確にする。
- **本体は短く、参照は遅延**: `SKILL.md` には実行判断だけ。詳細はリンクし、必要時だけ `read_file` する。
- **具体例は少数精鋭**: 例は Cline の迷いを減らすために置く。網羅表はリファレンスへ。
- **description をテスト対象にする**: 「どの依頼文で起動してほしいか」を逆算して書く。
- **スクリプトは決定的処理だけ**: 検証、変換、取得などに限定。判断そのものを壊れやすいスクリプトへ押し込まない。
- **パスは `/` で書く**: Windows 環境でもドキュメント中のパスは原則 forward slash。

## よくある落とし穴

- `name` とディレクトリ名がズレて、スキルとして認識・管理しづらくなる。
- description が「便利なスキルです」程度で、自動起動しない。
- description に手順を詰めすぎて、Cline が本文を読む前に誤った判断をする。
- 常時適用すべき規約を Skill にしてしまい、必要な場面で読まれない。
- `SKILL.md` に詳細を全部入れて重くなり、肝心の手順が埋もれる。
- 補助ファイルへのリンクだけ置き、**いつ読むべきか**を書いていない。
- Cline 公式仕様と Claude Code 独自仕様を混同する。Claude Code 由来の項目は、Cline で使う前に [skills-reference.md](skills-reference.md) または cline-docs で確認する。

## 出力時のチェックリスト

- [ ] 配置先ディレクトリと `name` が一致している
- [ ] description が「何をするか」「いつ使うか」を含む
- [ ] `SKILL.md` は実行時に必要な内容だけに絞られている
- [ ] 詳細リファレンス・長い例・仕様表は別ファイルに分離されている
- [ ] 補助ファイルを読む条件が本文に書かれている
- [ ] Rule / Memory Bank / 一回限りの依頼と混同していない
- [ ] 仕様に不安がある場合のフォールバックとして cline-docs を案内している

## 困ったとき

1. 同階層の [skills-reference.md](skills-reference.md) を読む。
2. Rule との切り分けで迷うなら `cline-rule-writer` を使う。
3. Cline の公式仕様・配置場所・フィールドが変わっていそうなら、最終フォールバックとして **cline-docs スキル**を使い、`customization/skills` を確認する。
