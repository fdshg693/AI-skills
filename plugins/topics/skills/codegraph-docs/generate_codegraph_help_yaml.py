#!/usr/bin/env python3
# /// script
# requires-python = ">=3.11"
# dependencies = [
#     "pyyaml",
# ]
# ///
"""Generate a YAML summary of `codegraph --help` and every subcommand.

CodeGraph's `--help` is produced by commander.js (same family as Claude Code
CLI). Layout:

- `Usage:` is a single line (`codegraph [options] [command]`).
- `Options:` / `Commands:` entries are 2-space-indented
  `name<2+ spaces>description` header lines. Wrapped descriptions are
  indented deeper and joined with a single space.
- Some real commands (currently `serve`) are hidden from the top-level
  `Commands:` list but still answer `codegraph <name> --help`.

Default run writes one file, `output/cli/help_result.yaml`, with the
top-level parse plus a `subcommands:` map of every distinct command help.
Pass `--top-only` to skip the per-command fetches.

On rerun, generation is skipped if the existing output was fetched within
the last 24 hours; pass `--force` to regenerate regardless of age.
"""

from __future__ import annotations

import argparse
import os
import re
import shutil
import subprocess
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

import yaml

SKILL_DIR = Path(__file__).resolve().parent
OUTPUT_DIR = SKILL_DIR / "output" / "cli"
DEFAULT_OUTPUT = OUTPUT_DIR / "help_result.yaml"

SPLIT_RE = re.compile(r" {2,}")
SECTION_HEADERS = ("Arguments:", "Options:", "Commands:")
# commander.js では全セクションのエントリのヘッダ行がインデント2。
# これより深いインデントの行は、直前エントリの説明の続行とみなす。
ENTRY_HEADER_INDENT_MAX = 2
FRESHNESS = timedelta(days=1)
# 1コマンドの --help は通常1秒未満。ハングしたら切り、全体を止めない。
HELP_TIMEOUT_SECONDS = 30
# トップレベルの Commands: に出ないが、`codegraph <name> --help` が独自の
# Usage を返す隠れコマンド。公式 docs の `serve --mcp` がこれ。
EXTRA_COMMANDS = ("serve",)
# `codegraph help` はトップレベル --help と同じ出力を返すだけ。
SKIP_COMMANDS = {"help"}


def read_fetched_at(path: Path) -> datetime | None:
    if not path.is_file():
        return None
    try:
        with path.open(encoding="utf-8") as f:
            data = yaml.safe_load(f)
    except yaml.YAMLError:
        return None
    if not isinstance(data, dict):
        return None
    value = data.get("fetched_at")
    if not isinstance(value, str):
        return None
    try:
        return datetime.fromisoformat(value)
    except ValueError:
        return None


def resolve_codegraph() -> str:
    found = shutil.which("codegraph")
    if not found:
        raise FileNotFoundError(
            "codegraph が見つかりません。`npm i -g @colbymchenry/codegraph` で入れ、"
            "PATH から呼べるようにしてください。"
        )
    return found


def run_codegraph(*args: str) -> str:
    env = os.environ.copy()
    env["NO_COLOR"] = "1"
    env.pop("FORCE_COLOR", None)
    result = subprocess.run(
        [resolve_codegraph(), *args],
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        check=True,
        timeout=HELP_TIMEOUT_SECONDS,
        env=env,
    )
    return result.stdout


def split_entry(text: str) -> tuple[str, str]:
    parts = SPLIT_RE.split(text, maxsplit=1)
    if len(parts) == 2:
        return parts[0].strip(), parts[1].strip()
    return parts[0].strip(), ""


def parse_entry_section(lines: list[str]) -> list[dict[str, str]]:
    """Arguments:/Options:/Commands: entries are `name<2+ spaces>description` plus continuations."""
    entries: list[dict[str, str]] = []
    for line in lines:
        if not line.strip():
            continue
        indent = len(line) - len(line.lstrip(" "))
        text = line.strip()
        is_bare_label = text.endswith(":") and " " not in text
        is_header = indent <= ENTRY_HEADER_INDENT_MAX and (not is_bare_label or not entries)
        if is_header:
            name, description = split_entry(text)
            if not name:
                continue
            entries.append({"name": name, "description": description})
        elif entries:
            entries[-1]["description"] = (entries[-1]["description"] + " " + text).strip()
    return entries


def parse_help(help_text: str) -> dict:
    usage: list[str] = []
    description_lines: list[str] = []
    sections: dict[str, list[str]] = {name: [] for name in SECTION_HEADERS}
    current_section: str | None = None
    in_usage = False

    for line in help_text.splitlines():
        stripped = line.strip()
        if stripped.startswith("Usage:"):
            usage.append(stripped[len("Usage:") :].strip())
            current_section = None
            in_usage = True
            continue
        if stripped in SECTION_HEADERS:
            current_section = stripped
            in_usage = False
            continue
        if in_usage:
            if stripped:
                usage.append(stripped)
            else:
                in_usage = False
            continue
        if current_section is not None:
            sections[current_section].append(line)
        elif stripped:
            description_lines.append(stripped)

    return {
        "usage": usage,
        "description": " ".join(description_lines).strip(),
        "commands": parse_entry_section(sections["Commands:"]),
        "arguments": parse_entry_section(sections["Arguments:"]),
        "options": parse_entry_section(sections["Options:"]),
    }


