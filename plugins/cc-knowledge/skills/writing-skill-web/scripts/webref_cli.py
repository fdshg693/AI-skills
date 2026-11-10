"""Copy-and-adapt template: unified Typer entry point for this skill's other
scripts/*.py templates.

Copy this file into the new skill's directory alongside whichever other
templates from scripts/ you copied (download_web_reference.py, check_urls.py,
etc. -- possibly renamed per web-patterns-reference.md section 1.1, e.g.
download_web_reference.py -> download_vscode_docs.py). Then adapt
SUBCOMMANDS below:

  1. Delete rows for templates you did not copy into this skill.
  2. If you renamed a copied template's *file*, update that row's module name
     to match (the module name is the filename without ".py").

Once adapted, invoke every copied script through one command instead of
remembering each script's own filename:

    python webref_cli.py download --url https://example.com/llms.txt
    python webref_cli.py download-github --repo owner/name --docs-root docs
    python webref_cli.py check-urls --url https://example.com/llms.txt --only-broken
    python webref_cli.py generate-excerpt --model minimax-m3
    python webref_cli.py check-excerpt
    python webref_cli.py inspect-markers output/llms-full.txt
    python webref_cli.py extract-section some/known/page
    python webref_cli.py grep-sections "ERROR_CODE_\\d+" --ignore-case
    python webref_cli.py download-index --url https://example.com/sitemap.xml
    python webref_cli.py select-urls --keyword routing
    python webref_cli.py fetch-pages --manifest output/selection.json

Each subcommand forwards its arguments VERBATIM to that script's own
argparse-based main() -- the per-script flags documented in each script's
docstring/--help are unchanged. This file only replaces "which script do I
run" with a single command palette; it does not reimplement any script's
argument parsing. Run `python webref_cli.py --help` to list the subcommands
actually wired up here, and `python webref_cli.py <subcommand> --help` for
that script's own arguments.
"""

from __future__ import annotations

import importlib
import sys
from types import ModuleType

import typer

# --- adapt this table when copying: delete rows for templates you did not
# copy into this skill, and fix the module name if you renamed the file. -----
SUBCOMMANDS: dict[str, tuple[str, str]] = {
    "download": (
        "download_web_reference",
        "Fetch a static web reference snapshot (freshness-checked, --force to refetch).",
    ),
    "download-github": (
        "download_github_docs",
        "Mirror Markdown docs from a GitHub repo via `gh api` (freshness-checked, --force).",
    ),
    "check-urls": (
        "check_urls",
        "Batch-check candidate URLs (e.g. llms.txt / llms-full.txt paths) for reachability.",
    ),
    "generate-excerpt": (
        "generate_llms_excerpt",
        "AI-curate a draft excerpt of a large llms.txt index (review before use).",
    ),
    "check-excerpt": (
        "check_llms_excerpt",
        "Validate a generated excerpt's format and drift against its source index.",
    ),
    "inspect-markers": (
        "inspect_section_markers",
        "Sample heading/source marker lines to confirm a llms-full.txt dump's structure.",
    ),
    "extract-section": (
        "extract_doc_section",
        "Extract one page's section from a llms-full.txt-style dump by URL/slug.",
    ),
    "grep-sections": (
        "grep_doc_sections",
        "Grep a llms-full.txt dump with each match attributed to its source URL.",
    ),
    "download-index": (
        "download_url_index",
        "Download sitemap or llms.txt and write a normalized URL list and compact tree.",
    ),
    "select-urls": (
        "select_url_index",
        "Filter the normalized URL list into an explicit selection manifest.",
    ),
    "fetch-pages": (
        "fetch_selected_pages",
        "Fetch only explicit URLs or manifest entries into output/temp/.",
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
