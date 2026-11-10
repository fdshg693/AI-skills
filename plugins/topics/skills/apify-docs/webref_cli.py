"""Unified Typer entry point for this skill's bundled web-reference script(s).

Adapted from writing-skill-web's scripts/webref_cli.py template.
extract-section / grep-sections / inspect-markers are not wired:
docs.apify.com/llms-full.txt (~45MB) has no `# Title` / `Source: URL` page
markers and is not downloaded. Body retrieval is fetch-page (URL + .md).

    python webref_cli.py download
    python webref_cli.py download --force
    python webref_cli.py fetch-page platform/actors
    python webref_cli.py fetch-page https://apify.com/agents.md
    python webref_cli.py search-store "google maps"
    python webref_cli.py check-urls --url https://docs.apify.com/llms.txt --only-broken
    python webref_cli.py generate-excerpt --force
    python webref_cli.py check-excerpt
"""

from __future__ import annotations

import importlib
import sys
from types import ModuleType

import typer

SUBCOMMANDS: dict[str, tuple[str, str]] = {
    "download": (
        "download_apify_reference",
        "Fetch docs.apify.com/llms.txt and apify.com/llms.txt (freshness-checked, --force to refetch).",
    ),
    "fetch-page": (
        "fetch_doc_page",
        "Fetch docs.apify.com / apify.com pages as Markdown (URL.md) into output/temp/.",
    ),
    "search-store": (
        "search_store",
        "Search Apify Store Actors via the public Store API (no token).",
    ),
    "check-urls": (
        "check_urls",
        "Batch-check candidate URLs (llms.txt / .md pages) for reachability.",
    ),
    "generate-excerpt": (
        "generate_apify_excerpt",
        "Maintainer: regenerate output/excerpt.md from output/llms.txt via aim.",
    ),
    "check-excerpt": (
        "check_apify_excerpt",
        "Maintainer: validate output/excerpt.md against output/llms.txt.",
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
