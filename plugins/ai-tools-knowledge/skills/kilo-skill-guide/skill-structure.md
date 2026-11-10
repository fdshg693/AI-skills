# Skill構成 詳細

出典: https://kilo.ai/docs/customize/skills

## 推奨構成

```text
.kilo/skills/my-skill/
├── SKILL.md          # 発見・起動判断・最小ワークフロー
├── reference.md      # APIや設定の詳細
└── examples.md       # 具体例・テンプレート
```

`SKILL.md`を短く保つことで、Skillの起動判断と必要時の詳細参照を分けられる。仕様表や多数の例を本文へ詰め込まない。

## 責務の境界

- `AGENTS.md`: 常時守るプロジェクト規約、構成、禁止事項
- `kilo.jsonc`の`instructions`: Kilo固有のルール、glob、URL、読み込み順序
- Skill: 依頼に応じて使う作業手順・専門知識
- Agent prompt: 特定agentの役割、人格、作業手順、権限と組み合わせる指示

プロジェクト全体で必ず適用したい内容をSkillに隠さない。逆に、特定の作業だけで必要な手順をAGENTS.mdへ常時注入しない。

## 保守

- 参照ファイルを追加したら`SKILL.md`から相対リンクする。
- 公式仕様が変わり得る項目は、公式URLと確認日を記録する。
- 外部スクリプトや依存関係を含める場合は、frontmatterのメタデータと本文に明記する。
- Skill内の命令はユーザー要求やプロジェクトの安全制約を上書きしない。
