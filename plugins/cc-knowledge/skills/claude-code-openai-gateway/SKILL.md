---
# 棲み分け: Claude Code の設定ファイル一般は claude-settings スキル、CLIフラグの正確な一覧は
#   claude-cli-docs スキル、公式ドキュメント本文は claude-code-docs スキル、
#   LiteLLM 側の最新仕様は litellm-docs スキルで確認する。
#   このスキルは「Anthropic Messages 互換ゲートウェイ経由で非Anthropicモデルを使う」構成判断に特化する。
# 前提条件: Docker（Engine起動済み）または LiteLLM を起動できる実行環境、OpenAI の API キー。
#   ゲートウェイを自分で運用せず既存のものへ繋ぐ場合は Docker 不要。
name: claude-code-openai-gateway
description: Use when the user wants Claude Code to run on a non-Anthropic model such as an OpenAI model, or asks about ANTHROPIC_BASE_URL / LLM gateway / LiteLLM proxy setup, per-session vs global model switching, or debugging a Claude Code session that talks to a custom Messages-API-compatible endpoint.
meta:
  tag: []
  requires_repo_tools: none
  requires_env: OPENAI_API_KEY, ANTHROPIC_BASE_URL, ANTHROPIC_AUTH_TOKEN
  dependencies: none
  requires_install: docker, docker compose
  requires_hooks: none
  requires_skills: claude-settings, claude-cli-docs, claude-code-docs, litellm-docs, claude-code-debugging
  status: experimental
  description: LiteLLM等のMessages互換ゲートウェイ経由でClaude CodeをOpenAIモデルで動かすための構成判断と手順
  version: 1.0.0
---

# Claude Code を OpenAI モデルで動かす

Claude Code は Anthropic Messages API しか話さない。OpenAI モデルを使うには、**Messages API 互換のゲートウェイを間に挟み、Claude Code の接続先をそこへ向ける**。Claude Code 側にプロバイダを切り替える設定は存在しない。

```
Claude Code ──/v1/messages──> ゲートウェイ（LiteLLM Proxy 等） ──> OpenAI API
   ANTHROPIC_BASE_URL            Anthropic形式 → OpenAI形式へ変換
   ANTHROPIC_AUTH_TOKEN          model_list の alias でルーティング
```

## まず読むもの

- **とにかくすぐ動かしたい** → [gateway/](gateway/)。`.env` を埋めて `docker compose up -d` するだけの LiteLLM Proxy 一式（compose / config / 単体確認スクリプト）が入っている。
- **実際に設定したい** → [setup.md](setup.md)。ゲートウェイ起動から、グローバル適用・特定スレッドだけの適用・動作確認までの一連の手順が1ファイルに入っている。
- **動かない／挙動が怪しい** → [compatibility-and-troubleshooting.md](compatibility-and-troubleshooting.md)。互換性の境界、既知の無害な診断メッセージ、切り分け手順。

## 構成を決めるときの原則

- **モデル ID は毎回明示する。** カスタム `ANTHROPIC_BASE_URL` 下ではモデル名の意味をゲートウェイが決める。指定しなければ Claude Code は既定の Claude モデル ID を送り、ゲートウェイの `model_list` に無ければ失敗する。`--model` かつ/または `ANTHROPIC_MODEL` で、ゲートウェイの alias と**完全一致する文字列**を渡す。
- **ゲートウェイの公開 alias は Claude Code が送る名前そのものにする。** プロバイダ指定（`openai/...`）はゲートウェイ設定の内側に閉じ込め、クライアントには漏らさない。
- **認証は `ANTHROPIC_AUTH_TOKEN`（`Authorization: Bearer` として送出）を使う。** `ANTHROPIC_API_KEY` と同時に設定しない。ゲートウェイへ渡すのはマスターキーではなく、モデルを限定した仮想キー。
- **秘密情報を `settings.json` の `env` に直書きしない。** シェル環境変数か `apiKeyHelper` 経由にする。上流プロバイダのキーはゲートウェイ側だけが持ち、Claude Code プロセスには渡さない。
- **`drop_params: true` を最初から入れない。** 非対応パラメータを黙って捨てるため、何が本当に非対応なのかが見えなくなる。明確な非互換エラーが出てから、限定的な回避策として採用する。
- **モデルピッカーへの表示を成功条件にしない。** ゲートウェイのモデル探索は ID に `claude` / `anthropic` を含むものだけをピッカーへ追加するため、OpenAI の ID は出てこない。明示指定で動けば正常。

## 適用範囲の選び方

| やりたいこと                             | 方法                                                                       |
| ---------------------------------------- | -------------------------------------------------------------------------- |
| 今のこのスレッド（1回の起動）だけ OpenAI | シェルに環境変数を設定してから `claude` を起動する（既定。影響が閉じる）   |
| このプロジェクトの作業は常に OpenAI      | プロジェクトのシェル設定 or `.claude/settings.json` の `env`（秘密は除く） |
| マシン全体で常に OpenAI                  | `~/.claude/settings.json` の `env` ＋ シェルのプロファイル                 |

判断に迷ったらセッション単位から始める。グローバルに入れると、Anthropic モデルへ戻したいときに変数の解除漏れで混乱しやすい。

## 検証の順序

構成を疑う前に、下から順に切り分ける。上の層を飛ばして「Claude Code が動かない」と判断しない。

1. **上流プロバイダ直叩き** — 該当モデル ID とキーで OpenAI API が 200 を返すか。ここが失敗ならゲートウェイの問題ではない。
2. **ゲートウェイ単体** — `curl` 等で `POST /v1/messages` を叩き、Anthropic 形式の応答・SSE・tool use が返るか。
3. **Claude Code E2E** — 隔離した非対話実行で応答・ストリーミング・ツールループを確認する。

各層の具体的なコマンドと合否基準は [compatibility-and-troubleshooting.md](compatibility-and-troubleshooting.md) を参照。

## 注意

- カスタム base URL では Remote Control など一部機能が使えない。障害と混同しない。
- ゲートウェイのポートは loopback（`127.0.0.1`）にだけ公開する。検証用キーを持つプロキシを LAN へ晒さない。
- ゲートウェイのイメージは `main-latest` ではなくリリースタグ（可能なら digest）に固定する。再現できない構成は切り分けに使えない。
