# diagnosing-actions

GitHub Actions の失敗を、run / job の URL または PR 番号から読み取り専用で特定するスキル。

`coding/skills/review` と同じ発想で、長いログを会話に出さず `temp/actions/` へ切り出す。まず `INDEX.md` を読み、表に出た失敗ジョブのファイルだけを開く。

再実行、`gh run watch`、コメント、merge はしない。それらを含む PR 操作は `skills/plugins/coding/skills/pr-check` の範囲。

## ディレクトリ

```
skills/diagnosing-actions/
├── SKILL.md              # 実行時の手順
├── actions_report.py     # gh から失敗ジョブを取得し INDEX と jobs/ を書く
├── README.md
└── tests/test_actions_report.py
```

## 出力

```
temp/actions/<timestamp>_pr123/INDEX.md
temp/actions/<timestamp>_pr123/jobs/001_discover.md
temp/actions/<timestamp>_run99/jobs/001_discover_part01.md
```

- 1ファイルはおおよそ 300 行。超えるときは `## step:` の境目で `part` に分ける
- 各 step は `##[error]` や `error:` などの周辺だけを残す。マーカーが無い step は末尾だけを残す
- annotation は failure をすべて、warning は少数だけ載せる
- `cancelled` は他ジョブの巻き添えが多いので、本物の failure があるときは INDEX に名前だけ書く。cancelled しか無いときはログを取る
- 標準出力は INDEX のパスと、失敗ジョブごとの先頭エラーだけ

## 直接実行

```bash
python skills/plugins/cicd/skills/diagnosing-actions/actions_report.py https://github.com/OWNER/REPO/actions/runs/123
python skills/plugins/cicd/skills/diagnosing-actions/actions_report.py 123 --gh-repo OWNER/REPO
python skills/plugins/cicd/skills/diagnosing-actions/actions_report.py run:123 --gh-repo OWNER/REPO
```

`gh` が無い、または未認証のときはエラーで終了する。

## テスト

```bash
uv run pytest skills/plugins/cicd/skills/diagnosing-actions/tests
```
