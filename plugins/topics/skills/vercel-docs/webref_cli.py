"""Unified Typer entry point for this skill's bundled web-reference script(s).

Adapted from writing-skill-web's scripts/webref_cli.py template. extract-section
/ grep-sections are not wired: Vercel's llms-full.txt puts `-----`-fenced
metadata (`title:` / `source:`) BEFORE the `# Title` heading, so it is not the
(`# Title` / `Source: URL`) layout those scripts expect. Body retrieval is
fetch-page (docs URL + .md).

    python webref_cli.py download
    python webref_cli.py download --force
    python webref_cli.py download --include-full
    python webref_cli.py fetch-page docs/functions
    python webref_cli.py check-urls --url https://vercel.com/docs/llms.txt --only-broken
    python webref_cli.py inspect-markers "${CLAUDE_SKILL_DIR}/output/llms-full.txt"
"""

from __future__ import annotations

import importlib
import sys
from types import ModuleType

import typer

SUBCOMMANDS: dict[str, tuple[str, str]] = {
    "download": (
        "download_vercel_reference",
        "Fetch the Vercel docs index snapshot (llms.txt / products.md / sitemap.md / taxonomy.json; --include-full adds llms-full.txt). Freshness-checked, --force to refetch.",
    ),
    "check-urls": (
        "check_urls",
        "Batch-check candidate URLs (llms.txt / sitemap.md / .md pages) for reachability.",
    ),
    "inspect-markers": (
        "inspect_section_markers",
        "Sample heading/source marker lines to confirm an llms-full.txt-style dump structure.",
    ),
    "fetch-page": (
        "fetch_doc_page",
        "Fetch one or more docs pages as Markdown (URL.md) into output/temp/.",
    ),
}

app = typer.Typer(
    add_completion=False,
    no_args_is_help=True,
    help="Unified entry point for this skill's bundled web-reference scripts.",
)


@app.callback()
def _root() -> None:
    """No-op callback.

    Typer collapses a Typer() app to a bare single Command (dropping the
    subcommand name entirely, e.g. `download --force` would parse `download`
    itself as a stray positional arg) whenever exactly one @app.command() is
    registered and no callback exists. Registering this callback forces Typer
    to always build a Group, so `python webref_cli.py download ...` keeps
    working regardless of how many subcommands are wired up.
    """


def _load(module_name: str) -> ModuleType:
    return importlib.import_module(module_name)


def _make_forwarder(module_name: str):
    def _run(ctx: typer.Context) -> None:
        module = _load(module_name)
        original_argv = sys.argv
        sys.argv = [module_name, *ctx.args]
        try:
            exit_code = module.main()
        finally:
            sys.argv = original_argv
        raise typer.Exit(code=exit_code if isinstance(exit_code, int) else 0)

    return _run


for _name, (_module_name, _help) in SUBCOMMANDS.items():
    app.command(
        name=_name,
        help=_help,
        context_settings={
            "allow_extra_args": True,
            "ignore_unknown_options": True,
            "help_option_names": [],
        },
    )(_make_forwarder(_module_name))


if __name__ == "__main__":
    app()
