r"""Fetch the text content of exactly one URL via Tavily extract and write it to a file.

Minimal, single-purpose sibling of the `tav-cli` skill's `extract_url_content.py`:
no `--topic` output layout, no result envelope, no `tav_core` dependency. Unlike
that stdout-only design, this script always writes the fetched page to a Markdown
file (so large pages don't blow up the calling agent's context) and prints only
the file path to the terminal. An optional audit log (full request/response) can
be written alongside, toggled the same way `tav-cli` toggles its own audit log.

For anything beyond "I have exactly one URL and want its text" (multiple URLs,
site maps/crawls, keyword search when the URL is unknown, or results that need
to accumulate across many pages for later reuse), use the `tav-cli` skill
instead.

PowerShell example:
    python .\claude-plugins\my-tools\skills\tav-lit\extract_page.py https://example.com/page

bash example:
    python ./skills/plugins/web-lookup/skills/tav-lit/extract_page.py https://example.com/page --query "pricing"
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
from collections.abc import Sequence
from datetime import datetime, timezone
from pathlib import Path

EXIT_SUCCESS = 0
EXIT_RUNTIME_ERROR = 1
EXIT_MISSING_API_KEY = 2
EXIT_INVALID_API_KEY = 3
EXIT_EMPTY_RESULT = 4

REQUEST_TIMEOUT_SECONDS = 60.0

# Output-layout settings, read from the environment (see README "設定とパス解決").
OUTPUT_DIR_ENV = "TAVILY_OUTPUT_DIR"
WRITE_LOG_ENV = "TAVILY_WRITE_LOG"
DEFAULT_OUTPUT_DIR = "temp/simple_tavily"

# Fixed, script-relative log location (not affected by TAVILY_OUTPUT_DIR), mirroring
# tav-cli's `logs/<script>-log.json` convention: one file, overwritten each run.
SCRIPT_DIR = Path(__file__).resolve().parent
ENV_PATH = SCRIPT_DIR / ".env"
LOG_PATH = SCRIPT_DIR / "logs" / "extract_page-log.json"

_FALSEY_ENV_VALUES = {"", "false", "0", "no", "off"}
_SLUG_SEPARATOR = re.compile(r"[^\w]+", re.UNICODE)
_SEQUENCE_PREFIX = re.compile(r"^(\d{4})")


def parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Fetch the text content of one URL via Tavily extract.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=(
            "Always writes '# <title>', 'Source: <url>', and the page content to a\n"
            "Markdown file under TAVILY_OUTPUT_DIR (default temp/simple_tavily/) and\n"
            "prints only that file's path to stdout. Only one URL per call by design;\n"
            "use the tav-cli skill for batches."
        ),
    )
    parser.add_argument("url", help="Single URL to fetch text content for.")
    parser.add_argument(
        "--query",
        help=(
            "Only return chunks relevant to this query/keyword instead of the "
            "full page (Tavily-side focused extraction)."
        ),
    )
    parser.add_argument(
        "--deep",
        action="store_true",
        help=(
            "Use extract_depth=advanced for pages basic extraction handles "
            "poorly (heavy JS, tables). Default is basic."
        ),
    )
    return parser.parse_args(argv)


def missing_required_key_message(key: str, env_path: Path) -> str:
    env_state = "未設定" if key not in os.environ else "空で設定されている"
    if not env_path.is_file():
        file_state = f"想定した .env は {env_path} ですが、ファイルがありません。"
    else:
        file_state = f"{env_path} はありますが、{key} が無いか空です。"
    return f"{key} が解決できません。\n環境変数 {key} は{env_state}です。\n{file_state}"


def resolve_api_key() -> str:
    """Return TAVILY_API_KEY from the environment, falling back to a co-located `.env`.

    Env var takes priority (including an empty value, which is not filled from
    `.env`). If unset, load `.env` from the same directory as this script
    (independent of the current working directory) — not an upward search from cwd.
    """
    api_key = os.environ.get("TAVILY_API_KEY", "").strip()
    if api_key:
        return api_key

    try:
        from dotenv import load_dotenv
    except ImportError:
        return ""

    load_dotenv(dotenv_path=ENV_PATH, override=False)
    return os.environ.get("TAVILY_API_KEY", "").strip()


def _env_flag(name: str, *, default: bool = True) -> bool:
    """Parse a boolean toggle env var with the shared falsey convention.

    Default (unset) is ``default``. Values ``false`` / ``0`` / ``no`` / ``off`` /
    empty (case-insensitive) read as ``False``; anything else reads as ``True``.
    """
    raw = os.environ.get(name)
    if raw is None:
        return default
    return raw.strip().lower() not in _FALSEY_ENV_VALUES


def should_write_log() -> bool:
    """Whether to write ``logs/extract_page-log.json``, from ``TAVILY_WRITE_LOG``.

    Default (unset) is ``True``. Same falsey convention as the `tav-cli` skill's
    own ``TAVILY_WRITE_LOG`` toggle.
    """
    return _env_flag(WRITE_LOG_ENV)


def get_output_dir() -> Path:
    """Base directory for the written Markdown file, from ``TAVILY_OUTPUT_DIR``.

    An **absolute** value is used verbatim. A **relative** one (including the
    ``temp/simple_tavily`` default) is resolved against the **current working
    directory** at invocation, matching `tav-cli`'s own resolution rule.
    """
    value = os.environ.get(OUTPUT_DIR_ENV, "").strip()
    return Path(value or DEFAULT_OUTPUT_DIR)


def slugify(text: str | None, *, max_length: int = 50) -> str:
    """Turn a title into a safe file-name stem (mirrors tav-cli's slugify)."""
    lowered = (text or "").strip().lower()
    slug = _SLUG_SEPARATOR.sub("-", lowered).strip("-")
    if len(slug) > max_length:
        slug = slug[:max_length].rstrip("-")
    return slug or "item"


def next_sequence(directory: Path) -> int:
    """Next ``NNNN`` to allocate in ``directory`` (existing max + 1, else 1).

    Re-running the script against the same output dir appends (``0002`` after
    ``0001``) instead of overwriting a previous result.
    """
    if not directory.exists():
        return 1
    highest = 0
    for entry in directory.iterdir():
        match = _SEQUENCE_PREFIX.match(entry.name)
        if match:
            highest = max(highest, int(match.group(1)))
    return highest + 1


def write_result_file(*, title: str, url: str, content: str, query: str | None) -> Path:
    output_dir = get_output_dir()
    output_dir.mkdir(parents=True, exist_ok=True)
    sequence = next_sequence(output_dir)
    file_path = output_dir / f"{sequence:04d}-{slugify(title)}.md"

    lines = [f"# {title}", f"Source: {url}"]
    if query:
        lines.append(
            f"Note: content is limited to chunks relevant to '{query}'; "
            "'[...]' marks skipped, non-contiguous text."
        )
    lines.append("")
    lines.append(content)
    file_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return file_path


def write_log_file(*, request: dict, response: dict) -> Path:
    LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "script": Path(__file__).name,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "request": request,
        "response": response,
    }
    LOG_PATH.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return LOG_PATH


