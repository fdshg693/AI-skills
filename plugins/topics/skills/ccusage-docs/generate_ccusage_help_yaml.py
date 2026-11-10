#!/usr/bin/env python3
# /// script
# requires-python = ">=3.11"
# dependencies = [
#     "pyyaml",
# ]
# ///
"""Generate YAML summaries of `ccusage --help` (and optional subcommand helps).

ccusage's `--help` is produced by gunshi (not commander.js / clap). The layout is:

- `USAGE:` / `COMMANDS:` / `OPTIONS:` headers (all caps, trailing colon).
- `USAGE:` is one or more indented invocation lines.
- `COMMANDS:` / `OPTIONS:` entries are 2-space-indented
  `name<2+ spaces>description` lines. Wrapped descriptions (deeper indent)
  are joined with a single space.
- After `COMMANDS:` there is often a prose block starting with
  `For more info, run any command with the `--help` flag:` plus example
  lines. Those are not commands and are skipped until the next header.

The project's workspace root lists `ccusage` in package.json, so this
script prefers `pnpm exec ccusage` / `node_modules/.bin/ccusage` over a
globally installed binary.

Default run (skill load) refreshes only the top-level `output/cli/help_result.yaml`.
Pass `--all` to also capture every first-level command and, when that
command has subcommands, nest their `--help` under `subcommands:`.
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
# Nested under output/cli/ so official-site snapshots (output/llms.txt etc.) stay separate.
OUTPUT_DIR = SKILL_DIR / "output" / "cli"
DEFAULT_OUTPUT = OUTPUT_DIR / "help_result.yaml"
DEFAULT_INDEX = OUTPUT_DIR / "index.yaml"

SPLIT_RE = re.compile(r" {2,}")
SECTION_HEADERS = ("USAGE:", "COMMANDS:", "OPTIONS:", "ARGUMENTS:")
ENTRY_HEADER_INDENT_MAX = 2
FRESHNESS = timedelta(days=1)
INFO_PREFIX = "For more info"


def find_repo_root() -> Path | None:
    for parent in [SKILL_DIR, *SKILL_DIR.parents]:
        if (parent / "package.json").is_file() and (parent / "pnpm-lock.yaml").is_file():
            return parent
    return None


def _bin_candidates(bin_dir: Path) -> list[Path]:
    return [
        bin_dir / "ccusage.CMD",
        bin_dir / "ccusage.cmd",
        bin_dir / "ccusage",
    ]


def resolve_ccusage() -> list[str]:
    """Return an argv prefix that invokes the project-local ccusage."""
    repo_root = find_repo_root()
    if repo_root is not None:
        for candidate in _bin_candidates(repo_root / "node_modules" / ".bin"):
            if candidate.is_file():
                return [str(candidate)]
        pnpm = shutil.which("pnpm")
        if pnpm:
            return [pnpm, "--dir", str(repo_root), "exec", "ccusage"]

    which = shutil.which("ccusage")
    if which:
        return [which]
    raise FileNotFoundError(
        "ccusage が見つかりません。リポジトリルートで `pnpm install` するか、"
        "PATH に ccusage を入れてください。"
    )


def run_ccusage(*args: str) -> str:
    env = os.environ.copy()
    env["NO_COLOR"] = "1"
    env.pop("FORCE_COLOR", None)
    result = subprocess.run(
        [*resolve_ccusage(), *args],
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        check=True,
        env=env,
    )
    return result.stdout


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


def split_entry(text: str) -> tuple[str, str]:
    parts = SPLIT_RE.split(text, maxsplit=1)
    if len(parts) == 2:
        return parts[0].strip(), parts[1].strip()
    return parts[0].strip(), ""


def parse_entry_section(lines: list[str]) -> list[dict[str, str]]:
    entries: list[dict[str, str]] = []
    for line in lines:
        if not line.strip():
            continue
        indent = len(line) - len(line.lstrip(" "))
        text = line.strip()
        is_header = indent <= ENTRY_HEADER_INDENT_MAX
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
    skip_info_block = False

    for line in help_text.splitlines():
        stripped = line.strip()
        if stripped in SECTION_HEADERS:
            current_section = stripped
            skip_info_block = False
            continue
        if stripped.startswith(INFO_PREFIX):
            skip_info_block = True
            continue
        if skip_info_block:
            continue
        if current_section == "USAGE:":
            if stripped:
                usage.append(stripped)
            continue
        if current_section is not None:
            sections[current_section].append(line)
        elif stripped:
            description_lines.append(stripped)

    return {
        "usage": usage,
        "description": " ".join(description_lines).strip(),
        "commands": parse_entry_section(sections["COMMANDS:"]),
        "arguments": parse_entry_section(sections["ARGUMENTS:"]),
        "options": parse_entry_section(sections["OPTIONS:"]),
    }


def command_slug(parts: list[str]) -> str:
    return "-".join(parts) if parts else "help_result"


def dump_yaml(path: Path, data: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        yaml.dump(
            data,
            f,
            allow_unicode=True,
            sort_keys=False,
            default_flow_style=False,
            width=100000,
        )


def invocation_of(parts: list[str]) -> str:
    return "ccusage" if not parts else "ccusage " + " ".join(parts)


def build_record(
    version: str,
    fetched_at: str,
    parts: list[str],
    parsed: dict,
    extra: dict | None = None,
) -> dict:
    record = {
        "version": version,
        "fetched_at": fetched_at,
        "invocation": invocation_of(parts),
        **parsed,
    }
    if extra:
        record.update(extra)
    return record


def fetch_parsed(parts: list[str], help_file: Path | None) -> dict:
    if help_file is not None and not parts:
        return parse_help(help_file.read_text(encoding="utf-8"))
    return parse_help(run_ccusage(*parts, "--help"))


def generate_all(version: str, fetched_at: str, top: dict) -> list[dict[str, str]]:
    index: list[dict[str, str]] = [
        {
            "name": "(top-level)",
            "file": DEFAULT_OUTPUT.name,
            "invocation": "ccusage",
            "description": top.get("description") or "Top-level ccusage help",
        }
    ]
    for command in top["commands"]:
        name = command["name"].split()[0]
        parts = [name]
        parsed = fetch_parsed(parts, None)
        extra: dict = {}
        if parsed["commands"]:
            nested: dict[str, dict] = {}
            for child in parsed["commands"]:
                child_name = child["name"].split()[0]
                child_parts = [name, child_name]
                nested[child_name] = build_record(
                    version, fetched_at, child_parts, fetch_parsed(child_parts, None)
                )
            extra["subcommands"] = nested
        dest = OUTPUT_DIR / f"{command_slug(parts)}.yaml"
        dump_yaml(dest, build_record(version, fetched_at, parts, parsed, extra))
        index.append(
            {
                "name": name,
                "file": dest.name,
                "invocation": invocation_of(parts),
                "description": command.get("description") or parsed.get("description") or "",
            }
        )
        print(f"Wrote {dest.relative_to(SKILL_DIR)}")
    return index


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--help-file",
        type=Path,
        help="Parse a previously captured `ccusage --help` output instead of invoking ccusage.",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=DEFAULT_OUTPUT,
        help=f"Top-level YAML output path (default: {DEFAULT_OUTPUT.relative_to(SKILL_DIR)})",
    )
    parser.add_argument(
        "--all",
        action="store_true",
        help="Also generate first-level command YAML files (and nested subcommands).",
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
        version = run_ccusage("--version").splitlines()[0].strip()
        top = fetch_parsed([], args.help_file)
    except FileNotFoundError as exc:
        print(str(exc), file=sys.stderr)
        print("バンドル済みの output/cli/ を参照してください。", file=sys.stderr)
        return 0
    except subprocess.CalledProcessError as exc:
        print(
            f"ccusage の実行に失敗しました (exit {exc.returncode}): {exc.stderr}",
            file=sys.stderr,
        )
        print("バンドル済みの output/cli/ を参照してください。", file=sys.stderr)
        return 0

    fetched_at_now = datetime.now(timezone.utc).isoformat()
    dump_yaml(args.output, build_record(version, fetched_at_now, [], top))
    try:
        display_path = args.output.resolve().relative_to(SKILL_DIR)
    except ValueError:
        display_path = args.output
    print(f"Wrote {display_path}")

    if args.all:
        index = generate_all(version, fetched_at_now, top)
        dump_yaml(
            DEFAULT_INDEX,
            {
                "version": version,
                "fetched_at": fetched_at_now,
                "commands": index,
            },
        )
        print(f"Wrote {DEFAULT_INDEX.relative_to(SKILL_DIR)}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
