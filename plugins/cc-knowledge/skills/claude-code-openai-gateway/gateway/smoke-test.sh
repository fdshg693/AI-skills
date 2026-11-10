#!/usr/bin/env bash
# ゲートウェイ単体の確認（Claude Code を繋ぐ前に実行する）。
# 使い方: ./smoke-test.sh [alias]   ※ alias 既定は config.yaml の gpt-5-mini
set -euo pipefail
cd "$(dirname "$0")"

[ -f .env ] || { echo "ERROR: .env がない。.env.example をコピーして埋める。" >&2; exit 1; }
# shellcheck disable=SC1091
set -a; . ./.env; set +a

MODEL="${1:-gpt-5-mini}"
PORT="${LITELLM_PORT:-4000}"
BASE="http://127.0.0.1:${PORT}"

echo "== 1. liveliness =="
curl --connect-timeout 5 --max-time 30 -fsS "${BASE}/health/liveliness"; echo

echo "== 2. 公開モデル一覧（config.yaml の alias だけが出ること） =="
curl --connect-timeout 5 --max-time 30 -fsS "${BASE}/v1/models" -H "Authorization: Bearer ${LITELLM_MASTER_KEY}"; echo

echo "== 3. Messages 契約（Anthropic 形式で返ること） =="
curl --connect-timeout 5 --max-time 120 -fsS "${BASE}/v1/messages" \
  -H "Authorization: Bearer ${LITELLM_MASTER_KEY}" \
  -H "anthropic-version: 2023-06-01" \
  -H "content-type: application/json" \
  -d "{\"model\":\"${MODEL}\",\"max_tokens\":64,\"messages\":[{\"role\":\"user\",\"content\":\"reply with OK\"}]}"
echo
echo "OK: 3層とも通った。次は README.md の「Claude Code を繋ぐ」へ。"
