# Context 詳細

出典: https://kilo.ai/docs/customize/context/context-condensing
出典: https://kilo.ai/docs/customize/context/kilocodeignore

## 指示とコンテキストは別物

AGENTS.mdやinstructionsは、agentがどう振る舞うかを定義する指示。コンテキスト機能は、どのファイル・履歴・コード情報を会話へ含めるかを調整する。大きな指示ファイルでコンテキスト不足を解決しようとしない。

## 実践方針

- 必要なファイルだけを明示的にReadし、巨大な生成物やvendorをむやみに含めない。
- `.kilocodeignore`はインデックスやコンテキストから除外したいパスに使う。秘密情報の保護はignoreだけに依存せず、権限・secret管理も併用する。
- Context Condensingは長い会話を圧縮して継続する仕組みであり、永続的なプロジェクト知識の保存先ではない。
- 重要な決定事項はAGENTS.mdまたは通常の設計資料へ明示的に記録する。

仕様やignoreのglob挙動はクライアントの現行ドキュメントを確認してから設定する。除外しすぎると、agentが必要なファイルを見つけられない。
