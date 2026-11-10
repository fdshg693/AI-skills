"""Generate a YAML summary of `cline --help` output.

Cline CLI uses Commander.js-style help with Arguments:, Options:, and Commands:
sections. The output is intentionally a small, searchable snapshot for the
cline-cli-docs skill. It is refreshed at most once per day unless --force is
provided. A captured subcommand help file can be parsed with --help-file.
"""

from __future__ import annotations

import argparse
import re
import shutil
import subprocess
import tempfile
from datetime import datetime, timedelta, timezone
from pathlib import Path

import yaml

SKILL_DIR = Path(__file__).resolve().parent
DEFAULT_OUTPUT = SKILL_DIR / "output" / "help_result.yaml"
SECTION_HEADERS = ("Arguments:", "Options:", "Commands:")
SPLIT_RE = re.compile(r" {2,}")
FRESHNESS = timedelta(days=1)


def read_fetched_at(path: Path) -> datetime | None:
    if not path.is_file():
        return None
    try:
        with path.open(encoding="utf-8") as stream:
            data = yaml.safe_load(stream)
    except (OSError, yaml.YAMLError):
        return None
    if not isinstance(data, dict) or not isinstance(data.get("fetched_at"), str):
        return None
    try:
        return datetime.fromisoformat(data["fetched_at"])
    except ValueError:
        return None


def run_cline(*args: str) -> str:
    executable = shutil.which("cline") or "cline"
    # Some installed Cline builds print help and keep a background process alive.
    # Use a temporary file instead of PIPE so a timed-out child cannot keep this
    # generator blocked through an inherited pipe handle.
    with tempfile.TemporaryFile(mode="w+", encoding="utf-8", errors="replace") as stream:
        try:
            result = subprocess.run(
                [executable, *args],
                stdout=stream,
                stderr=stream,
                timeout=3,
                check=False,
            )
        except subprocess.TimeoutExpired as error:
            stream.seek(0)
            output = stream.read()
            if not output.strip():
                raise RuntimeError(f"cline {' '.join(args)} timed out") from error
            return output
        stream.seek(0)
        output = stream.read()
    if result.returncode != 0 and not output.strip():
        raise subprocess.CalledProcessError(result.returncode, [executable, *args])
    return output


def split_entry(text: str) -> tuple[str, str]:
    parts = SPLIT_RE.split(text, maxsplit=1)
    if len(parts) == 2:
        return parts[0].strip(), parts[1].strip()
    return parts[0].strip(), ""


def parse_section(lines: list[str]) -> list[dict[str, str]]:
    """Parse Commander.js entries and append indented wrapped lines."""
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


def parse_help(help_text: str) -> dict:
    usage = ""
    description_lines: list[str] = []
    sections: dict[str, list[str]] = {name: [] for name in SECTION_HEADERS}
    current_section: str | None = None

    for line in help_text.splitlines():
        stripped = line.strip()
        if stripped.startswith("Usage:"):
            usage = stripped[len("Usage:") :].strip()
            current_section = None
        elif stripped in SECTION_HEADERS:
            current_section = stripped
        elif current_section is not None:
            sections[current_section].append(line)
        elif stripped:
            description_lines.append(stripped)

    return {
        "usage": usage,
        "description": " ".join(description_lines).strip(),
        "arguments": parse_section(sections["Arguments:"]),
        "options": parse_section(sections["Options:"]),
        "commands": parse_section(sections["Commands:"]),
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--help-file",
        type=Path,
        help="Parse captured `cline ... --help` output instead of invoking cline.",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=DEFAULT_OUTPUT,
        help="YAML output path (default: output/help_result.yaml).",
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Regenerate even when the existing output is less than a day old.",
    )
    args = parser.parse_args()

    if not args.force:
        fetched_at = read_fetched_at(args.output)
        if fetched_at is not None and datetime.now(timezone.utc) - fetched_at < FRESHNESS:
            print(
                f"{args.output}: fresh snapshot at {fetched_at.isoformat()}; use --force to refresh."
            )
            return

    version = run_cline("--version").splitlines()[0].strip()
    help_text = (
        args.help_file.read_text(encoding="utf-8") if args.help_file else run_cline("--help")
    )
    data = {
        "version": version,
        "fetched_at": datetime.now(timezone.utc).isoformat(),
        **parse_help(help_text),
    }

    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open("w", encoding="utf-8") as stream:
        yaml.safe_dump(
            data,
            stream,
            allow_unicode=True,
            sort_keys=False,
            default_flow_style=False,
            width=100000,
        )

    try:
        display_path = args.output.resolve().relative_to(SKILL_DIR)
    except ValueError:
        display_path = args.output
    print(f"Wrote {display_path}")


if __name__ == "__main__":
    main()