def main(argv: Sequence[str] | None = None) -> int:
    args = parse_args(argv)

    api_key = resolve_api_key()
    if not api_key:
        print(missing_required_key_message("TAVILY_API_KEY", ENV_PATH), file=sys.stderr)
        return EXIT_MISSING_API_KEY

    try:
        from tavily import TavilyClient
        from tavily.errors import InvalidAPIKeyError
    except ImportError:
        print(
            "The 'tavily' package is not installed. Install it with "
            "'pip install tavily python-dotenv' (see tav-cli skill's README.md).",
            file=sys.stderr,
        )
        return EXIT_RUNTIME_ERROR

    client = TavilyClient(api_key=api_key)
    extract_depth = "advanced" if args.deep else "basic"
    chunks_per_source = 5 if args.query else None

    try:
        response = client.extract(
            urls=[args.url],
            query=args.query,
            extract_depth=extract_depth,
            chunks_per_source=chunks_per_source,
            format="markdown",
            timeout=REQUEST_TIMEOUT_SECONDS,
            include_images=False,
            include_favicon=False,
        )
    except InvalidAPIKeyError as exc:
        print(f"Invalid Tavily API key: {exc}", file=sys.stderr)
        return EXIT_INVALID_API_KEY
    except Exception as exc:  # network errors, timeouts, unexpected API shapes
        print(f"Extraction failed: {exc}", file=sys.stderr)
        return EXIT_RUNTIME_ERROR

    if should_write_log():
        log_path = write_log_file(
            request={
                "url": args.url,
                "query": args.query,
                "extract_depth": extract_depth,
                "chunks_per_source": chunks_per_source,
            },
            response=response,
        )
        print(f"Wrote log to {log_path}")

    results = response.get("results") or []
    if not results:
        failed = response.get("failed_results") or []
        reason = failed[0].get("error") if failed else "no results returned"
        print(f"Could not extract content from {args.url}: {reason}", file=sys.stderr)
        return EXIT_EMPTY_RESULT

    item = results[0]
    title = item.get("title") or args.url
    content = item.get("raw_content") or ""

    result_path = write_result_file(
        title=title,
        url=item.get("url", args.url),
        content=content,
        query=args.query,
    )
    print(f"Wrote page content to {result_path}")
    return EXIT_SUCCESS


if __name__ == "__main__":
    raise SystemExit(main())
