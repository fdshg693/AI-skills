"""Unified Typer entry point for this skill's bundled scripts.

    python webref_cli.py download --force
    python webref_cli.py extract-section ai-providers/alibaba

Each subcommand forwards its arguments VERBATIM to that script's own
argparse-based main() -- the per-script flags documented in each script's
docstring/--help are unchanged. This file only replaces "which script do I
run" with a single command palette. Run `python webref_cli.py --help` to
list the subcommands wired up here, and `python webref_cli.py <subcommand>
--help` for that script's own arguments.
"""

from __future__ import annotations

import importlib
import sys
from types import ModuleType

import typer

SUBCOMMANDS: dict[str, tuple[str, str]] = {
    "download": (
        "download_kilo_docs_reference",
        "Fetch the Kilo Code docs snapshot (freshness-checked, --force to refetch).",
    ),
    "extract-section": (
        "extract_doc_section",
        "Extract one page's section from output/llms.txt by URL/path/slug.",
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
    subcommand name entirely) whenever exactly one @app.command() is
    registered and no callback exists. Registering this callback forces
    Typer to always build a Group, so subcommand dispatch keeps working
    even though this skill only wires up two rows in SUBCOMMANDS.
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
