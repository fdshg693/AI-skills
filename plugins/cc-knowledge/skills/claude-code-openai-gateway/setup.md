# セットアップ手順（ゲートウェイ起動 → Claude Code 接続 → 確認）

ゼロから、Claude Code が OpenAI モデルで応答するまでの一連の手順。LiteLLM Proxy を例にする。

## 目次

- [0. 事前確認](#0-事前確認)
- [1. ゲートウェイを用意する](#1-ゲートウェイを用意する)
- [2. 起動と単体確認](#2-起動と単体確認)
- [3-A. このスレッドだけ OpenAI にする](#3-a-このスレッドだけ-openai-にする)
- [3-B. グローバルに OpenAI にする](#3-b-グローバルに-openai-にする)
- [4. 動いていることの確認](#4-動いていることの確認)
- [5. 元に戻す](#5-元に戻す)

---

## 0. 事前確認

先に潰しておかないと、後段の失敗をゲートウェイのせいだと誤診する。

1. **上流が生きているか。** 使いたいモデル ID とキーで、OpenAI API に直接 1 回投げて 200 を確認する。モデル ID のタイポ・アカウント権限・レート制限はここで出る。
2. **既存の Anthropic 系環境変数を確認する。** `ANTHROPIC_API_KEY`、`ANTHROPIC_BASE_URL`、`ANTHROPIC_AUTH_TOKEN`、`ANTHROPIC_MODEL`、クラウドプロバイダ選択変数（Bedrock/Vertex 系）、カスタムヘッダー系が既に設定されていないか。残っていると競合する。
3. **Docker Engine が起動しているか。** クライアントが入っていても daemon が落ちていることがある。

## 1. ゲートウェイを用意する

すぐ動かせる雛形が [gateway/](gateway/) にある（`.env.example` をコピーして `docker compose up -d`）。以下は、そこで何を書いているかの説明。自分で置く場合は Git 管理外のディレクトリ（`temp/` 配下など）に 3 ファイルを置く。

**`config.yaml`** — 公開する alias を、Claude Code へ渡すモデル ID と完全一致させる。

```yaml
model_list:
  - model_name: gpt-5.6-luna # ← Claude Code に --model で渡す文字列
    litellm_params:
      model: openai/gpt-5.6-luna # ← 実体。プロバイダ指定はここに閉じ込める
      api_key: os.environ/OPENAI_API_KEY

general_settings:
  master_key: os.environ/LITELLM_MASTER_KEY
```

必要な alias だけを列挙する。意図しないモデルを公開しない。`drop_params` は書かない（[SKILL.md](SKILL.md) の原則を参照）。

**`compose.yaml`** — loopback だけに公開し、イメージは digest で固定する。

```yaml
services:
  litellm:
    image: docker.litellm.ai/berriai/litellm:<VERSION>@sha256:<DIGEST>
    ports:
      - "127.0.0.1:4000:4000" # loopback限定。"4000:4000" と書かない
    env_file:
      - .env
    volumes:
      - ./config.yaml:/app/config.yaml:ro
    command: ["--config", "/app/config.yaml"]
```

**`.env`** — 秘密はここだけに置き、Git 管理しない。

```
OPENAI_API_KEY=<上流のキー>
LITELLM_MASTER_KEY=<ランダム生成した値>
```

`LITELLM_MASTER_KEY` はその場で生成する。使い回さない。

## 2. 起動と単体確認

```bash
docker compose config --quiet          # 構文とenv参照の解決を先に確認
docker compose up -d
```

起動後、Claude Code を繋ぐ前に単体で確認する。

```bash
curl -s http://127.0.0.1:4000/health/liveliness
curl -s http://127.0.0.1:4000/v1/models -H "Authorization: Bearer $LITELLM_MASTER_KEY"
```

`/v1/models` が `config.yaml` に書いた alias だけを返すこと。ここに余計なモデルが出るなら設定を直す。

さらに Messages 契約を1回叩いておく（Claude Code の失敗と切り分けるための基準線になる）。

```bash
curl -s http://127.0.0.1:4000/v1/messages \
  -H "Authorization: Bearer $LITELLM_MASTER_KEY" \
  -H "anthropic-version: 2023-06-01" \
  -H "content-type: application/json" \
  -d '{"model":"gpt-5.6-luna","max_tokens":64,"messages":[{"role":"user","content":"reply with OK"}]}'
```

Anthropic 形式（`type: message` と `content[].text`）が返れば通っている。

**クライアントに渡すキー**: 恒常運用ではマスターキーを Claude Code へ渡さず、LiteLLM の仮想キーを発行してモデルを限定する。使い捨ての検証ならマスターキーでもよいが、終了時に破棄する。

## 3-A. このスレッドだけ OpenAI にする

**新しいシェルを開き**、そのプロセスにだけ環境変数を設定してから `claude` を起動する。シェルを閉じれば元に戻る。これが既定の方法。

PowerShell:

```powershell
$env:ANTHROPIC_BASE_URL  = "http://127.0.0.1:4000"
$env:ANTHROPIC_AUTH_TOKEN = "<ゲートウェイの仮想キー>"
Remove-Item Env:ANTHROPIC_API_KEY -ErrorAction SilentlyContinue  # 併存させない
claude --model gpt-5.6-luna
```

Git Bash:

```bash
export ANTHROPIC_BASE_URL="http://127.0.0.1:4000"
export ANTHROPIC_AUTH_TOKEN="<ゲートウェイの仮想キー>"
unset ANTHROPIC_API_KEY
claude --model gpt-5.6-luna
```

- `--model` は毎回渡す。省略すると既定の Claude モデル ID が送られ、`model_list` に無ければ失敗する。
- セッション途中で切り替えたい場合も `/model <alias>` で同じ alias 文字列を渡す。
- `ANTHROPIC_MODEL` を設定しておけば `--model` を省略できるが、どのモデルで動いているか見失いやすいので明示を勧める。

## 3-B. グローバルに OpenAI にする

マシン全体で常時使う場合。**秘密情報を `settings.json` に書かない**ことだけは崩さない。

1. `~/.claude/settings.json` に、秘密でない値だけを入れる。

```json
{
  "env": {
    "ANTHROPIC_BASE_URL": "http://127.0.0.1:4000",
    "ANTHROPIC_MODEL": "gpt-5.6-luna"
  }
}
```

2. トークンはシェルのプロファイル（`$PROFILE` / `.bashrc`）で `ANTHROPIC_AUTH_TOKEN` として設定するか、`apiKeyHelper` に取得スクリプトを指定する。
3. `ANTHROPIC_API_KEY` が環境やプロファイルに残っていれば消す。
4. ゲートウェイを常時起動にする（`restart: unless-stopped` 等）。落ちていると全スレッドが失敗する。

`settings.json` の編集手順・スコープの詳細は **claude-settings スキル**を参照。

プロジェクト単位にしたい場合は `.claude/settings.json`（コミットされる、チーム全員に効く）へ同じ `env` を置くが、チームの他メンバーのゲートウェイ有無を確認してからにする。

## 4. 動いていることの確認

「応答が返った」だけでは、Claude モデルにフォールバックしていないことを保証できない。次の2点を突き合わせる。

```bash
claude -p "reply with exactly: OK" --model gpt-5.6-luna --output-format json
```

- CLI の JSON 出力の `modelUsage` に、指定した alias が出ていること。
- ゲートウェイのログで、同じ時刻の `/v1/messages` が 200 を返し、実体（`openai/...`）へルーティングされていること。

ツールループまで確認したいなら、リポジトリ外の一時ディレクトリを cwd にして、Read → Write → Read を促すプロンプトを `--tools Read,Write --permission-mode acceptEdits` で実行し、**実際に書かれたファイルの中身**と最終回答が一致するかを見る。応答文だけを根拠にしない。

うまくいかないときは [compatibility-and-troubleshooting.md](compatibility-and-troubleshooting.md) へ。

## 5. 元に戻す

- セッション単位（3-A）: シェルを閉じる。それだけ。
- グローバル（3-B）: `settings.json` の `env` から該当キーを削除し、シェルプロファイルの `ANTHROPIC_AUTH_TOKEN` も消す。**変数が1つでも残ると中途半端な状態になる**ので、`ANTHROPIC_BASE_URL`・`ANTHROPIC_AUTH_TOKEN`・`ANTHROPIC_MODEL` をまとめて確認する。
- ゲートウェイ: `docker compose down`。検証用に発行したキーは破棄し、`.env` も消す。
