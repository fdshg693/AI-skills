# gateway/ — すぐ動かせる LiteLLM Proxy 一式

[../setup.md](../setup.md) の手順1〜2（ゲートウェイの用意と単体確認）を、そのまま `docker compose up` できる形にしたもの。判断の根拠・原則は [../SKILL.md](../SKILL.md)、詰まったときは [../compatibility-and-troubleshooting.md](../compatibility-and-troubleshooting.md)。

## ファイル

| ファイル         | 役割                                                                  |
| ---------------- | --------------------------------------------------------------------- |
| `compose.yaml`   | LiteLLM Proxy。`127.0.0.1:4000` にだけ公開                            |
| `config.yaml`    | 公開する alias と実体のマッピング。**ここを自分のモデルに書き換える** |
| `.env.example`   | 秘密のひな形。コピーして `.env` を作る（`.env` はコミットされない）   |
| `smoke-test.sh`  | Git Bash 用。ゲートウェイ単体の3層確認                                |
| `smoke-test.ps1` | PowerShell 用。同上                                                   |

## 手順

### 1. .env を作る

```bash
cp .env.example .env    # PowerShell: Copy-Item .env.example .env
```

`OPENAI_API_KEY` に上流のキー、`LITELLM_MASTER_KEY` にその場で生成したランダム値を入れる。生成コマンドは `.env.example` のコメントにある。**上流キーはここだけが持つ。Claude Code のプロセスには渡さない。**

### 2. 使うモデルを決める

`config.yaml` の `model_name`（Claude Code に渡す文字列）と `model`（実体）を、使いたい OpenAI モデルに書き換える。既定は `gpt-5-mini`。Claude CLIの現行版が送る `reasoning.effort` に対応するモデルを使う。alias は Claude Code が送る名前そのものにする。

### 3. 起動

```bash
docker compose config --quiet   # 構文とenv参照を先に解決
docker compose up -d --wait --wait-timeout 90
docker compose logs --no-color --tail 50 litellm  # 起動ログを確認（終了する）
```

`docker compose logs -f litellm` はログを追従し続ける監視コマンドなので、実行したままでは次の手順に進まない。使う場合は起動完了を確認して `Ctrl+C` で終了してから、単体確認を実行する。

### 4. 単体確認（Claude Code を繋ぐ前に必ず）

```bash
./smoke-test.sh gpt-5-mini
```

```powershell
pwsh -File .\smoke-test.ps1 -Model gpt-5-mini
```

`/v1/models` に `config.yaml` の alias **だけ**が出て、`/v1/messages` が Anthropic 形式（`type: message` と `content[].text`）を返せば通っている。ここが落ちる限り Claude Code 側を触っても意味がない。

### 5. クライアント用のキーを発行（PostgreSQL構成時のみ）

このサンプルはデータベースなし構成のため、`/key/generate` による仮想キー発行は使えない（`No connected db.` になる）。使い捨ての検証では `LITELLM_MASTER_KEY` をクライアントキーとして使い、終了時に破棄する。継続運用でモデルを限定した仮想キーを発行する場合は、PostgreSQL と LiteLLM のデータベース設定を別途追加する。

このサンプルでは `ANTHROPIC_AUTH_TOKEN` に `LITELLM_MASTER_KEY` の値を使う。

## Claude Code を繋ぐ

**新しいシェル**で環境変数を設定してから起動する（シェルを閉じれば元に戻る）。

PowerShell:

```powershell
$env:ANTHROPIC_BASE_URL   = "http://127.0.0.1:4000"
$env:ANTHROPIC_AUTH_TOKEN = "sk-REPLACE_ME"
Remove-Item Env:ANTHROPIC_API_KEY -ErrorAction SilentlyContinue
claude --model gpt-5-mini
```

Git Bash:

```bash
export ANTHROPIC_BASE_URL="http://127.0.0.1:4000"
export ANTHROPIC_AUTH_TOKEN="sk-REPLACE_ME"
unset ANTHROPIC_API_KEY
claude --model gpt-5-mini
```

`--model` は毎回渡す。省略すると既定の Claude モデル ID が送られ、`model_list` に無くて失敗する。グローバル適用にしたい場合は [../setup.md](../setup.md) の 3-B。

### 効いているかの確認

```bash
claude -p "reply with exactly: OK" --model gpt-5-mini --output-format json
```

JSON の `modelUsage` に指定した alias が出ていること、かつ `docker compose logs litellm` の同時刻に `/v1/messages` 200 が出ていること。応答が返っただけでは Claude モデルへフォールバックしていない保証にならない。

## 片付け

```bash
docker compose down
rm .env            # 検証用に発行したキーも破棄する
```

Claude Code 側は、セッション単位なら該当シェルを閉じるだけ。

## 注意

- ポートは `127.0.0.1` 固定。`"4000:4000"` に書き換えて LAN へ晒さない。
- `config.yaml` に `drop_params: true` を最初から入れない。非互換エラーが実際に出てから、限定的な回避策として検討する。
- モデルピッカーに OpenAI の ID は出てこない（ID に `claude`/`anthropic` を含むものだけが追加される仕様）。明示指定で動けば正常。
