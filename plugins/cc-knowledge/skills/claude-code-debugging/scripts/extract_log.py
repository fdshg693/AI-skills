#!/usr/bin/env python3
"""Extract matching lines from Claude Code debug logs into one text file.

Extraction only -- this script never calls a model or summarizes anything.
Pipe or paste the written output file into the `aim` CLI (see the
my-tools:aim-cli skill) for that: a 2-stage "extract, then summarize"
split keeps this script free of API-key handling.

Handles three log shapes this skill's hands-on experiments (steps 1/3/7)
found in the wild, each with a different on-disk format -- pick the matching
subcommand:

  transcript  Session transcript jsonl (~/.claude/projects/<project>/*.jsonl).
              One JSON object per line. Has `type` (user/assistant/system/
              mode/...) and `timestamp` fields; assistant tool calls live in
              message.content[].tool_use.name. Individual lines can be huge
              (one real example was 140KB+, a Read tool result inlined) --
              see --max-chars/--full.

  hook        jsonl written by a PostToolUse/PreToolUse logging hook (see
              hooks-logging.md). One JSON object per line with `tool_name`
              and `hook_event_name`. IMPORTANT: the logging hook template in
              hooks-logging.md writes stdin verbatim and adds no timestamp,
              so --since/--until are not available for this kind -- use
              --last instead.

  debug       Plain text produced by `claude --debug-file <path>` (or the
              auto-generated ~/.claude/debug/<uuid>.txt). Each line looks
              like "<ISO8601 timestamp> [LEVEL] message". There is no
              structured category field (Step 1 found `-d "hooks"` does not
              reliably filter by category either) -- filter with --keyword,
              not a category flag.

Usage:
    python extract_log.py transcript SESSION.jsonl --tool Bash --last 20
    python extract_log.py hook hook-fired.jsonl --tool Bash --last 10
    python extract_log.py debug debug-logs\\*.log --keyword "safe mode" --ignore-case
    python extract_log.py debug session.log --since 2026-07-20T08:00:00Z --until 2026-07-20T08:10:00Z

Files may use shell wildcards (e.g. "logs\\*.jsonl"); they are expanded by
this script too so it works the same whether or not your shell globs them
(PowerShell does not glob arguments to external programs, bash does).
"""

import argparse
import glob
import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

SKILL_DIR = Path(__file__).resolve().parent.parent
OUTPUT_DIR = SKILL_DIR / "output" / "temp"

DEBUG_LINE_RE = re.compile(r"^(?P<ts>\S+)\s+\[(?P<level>[A-Z]+)\]\s?(?P<msg>.*)$")


def parse_iso(value):
    s = value.strip()
    if s.endswith("Z"):
        s = s[:-1] + "+00:00"
    try:
        dt = datetime.fromisoformat(s)
    except ValueError:
        sys.exit(
            f"error: could not parse timestamp {value!r} (expected ISO8601, e.g. 2026-07-20T08:06:31Z)"
        )
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt


def expand_files(patterns):
    paths = []
    for pattern in patterns:
        matches = sorted(glob.glob(pattern))
        if matches:
            paths.extend(Path(m) for m in matches)
        elif Path(pattern).exists():
            paths.append(Path(pattern))
        else:
            sys.exit(f"error: no file matches {pattern!r}")
    return paths


def name_list(value):
    return [v.strip() for v in value.split(",") if v.strip()] if value else None


def render(obj, max_chars):
    text = (
        json.dumps(obj, ensure_ascii=False, indent=2) if isinstance(obj, (dict, list)) else str(obj)
    )
    if max_chars is not None and len(text) > max_chars:
        cut = len(text) - max_chars
        text = (
            text[:max_chars]
            + f"\n... [truncated, {cut} more chars -- rerun with --full to see everything]"
        )
    return text


def write_entries(entries, kind, out_path, max_chars):
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    with out_path.open("w", encoding="utf-8") as f:
        for path, lineno, header_extra, obj in entries:
            f.write(f"----- {path}:{lineno} [{kind}]{header_extra} -----\n")
            f.write(render(obj, max_chars))
            f.write("\n\n")
    return out_path


def default_out_path(kind, files):
    stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    stem = files[0].stem if files else kind
    return OUTPUT_DIR / f"extract_{kind}_{stem}_{stamp}.txt"


def apply_last(entries, last):
    return entries[-last:] if last else entries


def cmd_transcript(args):
    files = expand_files(args.files)
    types = name_list(args.type)
    tools = name_list(args.tool)
    since = parse_iso(args.since) if args.since else None
    until = parse_iso(args.until) if args.until else None
    keyword_re = (
        re.compile(args.keyword, re.IGNORECASE if args.ignore_case else 0) if args.keyword else None
    )

    entries = []
    scanned = 0
    for path in files:
        for lineno, raw in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
            if not raw.strip():
                continue
            scanned += 1
            try:
                obj = json.loads(raw)
            except json.JSONDecodeError:
                print(f"warning: skipping unparseable line {path}:{lineno}", file=sys.stderr)
                continue

            if types and obj.get("type") not in types:
                continue

            tool_names = [
                c.get("name")
                for c in (obj.get("message", {}).get("content") or [])
                if isinstance(c, dict) and c.get("type") == "tool_use"
            ]
            if tools and not (set(tool_names) & set(tools)):
                continue

            ts = obj.get("timestamp")
            if since or until:
                if not ts:
                    continue
                dt = parse_iso(ts)
                if since and dt < since:
                    continue
                if until and dt > until:
                    continue

            if keyword_re and not keyword_re.search(raw):
                continue

            extra = f" type={obj.get('type')}"
            if tool_names:
                extra += f" tools={','.join(tool_names)}"
            if ts:
                extra += f" timestamp={ts}"
            entries.append((path, lineno, extra, obj))

    entries = apply_last(entries, args.last)
    out_path = Path(args.out) if args.out else default_out_path("transcript", files)
    write_entries(entries, "transcript", out_path, None if args.full else args.max_chars)
    print(
        f"Wrote {out_path} ({len(entries)} matching entries, {scanned} lines scanned across {len(files)} file(s))"
    )


