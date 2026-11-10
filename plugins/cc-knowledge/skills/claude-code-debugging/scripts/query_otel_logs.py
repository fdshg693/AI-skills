#!/usr/bin/env python3
"""Query the local claude-code-debugging OTel stack's Loki instance directly.

Unlike tools/infra/ai-logs/scripts/fetch_logs.py (which SSHes into a remote VM
and queries Loki via `docker exec ... wget`), this stack runs entirely on the
local machine with Loki's HTTP API exposed on 127.0.0.1:3100, so this script
talks to it directly over HTTP -- no SSH, no docker exec.

Reads otel-stack/.env (next to this script's parent directory) so callers
(including AI agents) don't need to know or pass credentials directly. The
current query path (direct Loki HTTP API, no auth) does not actually need
GRAFANA_ADMIN_PASSWORD, but .env is still read for a consistent secrets
location and in case a future version queries through the Grafana API instead.

Usage:
    python query_otel_logs.py logs [--since 1h] [--limit 200] [--service claude-code]
    python query_otel_logs.py list-services
"""

import argparse
import datetime
import json
import re
import sys
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

DURATION_RE = re.compile(r"^(\d+)([smhd])$")
UNIT_SECONDS = {"s": 1, "m": 60, "h": 3600, "d": 86400}

STACK_DIR = Path(__file__).resolve().parent.parent / "otel-stack"
ENV_PATH = STACK_DIR / ".env"


def parse_duration(value):
    m = DURATION_RE.match(value.strip())
    if not m:
        sys.exit(f"error: --since must look like '30s', '15m', '2h', '1d' (got {value!r})")
    amount, unit = m.groups()
    return int(amount) * UNIT_SECONDS[unit]


def load_env(path):
    """Minimal KEY=VALUE .env parser (no external deps)."""
    values = {}
    if not path.exists():
        return values
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, val = line.partition("=")
        values[key.strip()] = val.strip()
    return values


def query_loki(base_url, path, params):
    url = f"{base_url}{path}?" + urllib.parse.urlencode(params)
    try:
        with urllib.request.urlopen(url, timeout=10) as resp:
            body = resp.read()
    except urllib.error.URLError as e:
        sys.exit(
            f"error: could not reach Loki at {base_url} ({e}). "
            f"Is the stack up? Run `docker compose up -d` in {STACK_DIR}"
        )
    try:
        return json.loads(body)
    except json.JSONDecodeError:
        sys.exit(f"error: non-JSON response from Loki: {body[:300]!r}")


def cmd_list_services(args):
    data = query_loki(args.loki_url, "/loki/api/v1/label/service_name/values", {})
    values = data.get("data", [])
    if not values:
        print("(no service_name values in Loki yet -- no logs have ever been ingested)")
        return
    for v in values:
        print(v)


def cmd_logs(args):
    since_s = parse_duration(args.since)
    end_ns = int(datetime.datetime.now().timestamp() * 1_000_000_000)
    start_ns = end_ns - since_s * 1_000_000_000

    query = f'{{service_name="{args.service}"}}' if args.service else '{service_name=~".+"}'
    params = {
        "query": query,
        "start": str(start_ns),
        "end": str(end_ns),
        "limit": str(args.limit),
        "direction": "backward",
    }

    data = query_loki(args.loki_url, "/loki/api/v1/query_range", params)
    streams = data.get("data", {}).get("result", [])
    if not streams:
        print(
            f"(no log entries in the last {args.since}"
            + (f" for service_name={args.service!r}" if args.service else "")
            + ")"
        )
        return

    entries = []
    for stream in streams:
        labels = stream.get("stream", {})
        for ts_ns, line in stream.get("values", []):
            entries.append((int(ts_ns), labels, line))
    entries.sort(key=lambda e: e[0])

    for ts_ns, labels, line in entries:
        ts = datetime.datetime.fromtimestamp(ts_ns / 1_000_000_000)
        svc = labels.get("service_name", "?")
        event = labels.get("event_name", line)
        print(f"{ts:%Y-%m-%d %H:%M:%S} [{svc}] {event}")

    print(f"\n({len(entries)} entries, last {args.since})", file=sys.stderr)


def main():
    load_env(ENV_PATH)  # validated for presence; values not required for the direct Loki path today

    parser = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument(
        "--loki-url",
        default="http://localhost:3100",
        help="Loki base URL (default: http://localhost:3100)",
    )
    sub = parser.add_subparsers(dest="action", required=True)

    p_logs = sub.add_parser("logs", help="Fetch recent log entries")
    p_logs.add_argument("--since", default="1h")
    p_logs.add_argument("--limit", type=int, default=200)
    p_logs.add_argument("--service", default="claude-code")
    p_logs.set_defaults(func=cmd_logs)

    p_services = sub.add_parser("list-services", help="List distinct service_name label values")
    p_services.set_defaults(func=cmd_list_services)

    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
