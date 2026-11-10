"""Unified Typer entry point for the LiteLLM URL index scripts.

Each subcommand forwards arguments verbatim to the selected script's
argparse-based ``main`` function. Run ``--help`` to list available commands.
"""

from __future__ import annotations

import importlib
import sys
from types import ModuleType

import typer

# --- adapt this table when copying: delete rows for templates you did not
# copy into this skill, and fix the module name if you renamed the file. -----
SUBCOMMANDS: dict[str, tuple[str, str]] = {
    "download-index": (
        "download_litellm_url_index",
        "Download LiteLLM's sitemap and write the filtered URL list and compact tree.",
    ),
    "select-urls": (
        "select_url_index",
        "Filter the normalized URL list into an explicit selection manifest.",
    ),
    "fetch-pages": (
        "fetch_selected_pages",
        "Fetch only explicit LiteLLM documentation URLs or manifest entries into output/temp/.",
    ),
}
# ------------------------------------------------------------------------------

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
    registered and no callback exists. This template ships with 7 rows in
    SUBCOMMANDS, but copies commonly trim it down to just 1 (e.g. a skill
    that only needs `download`) -- which would silently hit that collapse.
    Registering this callback forces Typer to always build a Group, so
    subcommand dispatch keeps working regardless of how many rows survive
    adaptation. Do not remove this when trimming SUBCOMMANDS.
    """


def _load(module_name: str) -> ModuleType:
    return importlib.import_module(module_name)


def _make_forwarder(module_name: str):
    def _run(ctx: typer.Context) -> None:
        module = _load(module_name)
        # The wrapped script's own main() takes no arguments and reads
        # sys.argv itself (via argparse.parse_args()). Swap sys.argv so it
        # sees exactly this subcommand's forwarded args, not
        # "webref_cli.py <subcommand> ...".
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
        # help_option_names=[] stops Click itself from swallowing --help/-h --
        # without it, `webref_cli.py <subcommand> --help` would print this
        # dispatcher's generic help instead of forwarding to the wrapped
        # script's own argparse --help (which is what the module-level
        # docstring above promises).
        context_settings={
            "allow_extra_args": True,
            "ignore_unknown_options": True,
            "help_option_names": [],
        },
    )(_make_forwarder(_module_name))


if __name__ == "__main__":
    app()