def cmd_hook(args):
    if args.since or args.until:
        sys.exit(
            "error: --since/--until are not supported for `hook` logs -- the logging hook template in "
            "hooks-logging.md writes stdin verbatim and adds no timestamp field. Use --last instead."
        )
    files = expand_files(args.files)
    tools = name_list(args.tool)
    events = name_list(args.event)
    keyword_re = (
        re.compile(args.keyword, re.IGNORECASE if args.ignore_case else 0) if args.keyword else None
    )

    entries = []
    scanned = 0
    for path in files:
        for lineno, raw in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
            if not raw.strip():
                continue
            scanned += 1
            try:
                obj = json.loads(raw)
            except json.JSONDecodeError:
                print(f"warning: skipping unparseable line {path}:{lineno}", file=sys.stderr)
                continue

            if tools and obj.get("tool_name") not in tools:
                continue
            if events and obj.get("hook_event_name") not in events:
                continue
            if keyword_re and not keyword_re.search(raw):
                continue

            extra = f" event={obj.get('hook_event_name')} tool={obj.get('tool_name')}"
            entries.append((path, lineno, extra, obj))

    entries = apply_last(entries, args.last)
    out_path = Path(args.out) if args.out else default_out_path("hook", files)
    write_entries(entries, "hook", out_path, None if args.full else args.max_chars)
    print(
        f"Wrote {out_path} ({len(entries)} matching entries, {scanned} lines scanned across {len(files)} file(s))"
    )


def cmd_debug(args):
    files = expand_files(args.files)
    since = parse_iso(args.since) if args.since else None
    until = parse_iso(args.until) if args.until else None
    keyword_re = (
        re.compile(args.keyword, re.IGNORECASE if args.ignore_case else 0) if args.keyword else None
    )

    entries = []
    scanned = 0
    for path in files:
        for lineno, raw in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
            if not raw.strip():
                continue
            scanned += 1
            m = DEBUG_LINE_RE.match(raw)
            ts, level = (m.group("ts"), m.group("level")) if m else (None, None)

            if since or until:
                if not ts:
                    continue
                dt = parse_iso(ts)
                if since and dt < since:
                    continue
                if until and dt > until:
                    continue

            if keyword_re and not keyword_re.search(raw):
                continue

            extra = f" timestamp={ts}" if ts else ""
            if level:
                extra += f" level={level}"
            entries.append((path, lineno, extra, raw))

    entries = apply_last(entries, args.last)
    out_path = Path(args.out) if args.out else default_out_path("debug", files)
    write_entries(entries, "debug", out_path, None if args.full else args.max_chars)
    print(
        f"Wrote {out_path} ({len(entries)} matching entries, {scanned} lines scanned across {len(files)} file(s))"
    )


def add_common_args(p):
    p.add_argument("files", nargs="+", help="Log file path(s) or glob pattern(s)")
    p.add_argument("--keyword", help="Regex to match against the raw line text")
    p.add_argument("--ignore-case", action="store_true", help="Case-insensitive --keyword matching")
    p.add_argument("--last", type=int, help="Keep only the last N matching entries")
    p.add_argument(
        "--max-chars",
        type=int,
        default=2000,
        help="Truncate each entry to this many chars (default: 2000)",
    )
    p.add_argument(
        "--full", action="store_true", help="Do not truncate entries (overrides --max-chars)"
    )
    p.add_argument(
        "--out",
        help="Output file path (default: output/temp/extract_<kind>_<file>_<timestamp>.txt)",
    )


def main():
    parser = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    sub = parser.add_subparsers(dest="kind", required=True)

    p_transcript = sub.add_parser("transcript", help="Session transcript jsonl")
    add_common_args(p_transcript)
    p_transcript.add_argument(
        "--type", help="Comma-separated `type` values to keep (e.g. user,assistant)"
    )
    p_transcript.add_argument(
        "--tool", help="Comma-separated tool_use names to keep (e.g. Bash,Read)"
    )
    p_transcript.add_argument("--since", help="ISO8601 timestamp; drop entries before this")
    p_transcript.add_argument("--until", help="ISO8601 timestamp; drop entries after this")
    p_transcript.set_defaults(func=cmd_transcript)

    p_hook = sub.add_parser("hook", help="jsonl written by a logging hook (see hooks-logging.md)")
    add_common_args(p_hook)
    p_hook.add_argument("--tool", help="Comma-separated tool_name values to keep")
    p_hook.add_argument(
        "--event",
        help="Comma-separated hook_event_name values to keep (e.g. PreToolUse,PostToolUse)",
    )
    p_hook.add_argument("--since", help=argparse.SUPPRESS)
    p_hook.add_argument("--until", help=argparse.SUPPRESS)
    p_hook.set_defaults(func=cmd_hook)

    p_debug = sub.add_parser("debug", help="Plain text from --debug-file / ~/.claude/debug/*.txt")
    add_common_args(p_debug)
    p_debug.add_argument("--since", help="ISO8601 timestamp; drop lines before this")
    p_debug.add_argument("--until", help="ISO8601 timestamp; drop lines after this")
    p_debug.set_defaults(func=cmd_debug)

    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
