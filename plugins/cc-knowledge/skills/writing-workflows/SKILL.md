---
# 同梱のworkflows-reference.mdは詳細リファレンス(比較表・制約値・保存場所の解決順序・スクリプトAPI)。
# このファイル自体はDynamic Workflowを実際に作成・編集・レビューする際の判断とベストプラクティス集。
name: writing-workflows
description: Use when creating, editing, or reviewing a Claude Code dynamic workflow (.claude/workflows/*.js orchestration scripts using agent()/pipeline()/parallel()/phase()) — deciding whether a task warrants a workflow, structuring or auditing the script, choosing a save location, and passing args to a saved workflow.
meta:
  tag: []
  requires_repo_tools: none
  requires_env: CLAUDE_CONFIG_DIR, CLAUDE_CODE_SUBAGENT_MODEL, CLAUDE_CODE_DISABLE_WORKFLOWS
  dependencies: none
  requires_install: none
  requires_hooks: none
  requires_skills: claude-mechanisms, writing-subagents, claude-code-docs
  status: stable
  description: no description
  version: 1.0.0
---

# Dynamic Workflow作成のベストプラクティス

Dynamic WorkflowはClaudeが書くJavaScriptオーケストレーションスクリプトで、多数のsubagentをバックグラウンドで動かし1つの結果に統合する機構。通常は手で書かず、プロンプトで依頼して生成させ、良い結果が出たものだけ`.claude/workflows/`に保存して`/<name>`コマンド化する。このスキルは「そのワークフローを作る・編集する・レビューする」際の判断とチェックリストをまとめる。機構そのものの詳細(比較表・制約値・全スクリプトAPI)は同梱の[workflows-reference.md](workflows-reference.md)を参照。

## この機構を使うべきか先に確認する

- 単発の調査・少数ファイルの修正・普通の会話で捌ける規模なら、workflowではなくsubagentやSKILLで十分。**claude-mechanismsスキル**の判断フローを先に通すこと。
- workflowが向くのは: 1回の会話では捌ききれない規模(数十〜数百ファイル)のタスク、同じステップを大量の対象に繰り返すタスク、複数の独立したagentに相互検証させたいタスク(査読・照合)、複数角度からの草案を突き合わせて1つに絞りたいタスク。

## 作成手順(プロンプトで生成させる場合)

1. **依頼する** — 自然言語で「ワークフローを使って」と頼むか、プロンプトに`ultracode`というキーワードを含める。セッション全体で使いたいなら`/effort ultracode`に切り替える。
2. **生成されたスクリプトを確認する** — 実行前の承認画面で`View raw script`を選ぶか、`Ctrl+G`でエディタに開いて中身を読む。特に次を確認する。
   - fan-outする対象(対象ファイル一覧など)を最初の`agent()`呼び出しで動的に取得しているか(ハードコードされていないか)
   - 各`agent()`への指示文が1体ごとに十分具体的か(例: 「監査して」ではなく対象ファイルパスを明示した指示文になっているか)
   - 相互検証が必要なタスクなら、検証専用の`agent()`呼び出しが独立して入っているか(同じagentに「やって、かつ自己チェックして」と頼むのは相互検証にならない)
3. **小さく試す** — 対象を1ディレクトリ・少数issueなどに絞った版でまず走らせ、トークン消費と結果の質を見てから本番規模に広げる。
4. **`/workflows`で進捗を見る** — フェーズごとのagent数・トークン数・経過時間を確認し、想定より肥大化していれば停止する。
5. **良い結果が出たら保存する** — `/workflows`で該当runを選び保存する。チームで使うなら`.claude/workflows/`(プロジェクト・コミット対象)、自分だけなら`~/.claude/workflows/`。同名の場合は常にプロジェクト側が優先される。

## スクリプトを手で書く・編集する場合

生成されたスクリプトを直接いじる、または既存スクリプトをレビューする際の構造:

```javascript
export const meta = {
  name: "audit-routes",
  description: "Audit every route handler for missing auth checks",
};

const found = await agent("List every .ts file under src/routes/.", {
  schema: {
    type: "object",
    required: ["files"],
    properties: { files: { type: "array", items: { type: "string" } } },
  },
});

const audits = await pipeline(found.files, (file) =>
  agent(`Audit ${file} for missing authentication checks.`, { label: file }),
);

return audits.filter(Boolean);
```

- `agent(prompt, options)` — 1体のsubagentを起動する。構造化した値を後段に渡したいなら`options.schema`(JSON Schema)を指定する。進捗画面での表示名は`options.label`。
- `pipeline(list, item => agent(...))` — リストの各要素に対して1体ずつagentを起動し、結果配列を返す(fan-out)。
- `parallel()` / `phase()` — 並列実行のグループ化、進捗画面上のフェーズ分けに使う。詳細は[workflows-reference.md](workflows-reference.md#スクリプトapi)。
- 本体はplain JavaScript + top-level `await`。**分岐・集計・件数カウント・停止条件判定などの決定論的ロジックはスクリプト側のコードに書き、agentへの指示文に「数えて」「判定して」と丸投げしない** — 各`agent()`呼び出しは独立して起動されるため、状態はスクリプト変数で持ち回す。
- 保存済みワークフローへの入力は`args`グローバルで受け取る。呼び出し時に配列・オブジェクトがそのまま渡されるので、スクリプト側でJSON文字列としてパースする必要はない。

## 品質を上げる定番パターン

- **相互検証**: 1体のagentに調査させ、別の独立したagentにその結果を反証させてから採用する(査読・監査タスクで有効)。
- **複数角度からの草案**: 同じお題を複数の独立したagent呼び出しに投げ、その結果を比較・統合する専用agentに渡す。
- **繰り返し収束**: チェック→修正→再チェックをループさせ、「2ラウンド連続で進展なし」等の停止条件をスクリプト側のコードで判定する。

## チェックリスト

- [ ] このタスクは本当にworkflow規模か(claude-mechanisms/subagentで足りないか)を確認した
- [ ] fan-out対象を動的に取得しており、ハードコードしていない
- [ ] 相互検証が必要なタスクでは、検証用の`agent()`呼び出しを独立させている(自己申告に頼っていない)
- [ ] 小規模な対象でまず試し、トークン消費を確認してから本番規模に広げた
- [ ] 決定論的なロジック(件数集計・停止条件判定など)はagentへの指示文ではなくスクリプトのJavaScriptで書いている
- [ ] チームで再利用するものは`.claude/workflows/`(コミット対象)、個人用は`~/.claude/workflows/`に保存した
- [ ] 大規模runを常用するなら`/config`のDynamic workflow size guidelineを設定し、runの規模を制御している

## 困ったときは

1. まず同梱の[workflows-reference.md](workflows-reference.md)(比較表・制約値・保存場所の解決順序・コスト管理・無効化設定など)を確認する。
2. workflowを使うべきか自体で迷う場合は**claude-mechanismsスキル**。
3. workflowが呼び出すsubagentそのものの設計(ツール制限・description・model選択など)は**writing-subagentsスキル**。
4. 執筆時点から仕様が変わっている可能性がある、または挙動が期待と違う場合は**claude-code-docsスキル**で最新の公式ドキュメント(`code.claude.com`)を確認する。
