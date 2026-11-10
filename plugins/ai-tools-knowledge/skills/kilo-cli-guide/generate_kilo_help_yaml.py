"""Generate a YAML catalog from the installed `kilo --help` output.

Kilo CLI uses yargs-style help: Commands, Positionals, and Options sections
contain a two-space-indented name followed by a description separated with
two or more spaces. Descriptions that do not fit wrap onto deeper-indented
lines. This parser joins those continuations into the preceding entry.

The result is a committed snapshot so the skill remains useful on machines
where Kilo CLI is unavailable. Generation is skipped for 24 hours unless
`--force` is passed.
"""

from __future__ import annotations

import argparse
import json
import re
import shutil
import subprocess
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any


SKILL_DIR = Path(__file__).resolve().parent
DEFAULT_OUTPUT = SKILL_DIR / "output" / "help_result.yaml"
FRESHNESS = timedelta(days=1)
COMMAND_TIMEOUT_SECONDS = 30
SECTION_HEADERS = {
    "Commands:": "commands",
    "Positionals:": "positionals",
    "Options:": "options",
}
SPLIT_RE = re.compile(r" {2,}")


def run_kilo(*args: str) -> str:
    """Run Kilo without a shell so command arguments cannot be injected."""
    executable = shutil.which("kilo")
    if executable is None:
        raise RuntimeError("`kilo` was not found on PATH. Install @kilocode/cli first.")
    try:
        result = subprocess.run(
            [executable, *args],
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            check=False,
            timeout=COMMAND_TIMEOUT_SECONDS,
        )
    except subprocess.TimeoutExpired as error:
        raise RuntimeError(
            f"`kilo {' '.join(args)}` exceeded {COMMAND_TIMEOUT_SECONDS} seconds."
        ) from error
    output = result.stdout or result.stderr
    if result.returncode:
        message = output.strip() or "no output"
        raise RuntimeError(f"`kilo {' '.join(args)}` failed: {message}")
    return output


def read_fetched_at(path: Path) -> datetime | None:
    """Read the generated ISO timestamp without requiring a YAML package."""
    if not path.is_file():
        return None
    match = re.search(r'^fetched_at: "([^"]+)"$', path.read_text(encoding="utf-8"), re.MULTILINE)
    if match is None:
        return None
    try:
        return datetime.fromisoformat(match.group(1))
    except ValueError:
        return None


def parse_entries(lines: list[str]) -> list[dict[str, str]]:
    entries: list[dict[str, str]] = []
    for line in lines:
        if not line.strip():
            continue
        indent = len(line) - len(line.lstrip(" "))
        text = line.strip()
        is_option = text.startswith("-")
        if indent <= 2 or is_option:
            name, *description = SPLIT_RE.split(text, maxsplit=1)
            entries.append({"name": name, "description": description[0] if description else ""})
        elif entries:
            entries[-1]["description"] = f"{entries[-1]['description']} {text}".strip()
    return entries


def parse_help(help_text: str) -> dict[str, list[dict[str, str]]]:
    sections: dict[str, list[str]] = {key: [] for key in SECTION_HEADERS.values()}
    current_section: str | None = None
    for line in help_text.splitlines():
        header = SECTION_HEADERS.get(line.strip())
        if header is not None:
            current_section = header
        elif current_section is not None:
            sections[current_section].append(line)
    return {name: parse_entries(lines) for name, lines in sections.items()}


def yaml_scalar(value: Any) -> str:
    """Emit JSON scalar syntax, which is also valid YAML 1.2."""
    return json.dumps(value, ensure_ascii=False)


def write_yaml(path: Path, data: dict[str, Any]) -> None:
    lines: list[str] = []
    for key in ("version", "fetched_at", "source"):
        lines.append(f"{key}: {yaml_scalar(data[key])}")
    for section in ("commands", "positionals", "options"):
        lines.append(f"{section}:")
        for entry in data[section]:
            lines.append(f"  - name: {yaml_scalar(entry['name'])}")
            lines.append(f"    description: {yaml_scalar(entry['description'])}")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--help-file", type=Path, help="Parse captured `kilo --help` output.")
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT, help="YAML output path.")
    parser.add_argument("--force", action="store_true", help="Regenerate regardless of age.")
    args = parser.parse_args()

    fetched_at = read_fetched_at(args.output)
    if not args.force and fetched_at and datetime.now(timezone.utc) - fetched_at < FRESHNESS:
        print(
            f"{args.output}: already fresh ({fetched_at.isoformat()}); use --force to regenerate."
        )
        return

    version = run_kilo("--version").splitlines()[0].strip()
    help_text = args.help_file.read_text(encoding="utf-8") if args.help_file else run_kilo("--help")
    data: dict[str, Any] = {
        "version": version,
        "fetched_at": datetime.now(timezone.utc).isoformat(),
        "source": "kilo --help" if args.help_file is None else str(args.help_file),
        **parse_help(help_text),
    }
    write_yaml(args.output, data)
    print(f"Wrote {args.output}")


if __name__ == "__main__":
    main()
