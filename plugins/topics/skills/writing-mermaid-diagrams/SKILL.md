---
# 同梱ファイル: renderer-differences.md（表示環境ごとの差異）/ readability-techniques.md（見やすさ・メンテしやすさのテクニック）
# skill-search（discovering-skills経由）で確認済み: このリポジトリにMermaid固有の既存スキルはなし（2026-08時点）
# writing-skill-webの判断（静的スナップショット vs 動的検索/取得）: mermaid.js.orgはllms.txt/llms-full.txtを公開していない
# （https://mermaid.js.org/llms.txt・llms-full.txt とも2026-08-10時点で404）ため静的スナップショットの型は使わず、
# 動的検索/取得パターンを採用（tav-lit/tav-cliへ委譲。WEB検索クライアントを自前実装しない）
# requires_env(TAVILY_API_KEY)はtav-lit/tav-cli経由の任意依存。未設定でも本文の静的な記述だけで大半は足りる
name: writing-mermaid-diagrams
description: Use when writing or editing Mermaid diagrams (flowchart, sequence, class, state, ER, etc.) in Markdown files, SKILL.md docs, PR descriptions, or Claude Artifacts. Covers two failure modes that plain Mermaid knowledge misses — diagrams that render differently (or break) across VS Code preview / Mermaid Live Editor / GitHub / Claude Artifacts, and diagrams that are technically valid but hard to read (crossing edges, unlabeled arrows, oversized graphs) or hard to maintain (unstable node IDs, no comments).
meta:
  tag: []
  requires_repo_tools: none
  requires_env: TAVILY_API_KEY
  dependencies: none
  requires_install: none
  requires_hooks: none
  requires_skills: tav-lit, tav-cli
  status: experimental
  description: no description
  version: 1.1.0
# このスキル自身はMermaid公式ドキュメントのミラーを持たない。理由と仕組みは次の通り。

# - `mermaid.js.org`は`llms.txt`/`llms-full.txt`（AI向けの索引・全文ダンプ）を公開していない（2026-08-10時点で両方404）。そのため`langchain-docs`/`openrouter-docs`スキルが使う「ダウンロードスクリプト同梱＋freshnessチェック」の型（静的スナップショットパターン、詳細は`writing-skill-web`スキル参照）は使わない。
---

# Mermaid図の作成

Mermaid記法自体は知っていても、「どこで見るか」で結果が変わることと、「文法的に正しい」ことと「読みやすい」ことは別問題である点を見落としがち。このスキルはその2点を補う。

## 手順

1. **図を描く前に、どのレンダラーで見られるかを決める** — VS Codeのプレビューだけで見るのか、GitHubのPR/README上で見るのか、Mermaid Live Editorで作って別の場所に貼るのか、Claude Artifactsに埋め込むのか。複数のレンダラーで見られるなら、その全部を洗い出したうえで手順2へ進む。
2. **複数のレンダラーをまたぐ場合、または挙動が怪しい場合は [renderer-differences.md](renderer-differences.md) を読む** — VS Code / Mermaid Live Editor / GitHub / Claude Artifactsの間でバージョン差・セキュリティレベル差により見え方が変わる具体的なポイントをまとめている。1つのレンダラーでしか見られない単純な図なら読み飛ばしてよい。
   - **このファイルはスナップショットであり、自動更新されない。** バージョン番号・拡張機能名など「変わりうる事実」の記述を鵜呑みにせず疑わしいと感じたら、手順3の要領で`tav-cli`（`tav search`）に再確認させる。
3. **図を書く（または直す）**
   - [readability-techniques.md](readability-techniques.md) の技法（方向の選び方、エッジの間引き、subgraphの使い方、ノードID設計、ラベル付け、コメント）を当てはめる
   - 文法自体が不安、または最新の構文・変更点を確認したい場合は、**学習データの記憶だけで書かず**、公式Diagram Syntaxリファレンス(`https://mermaid.js.org/intro/syntax-reference.html`)を`tav-lit`スキルで取得する（既知の1URLの本文取得はこのスキルが適任。`mermaid.js.org`はllms.txt/llms-full.txtを公開していないため、このスキル自体は静的スナップショットを同梱せず、都度`tav-lit`/`tav-cli`に頼る）
   - 特定の図の種類（`sequenceDiagram`, `classDiagram`, `erDiagram`等）の詳しい構文や、直近のMermaidリリースでの変更点を横断的に調べたい場合は`tav-cli`（`tav search`/`tav search-extract`、`mermaid.js.org`へのドメイン絞り込みを推奨）を使う
4. **実際にレンダリングして確認する** — 文法エラーが出ないことと、意図通りの見た目（交差なし・読める文字サイズ）になっていることは別。少なくとも1つのレンダラー（VS Codeのプレビュー、または[mermaid.live](https://mermaid.live)）で目視確認する。複数のレンダラーで見られる図なら、手順1で洗い出したレンダラーそれぞれで確認する。
5. **大きすぎる/複雑すぎると感じたら、無理に1枚に収めず分割する** — 詳細は[readability-techniques.md](readability-techniques.md)の分割の節。

## 最新情報の取得（このスキルが「陳腐化」しないための仕組み）

- 構文・最新挙動を確認したくなったその場で`tav-lit`（1URL）/`tav-cli`（キーワード検索・複数URL）に取得を委譲する（動的検索/取得パターン）。このスキルはWEB検索クライアントを自前実装しない。
- [renderer-differences.md](renderer-differences.md)自体は執筆時点（2026-08-10）のスナップショットとして残す。これは「調べ直す起点」であって「常に正しい最終真実」ではない。VS Codeのバージョン・拡張機能の統合状況など変わりやすい記述を見つけたら、`tav-cli`（`tav search "VS Code mermaid markdown preview 20XX"`のような形）で現在の状態を再確認し、大きく変わっていたら本ファイルを更新する。

## このスキルの対象外

- **Claude ArtifactsのHTML内で、Mermaidではなく手描きのSVGで図を描きたい場合** — ダイアグラムそのものの設計原則（何を描くべきか、比較の見せ方、矢印にラベルを付ける等）は`artifact-diagramming`スキルと共通するが、そちらはinline SVGの技法（`viewBox`・`currentColor`でのテーマ対応・`<marker>`等）を扱う別スキル。ArtifactのHTML内でどちらの手法を使うか自体で迷ったら`artifact-diagramming`を先に読む。
- **棒グラフ・折れ線グラフなど数値データの可視化** — Mermaidの`pie`/`xychart-beta`程度の単純なものはこのスキルの範囲内だが、本格的なデータビジュアライゼーションは`dataviz`スキルの領分。
