"""Unified Typer entry point for this skill's bundled web-reference script(s).

Adapted from writing-skill-web's scripts/webref_cli.py template. This skill
bundles a download script and a section-extraction script (see SKILL.md for
why: the docs/llms-full.txt dump follows the `# Title` / `Source: URL`
section-marker pattern, so extract_doc_section.py can pull one page without
grepping the whole ~87k-line file. The root llms.txt/llms-full.txt do not
follow that pattern and are meant to be grepped/read directly instead).

    python webref_cli.py download
    python webref_cli.py download --force
    python webref_cli.py extract-section ona/agents-md
"""

from __future__ import annotations

import importlib
import sys
from types import ModuleType

import typer

SUBCOMMANDS: dict[str, tuple[str, str]] = {
    "download": (
        "download_ona_reference",
        "Fetch the Ona llms.txt / llms-full.txt (root + docs) snapshot (freshness-checked, --force to refetch).",
    ),
    "extract-section": (
        "extract_doc_section",
        "Extract one docs page's section from output/docs/llms-full.txt by URL/slug.",
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
