# Custom Instructions / Rules 詳細

出典: https://kilo.ai/docs/customize/custom-instructions
出典: https://kilo.ai/docs/customize/custom-rules

## 使い分け

Custom Instructionsは個人設定やKiloの全体的な挙動を調整する概念。Custom Rulesはプロジェクト・グローバルの具体的な規則を、ファイルと`instructions`設定で管理する仕組みとして扱う。

## `kilo.jsonc`

`instructions`にはファイルパス、glob、URLを指定できる。

```jsonc
{
  "instructions": [
    ".kilo/rules/formatting.md",
    ".kilo/rules/*.md",
    "./docs/team-guidance.md",
  ],
}
```

VS CodeではSettings → Agent Behaviour → Rulesから管理できる。URLはセッション開始時に取得され、到達不能なら静かにスキップされるため、重要なルールの唯一の保管場所にしない。

## 適用順

公式ページでは、global configのinstructions、project configのinstructionsの順にロードされ、project側が競合時に優先すると説明されている。配列内の順序も意味を持つ。globのfilesystem orderに依存しないよう、重要ルールは個別パスで明示する。

## ベストプラクティス

- ルールをformatting、security、testingなど関心ごとに分割する。
- 常時必要なプロジェクト知識はAGENTS.mdに置き、Kilo固有の列挙・globはinstructionsに置く。
- ルールはMarkdownで見出し、箇条書き、短い例を使う。
- 機密ファイルを読まない規則は具体的なパス・拡張子で書く。ただし権限制御の代替ではない。
- 変更後は新しいsession/taskで反映を確認する。

legacyの`.kilocode/rules/`は互換目的で読み込まれ得るが、新規構成では`.kilo/rules/`と`kilo.jsonc`を優先する。