def primary_command_name(entry_name: str) -> tuple[str, list[str]]:
    """`init [options] [path]` / `daemon|daemons` → (`init`, []) / (`daemon`, [`daemons`])."""
    token = entry_name.split()[0]
    parts = [p for p in token.split("|") if p]
    if not parts:
        return "", []
    return parts[0], parts[1:]


def looks_like_top_level(parsed: dict, top: dict) -> bool:
    return parsed.get("usage") == top.get("usage") and parsed.get("commands") == top.get("commands")


def invocation_of(parts: list[str]) -> str:
    return "codegraph" if not parts else "codegraph " + " ".join(parts)


def build_record(
    version: str,
    fetched_at: str,
    parts: list[str],
    parsed: dict,
    *,
    hidden: bool = False,
    aliases: list[str] | None = None,
) -> dict:
    record = {
        "version": version,
        "fetched_at": fetched_at,
        "invocation": invocation_of(parts),
        "hidden": hidden,
        "aliases": aliases or [],
        **parsed,
    }
    return record


def fetch_parsed(parts: list[str], help_file: Path | None) -> dict:
    if help_file is not None and not parts:
        return parse_help(help_file.read_text(encoding="utf-8"))
    return parse_help(run_codegraph(*parts, "--help"))


def fetch_subcommand(name: str, top: dict) -> dict | None:
    try:
        parsed = fetch_parsed([name], None)
    except (subprocess.CalledProcessError, subprocess.TimeoutExpired, FileNotFoundError) as exc:
        print(f"skip {name}: {exc}", file=sys.stderr)
        return None
    if looks_like_top_level(parsed, top):
        return None
    return parsed


def collect_subcommands(top: dict) -> dict[str, tuple[dict, list[str], bool]]:
    """Return name → (parsed, aliases, hidden)."""
    collected: dict[str, tuple[dict, list[str], bool]] = {}
    for command in top["commands"]:
        name, aliases = primary_command_name(command["name"])
        if not name or name in SKIP_COMMANDS or name in collected:
            continue
        parsed = fetch_subcommand(name, top)
        if parsed is None:
            continue
        collected[name] = (parsed, aliases, False)

    for name in EXTRA_COMMANDS:
        if name in collected:
            continue
        parsed = fetch_subcommand(name, top)
        if parsed is None:
            continue
        collected[name] = (parsed, [], True)
    return collected


def dump_yaml(path: Path, data: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="\n") as f:
        yaml.dump(
            data,
            f,
            allow_unicode=True,
            sort_keys=False,
            default_flow_style=False,
            width=100000,
        )


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--help-file",
        type=Path,
        help="Parse a previously captured `codegraph --help` instead of invoking codegraph.",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=DEFAULT_OUTPUT,
        help=f"YAML output path (default: {DEFAULT_OUTPUT.relative_to(SKILL_DIR)})",
    )
    parser.add_argument(
        "--top-only",
        action="store_true",
        help="Write only the top-level help (skip per-command --help fetches).",
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Regenerate even if the existing output was fetched less than a day ago.",
    )
    args = parser.parse_args()

    if not args.force:
        fetched_at = read_fetched_at(args.output)
        if fetched_at is not None and datetime.now(timezone.utc) - fetched_at < FRESHNESS:
            print(
                f"{args.output}: すでに最新が取得済です（取得時刻: {fetched_at.isoformat()}）。"
                " --force で上書きできます。"
            )
            return 0

    try:
        version = run_codegraph("--version").splitlines()[0].strip()
        top = fetch_parsed([], args.help_file)
    except FileNotFoundError as exc:
        print(str(exc), file=sys.stderr)
        print("バンドル済みの output/cli/help_result.yaml を参照してください。", file=sys.stderr)
        return 0
    except subprocess.CalledProcessError as exc:
        err = (exc.stderr or exc.stdout or "").strip()
        print(f"codegraph の実行に失敗しました (exit {exc.returncode}): {err}", file=sys.stderr)
        print("バンドル済みの output/cli/help_result.yaml を参照してください。", file=sys.stderr)
        return 0
    except subprocess.TimeoutExpired:
        print(
            f"codegraph --help timed out after {HELP_TIMEOUT_SECONDS}s.",
            file=sys.stderr,
        )
        print("バンドル済みの output/cli/help_result.yaml を参照してください。", file=sys.stderr)
        return 0

    fetched_at_now = datetime.now(timezone.utc).isoformat()
    data = build_record(version, fetched_at_now, [], top)
    data.pop("hidden", None)
    data.pop("aliases", None)

    if not args.top_only:
        subcommands: dict[str, dict] = {}
        for name, (parsed, aliases, hidden) in collect_subcommands(top).items():
            # Nested records drop the repeated version/fetched_at; the parent has them.
            record = {
                "invocation": invocation_of([name]),
                "hidden": hidden,
                "aliases": aliases,
                **parsed,
            }
            subcommands[name] = record
        data["subcommands"] = subcommands

    dump_yaml(args.output, data)
    try:
        display_path = args.output.resolve().relative_to(SKILL_DIR)
    except ValueError:
        display_path = args.output
    n_sub = len(data.get("subcommands") or {})
    print(f"Wrote {display_path} ({n_sub} subcommands)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
