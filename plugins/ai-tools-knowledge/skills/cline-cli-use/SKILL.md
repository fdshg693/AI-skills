---
name: cline-cli-use
description: Use when delegating a coding or analysis task to the Cline CLI (`cline` command) as a one-shot, non-interactive worker — for example offloading implementation, refactoring, review, or repository exploration to Cline from another agent. Assumes an active Cline Pass subscription as described at https://docs.cline.bot/getting-started/clinepass and uses Cline Pass model IDs; if using another provider, adjust `--model` values appropriately. Not for looking up CLI flags or docs (use cline-cli-docs / cline-docs for that), and not for interactive TUI sessions.
user-invocable: true
disable-model-invocation: true
allowed-tools: Bash(cline *)
# 前提: Cline CLI（`cline`コマンド）がインストール済みで、Cline Pass加入または利用するprovider/model/APIキーが設定済みであること。未設定なら `cline auth` で設定する。
# 依存: cline-cli-docs（インストール済みCLIのフラグ一次情報）／cline-docs（docs.cline.bot最新情報）。CLI仕様が変わっていそうな場合は先に確認する。
# disable-model-invocation: --auto-approve true が既定で、書き込み・シェル実行などの副作用があり得るため、ユーザーの明示呼び出し（/cline-cli-use）に限定する。
meta:
  tag: []
  requires_repo_tools: none
  requires_env: Cline Pass subscription or provider API key configured via `cline auth`
  dependencies: none
  requires_install: cline CLI
  requires_hooks: none
  requires_skills: cline-cli-docs, cline-docs
  status: stable
  description: no description
  version: 1.0.0
---

# CLINE CLI 非対話実行

Cline CLI（`cline` コマンド）を**単発の非対話ワーカー**として使う。ターミナルUI（`--tui` / `-i`）での対話セッション、CLIフラグの調査、公式仕様の確認はこのスキルの対象外（必要なら `cline-cli-docs` / `cline-docs` を使う）。

このスキルを起動したユーザー依頼文そのものを、`cline "<prompt>"` に渡すプロンプトへ要約・具体化して使う。Cline Skills 公式仕様では Claude Code のスラッシュコマンド引数展開に相当する仕組みを確認できないため、本文中のプレースホルダ展開には依存しない。

## 前提条件（自動チェック）

`cline` の状態: !`cline --version 2>&1 && cline config 2>&1 || echo "cline コマンドが見つからない、または設定確認に失敗しました（Cline CLI未インストール、PATH未設定、未認証の可能性）"`

- 「コマンドが見つからない」場合は、Cline CLI のインストールをユーザーに案内する。
- provider / API key / model が未設定または不正な場合は、`cline auth` で設定してから実行する。
- APIキーを一時指定する `--key` / `cline auth --apikey` は秘密情報を履歴・ログに残しやすいため、実値を会話やファイルに出さない。

## 実行の基本形

```bash
cline --model cline-pass/glm-5.2 --thinking high "<prompt>"
```

- Cline CLI は `cline [options] [prompt]` 形式。prompt を渡すと単発実行になり、既定で act mode / auto-approve enabled として開始される。
- モデルはタスクの重さに応じて、軽量タスクは `cline-pass/minimax-m3`、通常作業は `cline-pass/glm-5.2`、きわめて高度な作業は `cline-pass/kimi-k3` を使う。
- 思考レベルは常に `--thinking high` 固定。`xhigh` などには上げない。
- provider は既定の設定（Cline Pass）を使う。別プロバイダを利用する場合は、そのプロバイダで有効なモデルIDへ `--model` 値を適宜変更し、明示が必要な環境だけ `--provider <id>` を追加する。
- 作業ディレクトリを固定したい場合は `--cwd <path>` を付ける。
- 結果を後続処理で扱いたい場合のみ `--json` を付ける。人間が読む最終回答だけなら既定の styled text でよい。

## モデルの使い分け

| タスクの性質                                                                                                         | モデル                               | `--thinking` |
| -------------------------------------------------------------------------------------------------------------------- | ------------------------------------ | ------------ |
| 軽量タスク（短い調査、要約、小規模な確認、単純な修正案作成など）                                                     | Minimax M3 (`cline-pass/minimax-m3`) | `high`       |
| 通常作業（実装・調査・リファクタ・レビューなど）                                                                     | GLM 5.2 (`cline-pass/glm-5.2`)       | `high`       |
| きわめて高度な作業（難しい設計判断、複雑なバグ解析、セキュリティ・データ損失・大規模変更など失敗コストが高いタスク） | Kimi K3 (`cline-pass/kimi-k3`)       | `high`       |

```bash
cline --model cline-pass/minimax-m3 --thinking high "<light prompt>"
cline --model cline-pass/glm-5.2 --thinking high "<prompt>"
cline --model cline-pass/kimi-k3 --thinking high "<hard prompt>"
```

- モデルは「軽量 / 通常 / きわめて高度」の3段階だけで選ぶ。迷ったら通常作業として `cline-pass/glm-5.2` を使う。
- Cline Pass 以外の provider を使う場合は、この表のモデルIDをその provider の同等モデルへ読み替える。
- `model not found` や `invalid thinking level` が出た場合だけ、`cline-cli-docs` でインストール済みCLIのヘルプを確認し、必要ならこの `SKILL.md` のモデルIDまたはフラグを更新する。毎回の事前確認は不要。

## 権限・副作用の扱い

Cline CLI の prompt 実行は、ヘルプ上 `--auto-approve <boolean>` の既定値が `true`。つまり、委譲先がファイル編集やシェル実行を確認なしで進める可能性がある。

- 書き込み・コマンド実行を許可する実装タスクでは既定のままでよい。
- 読み取り専用の調査・要約では、必ず `--auto-approve false` を付けるか、プロンプト内で「読み取り専用。ファイル作成・編集・削除、コマンド実行による変更は禁止」と明示する。
- 依頼元も依頼先も同じリポジトリのルールを読む可能性があるため、ログ生成・成果物作成などの副作用的なプロジェクト指示が二重に実行されないよう、必要なら「この依頼で明示した成果物以外は作らない」と書く。
- 危険な操作（削除、認証情報、外部課金、デプロイ、DB変更など）を含むタスクは、Cline CLIへ丸投げせず、事前にユーザー確認を取る。

## よく使う実行例

### 通常の実装タスク

```bash
cline --cwd . --model cline-pass/glm-5.2 --thinking high "READMEの手順に従い、lintが通るように該当ファイルを修正して。変更点と検証結果を最後に要約して。"
```

### 読み取り専用の調査

```bash
cline --cwd . --auto-approve false --model cline-pass/minimax-m3 --thinking high "読み取り専用で、認証処理の入口と関連ファイルを調査して要約して。ファイル作成・編集・削除は禁止。"
```

### 難しいバグ解析

```bash
cline --cwd . --model cline-pass/kimi-k3 --thinking high "再現条件が曖昧な競合バグを調査して、原因候補、根拠ファイル、最小修正案、検証方法を提示して。必要な修正だけ実施して。"
```

## 実行後の確認

1. Cline の最終回答から、変更ファイル・実行コマンド・未完了事項を確認する。
2. 依頼元側でも `git diff`、テスト、lint、型チェックなどを必要に応じて実行し、委譲先の説明を鵜呑みにしない。
3. 出力が不十分なら、同じセッション継続ではなく、追加条件を明示した新しい `cline ... "<prompt>"` を実行する。

## 関連スキル

- `cline-cli-docs` — `cline` コマンドの最新ヘルプ、オプション、サブコマンド確認。
- `cline-docs` — docs.cline.bot の公式仕様確認。
