---
name: using-playwright-cli
description: Drives a browser from the shell with `playwright-cli` (`npx playwright cli`), grounded in a local snapshot of the skill microsoft/playwright itself ships. Use when asked to open / navigate / click / fill / snapshot a page, take screenshots or PDFs, mock requests, record a trace or video, manage browser sessions, cookies or storage state, or run and debug Playwright tests from the command line; when first exploring an unfamiliar site (robots.txt / sitemap recon before opening a browser); when turning a browser procedure into a script; also when asked what `playwright-cli install --skills` installs.
allowed-tools: Bash(uv run ${CLAUDE_SKILL_DIR}/*.py *) Bash(playwright-cli:*) Bash(npx:*) Bash(npm:*)
# 同梱ファイル:
#   - download_playwright_cli_skill.py: upstream スナップショット取得（!`` で起動時に実行）
#   - output/playwright-cli/: upstream の playwright-cli スキル本体（生成物。手で編集しない）
#   - references/: 自前の運用手順（upstream ではなく実測が根拠）
#   - README.md: メンテナ向け。取得対象の増やし方、設計意図
# 暗黙の前提:
#   - `gh` と `uv` が PATH にあること（公開リポジトリなので未認証でも動くが、レート制限回避のため `gh auth login` 済みが望ましい）
#   - `playwright-cli` 本体は別途必要（未導入なら本文の Installation 節に従う）
# 設計メモ:
#   - この SKILL.md は薄いルーター。実体は output/playwright-cli/ 配下に一段深く置く。
# 依存スキル: なし（pwq/pwdo 前提の手順は my-tools の browser-context-tools。入っていれば使う任意の参照）
meta:
  tag: []
  requires_repo_tools: none
  requires_env: none
  dependencies: gh, uv
  requires_install: npm install -g @playwright/cli@latest
  requires_hooks: none
  requires_skills: none
  status: experimental
  description: playwright-cli 同梱スキルのミラーと、偵察・スクリプト化の自前手順へのルーター
  version: 1.0.0
---

!`uv run "${CLAUDE_SKILL_DIR}/download_playwright_cli_skill.py"`

# playwright-cli でブラウザを操作する

記憶ではなく `${CLAUDE_SKILL_DIR}/output/`（microsoft/playwright `main` が同梱しているスキルのスナップショット）を根拠にする。
上のコマンドで取得済み。エラーが出ていた場合は原因（`gh` 未インストール等）を伝えてから続行する。

## まずこれを読む

[output/playwright-cli/playwright-cli-skill.md](output/playwright-cli/playwright-cli-skill.md)
— `playwright-cli install --skills` が配る skill 本体（upstream の `SKILL.md`。ここでは別名で保存している）。
コマンド一覧、snapshot と ref による要素指定、セッション、`--raw` / `--json`、インストール手順はすべてここにある。
**この本文を読んでから実行する。** コマンド名やオプションを記憶で補わない。

## 状況別の入口

ブラウザ操作の前に、自分の状況に当たる行を見る。上から順に、最初に当たった行の参照先を読む。

| 状況                                       | まずやること                                                                                                                                                                                                                                | 見る場所                                                                 |
| ------------------------------------------ | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------ |
| **初見のサイトを渡された**                 | ブラウザを開く前に `.playwright-cli/recon/<host>/INDEX.md` を見る。無ければ `curl` で `robots.txt` → `sitemap.xml` の 2 GET（空振り 15 B、当たれば 745 B で全体像）。1 枚しか無いサイトだと分かったら次の行へ                               | [references/site-recon.md](references/site-recon.md)                     |
| **初見の・大きいページをブラウザで調べる** | `snapshot` / `eval` の生出力をそのまま会話に流さない。`pwq` が入っていれば `browser-context-tools` スキルの手順（実測で 3〜30 %）。無ければ `snapshot` を `> file` に逃がし、必要な部分だけ読む                                             | `browser-context-tools` スキル（任意）                                   |
| **ブラウザ操作の一区間を AI に委譲したい** | `snapshot` を 3 回以上撮る区間か見る（損益分岐）。`pwdo` が入っていれば `browser-context-tools` スキル。**認証が絡む区間は委譲しない**。**コンテキストを汚したくないだけでサブエージェントに投げない**（実測で課金が `pwdo` の 27〜237 倍） | `browser-context-tools` スキル（任意）                                   |
| **ブラウザ手順をスクリプト化する**         | 一括で書き下ろさず、少し書く → 実行 → 手で探索 → 記録から回収して追記、の往復で育てる                                                                                                                                                       | [references/script-cli-roundtrip.md](references/script-cli-roundtrip.md) |
| **認証（ログイン・2FA・CAPTCHA）が絡む**   | エージェントは認証情報に触れない。ユーザーに渡す区間の契約に従う                                                                                                                                                                            | `sharing-browser-with-user` スキル                                       |
| **実験用のサイトが要る**                   | 外部サイトを叩く前に、認証不要・ローカル完結のテストサイトで済まないか見る                                                                                                                                                                  | [references/test-sites.md](references/test-sites.md)                     |

## upstream の個別トピック

本文の末尾から張られている参照先。必要になったものだけ Read する（`output/` をまとめて流さない）。
全体の索引は [output/summary.md](output/summary.md)。

| やりたいこと                                    | 見る場所                                                 |
| ----------------------------------------------- | -------------------------------------------------------- |
| Playwright テストの実行・デバッグ               | `output/playwright-cli/references/playwright-tests.md`   |
| テスト生成（plan / generate / heal）            | `output/playwright-cli/references/test-generation.md`    |
| リクエストのモック（route / unroute）           | `output/playwright-cli/references/request-mocking.md`    |
| 任意の Playwright コード実行（`run-code`）      | `output/playwright-cli/references/running-code.md`       |
| セッション管理（複数ブラウザ、attach / detach） | `output/playwright-cli/references/session-management.md` |
| storage state・cookie・localStorage             | `output/playwright-cli/references/storage-state.md`      |
| trace の取得と閲覧                              | `output/playwright-cli/references/tracing.md`            |
| 動画録画・チャプター・アクション表示            | `output/playwright-cli/references/video-recording.md`    |
| 要素の id / class / data-* など属性の取得       | `output/playwright-cli/references/element-attributes.md` |
| PR に画像・動画を添付する（`gh --attach`）      | `output/playwright-cli/references/pr-attachments.md`     |

## 実行時の注意

- **`.playwright-cli/` を gitignore しておく。** `playwright-cli` の記録・偵察結果・storage state の置き場で、cookie などの認証情報を含みうる。作業するリポジトリの `.gitignore` に無ければ足すようユーザーに伝える
- Windows で URL に `&` を含むときのエスケープは本文の「URLs with `&` on Windows」に従う
- 判断の根拠は常に `output/`（upstream `main` のスナップショット）を使う。手元の Playwright のバージョンと差があれば差として報告する
- 答えるときは `output/` 内の相対パスと上流 URL
  （`https://github.com/microsoft/playwright/blob/main/<元パス>`、元パスは `output/_meta.json`）を示す

## スナップショットの更新

既定では 7 日以内に取得済みならスキップされる。強制再取得:

```bash
uv run "${CLAUDE_SKILL_DIR}/download_playwright_cli_skill.py" --force
```

同梱スキルは Playwright のリリースごとに更新される。バージョン差が問題になりそうなときは `--force` してから答える。
