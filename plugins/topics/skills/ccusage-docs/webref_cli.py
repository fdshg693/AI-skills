"""Unified Typer entry point for this skill's bundled web-reference script(s).

Adapted from writing-skill-web's scripts/webref_cli.py template. This skill
bundles a download script plus VitePress-aware section extract/grep (see
SKILL.md: ccusage.com/llms-full.txt concatenates pages with
`---\\nurl: /path.md\\n---` rather than `# Title` / `Source: URL`).
Excerpt generation is not wired up -- the llms.txt index is small and
every entry is in scope.

    python webref_cli.py download
    python webref_cli.py download --force
    python webref_cli.py extract-section guide/daily-reports
    python webref_cli.py grep-sections "cost.?mode" --ignore-case
"""

from __future__ import annotations

import importlib
import sys
from types import ModuleType

import typer

SUBCOMMANDS: dict[str, tuple[str, str]] = {
    "download": (
        "download_ccusage_reference",
        "Fetch the ccusage llms.txt / llms-full.txt snapshot (freshness-checked, --force to refetch).",
    ),
    "check-urls": (
        "check_urls",
        "Batch-check candidate URLs (e.g. llms.txt / llms-full.txt paths) for reachability.",
    ),
    "inspect-markers": (
        "inspect_section_markers",
        "Sample url:/heading marker lines to confirm llms-full.txt's VitePress page structure.",
    ),
    "extract-section": (
        "extract_doc_section",
        "Extract one docs page's section from output/llms-full.txt by URL/slug.",
    ),
    "grep-sections": (
        "grep_doc_sections",
        "Grep output/llms-full.txt with each match attributed to its source URL.",
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
