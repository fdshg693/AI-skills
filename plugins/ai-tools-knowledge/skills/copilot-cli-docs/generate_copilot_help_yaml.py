"""Generate a YAML summary of `copilot --help` output.

Assumes the CLI usage is `copilot [options] [command]`. Each Options/Commands/
Help Topics entry is split into a left (name/flags) and right (description)
column by scanning the line left-to-right for the first run of 2+ spaces (a
single space is never treated as a separator). Wrapped description lines
(indented further than the 2-space entry indent) are appended to the previous
entry's description.

The Examples section uses a different format (a `#` comment line followed by
one or more `$ ...` command lines), so it is parsed separately into a list of
{description, commands} entries.

The output YAML records a `fetched_at` timestamp. On rerun, generation is
skipped if the existing output was fetched within the last 24 hours; pass
--force to regenerate regardless of age.
"""

from __future__ import annotations

import argparse
import re
import shutil
import subprocess
from datetime import datetime, timedelta, timezone
from pathlib import Path

import yaml

SKILL_DIR = Path(__file__).resolve().parent
DEFAULT_OUTPUT = SKILL_DIR / "output" / "help_result.yaml"

SPLIT_RE = re.compile(r" {2,}")
ENTRY_SECTIONS = ("Options:", "Commands:", "Help Topics:")
SECTION_HEADERS = ENTRY_SECTIONS + ("Examples:", "Learn More:")
FRESHNESS = timedelta(days=1)


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


def run_copilot(*args: str) -> str:
    executable = shutil.which("copilot") or "copilot"
    result = subprocess.run(
        [executable, *args],
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        check=True,
    )
    return result.stdout


def split_entry(text: str) -> tuple[str, str]:
    parts = SPLIT_RE.split(text, maxsplit=1)
    if len(parts) == 2:
        return parts[0].strip(), parts[1].strip()
    return parts[0].strip(), ""


def parse_section(lines: list[str]) -> list[dict[str, str]]:
    entries: list[dict[str, str]] = []
    for line in lines:
        if not line.strip():
            continue
        indent = len(line) - len(line.lstrip(" "))
        text = line.strip()
        if indent <= 2:
            name, description = split_entry(text)
            entries.append({"name": name, "description": description})
        elif entries:
            entries[-1]["description"] = (entries[-1]["description"] + " " + text).strip()
    return entries


def parse_examples(lines: list[str]) -> list[dict[str, object]]:
    examples: list[dict[str, object]] = []
    current: dict[str, object] | None = None
    for line in lines:
        text = line.strip()
        if not text:
            continue
        if text.startswith("#"):
            current = {"description": text.lstrip("#").strip(), "commands": []}
            examples.append(current)
        elif text.startswith("$"):
            if current is None:
                current = {"description": "", "commands": []}
                examples.append(current)
            current["commands"].append(text[1:].strip())
    return examples


def parse_help(help_text: str) -> dict:
    usage = ""
    description_lines: list[str] = []
    sections: dict[str, list[str]] = {name: [] for name in SECTION_HEADERS}
    current_section: str | None = None

    for line in help_text.splitlines():
        stripped = line.strip()
        if stripped.startswith("Usage:"):
            usage = stripped[len("Usage:") :].strip()
        elif stripped in SECTION_HEADERS:
            current_section = stripped
        elif current_section is not None:
            sections[current_section].append(line)
        elif stripped:
            description_lines.append(stripped)

    return {
        "usage": usage,
        "description": " ".join(description_lines).strip(),
        "options": parse_section(sections["Options:"]),
        "commands": parse_section(sections["Commands:"]),
        "help_topics": parse_section(sections["Help Topics:"]),
        "examples": parse_examples(sections["Examples:"]),
        "learn_more": " ".join(line.strip() for line in sections["Learn More:"] if line.strip()),
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--help-file",
        type=Path,
        help="Parse a previously captured `copilot --help` output instead of invoking copilot.",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=DEFAULT_OUTPUT,
        help=f"YAML output path (default: {DEFAULT_OUTPUT.relative_to(SKILL_DIR)})",
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
                f"{args.output}: すでに最新が取得済です（取得時刻: {fetched_at.isoformat()}）。--force で上書きできます。"
            )
            return

    version = run_copilot("--version").splitlines()[0].strip()
    help_text = (
        args.help_file.read_text(encoding="utf-8") if args.help_file else run_copilot("--help")
    )

    fetched_at_now = datetime.now(timezone.utc).isoformat()
    data = {"version": version, "fetched_at": fetched_at_now, **parse_help(help_text)}

    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open("w", encoding="utf-8") as f:
        yaml.dump(
            data, f, allow_unicode=True, sort_keys=False, default_flow_style=False, width=100000
        )

    try:
        display_path = args.output.resolve().relative_to(SKILL_DIR)
    except ValueError:
        display_path = args.output
    print(f"Wrote {display_path}")


if __name__ == "__main__":
    main()
