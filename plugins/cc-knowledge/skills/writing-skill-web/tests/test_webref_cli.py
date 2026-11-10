"""Tests for scripts/webref_cli.py (unified Typer entry point template).

These tests substitute fake modules for the real download_web_reference.py
etc. (via sys.modules) rather than exercising the real scripts end-to-end --
each real script already has its own dedicated test module in this
directory; here we only verify webref_cli's dispatch/argv-forwarding logic.
"""

from __future__ import annotations

import sys
import types

import pytest
import typer
from typer.testing import CliRunner

import webref_cli

runner = CliRunner()


def test_help_lists_every_configured_subcommand():
    result = runner.invoke(webref_cli.app, ["--help"])
    assert result.exit_code == 0
    for name in webref_cli.SUBCOMMANDS:
        assert name in result.output


def test_forwarder_swaps_argv_to_only_the_forwarded_args_and_restores_it(monkeypatch):
    captured = {}

    def fake_main():
        captured["argv"] = list(sys.argv)
        return 0

    fake_module = types.ModuleType("fake_forwarder_target")
    fake_module.main = fake_main
    monkeypatch.setitem(sys.modules, "fake_forwarder_target", fake_module)

    original_argv = list(sys.argv)
    forwarder = webref_cli._make_forwarder("fake_forwarder_target")

    class DummyContext:
        args = ["--url", "https://example.com/llms.txt", "--force"]

    with pytest.raises(typer.Exit) as exc_info:
        forwarder(DummyContext())

    assert exc_info.value.exit_code == 0
    assert captured["argv"] == [
        "fake_forwarder_target",
        "--url",
        "https://example.com/llms.txt",
        "--force",
    ]
    assert sys.argv == original_argv


def test_forwarder_propagates_non_zero_exit_code(monkeypatch):
    fake_module = types.ModuleType("fake_failing_target")
    fake_module.main = lambda: 2
    monkeypatch.setitem(sys.modules, "fake_failing_target", fake_module)

    forwarder = webref_cli._make_forwarder("fake_failing_target")

    class DummyContext:
        args: list[str] = []

    with pytest.raises(typer.Exit) as exc_info:
        forwarder(DummyContext())

    assert exc_info.value.exit_code == 2


def test_cli_invocation_dispatches_to_the_registered_module(monkeypatch):
    """Full-stack check: `webref_cli.py download ...` really reaches the
    download subcommand's module with the forwarded arguments, restoring the
    real download_web_reference module afterwards (monkeypatch handles that)."""

    captured = {}

    def fake_main():
        captured["argv"] = list(sys.argv)
        return 0

    fake_module = types.ModuleType("download_web_reference")
    fake_module.main = fake_main
    monkeypatch.setitem(sys.modules, "download_web_reference", fake_module)

    result = runner.invoke(webref_cli.app, ["download", "--url", "https://example.com/llms.txt"])

    assert result.exit_code == 0
    assert captured["argv"] == ["download_web_reference", "--url", "https://example.com/llms.txt"]


def test_cli_invocation_surfaces_non_zero_exit_code(monkeypatch):
    fake_module = types.ModuleType("check_urls")
    fake_module.main = lambda: 1
    monkeypatch.setitem(sys.modules, "check_urls", fake_module)

    result = runner.invoke(webref_cli.app, ["check-urls", "--url", "https://example.com/broken"])
    assert result.exit_code == 1


@pytest.mark.parametrize(
    ("command", "module"),
    [
        ("download-index", "download_url_index"),
        ("select-urls", "select_url_index"),
        ("fetch-pages", "fetch_selected_pages"),
        ("download-github", "download_github_docs"),
    ],
)
def test_url_index_commands_forward_arguments(monkeypatch, command, module):
    captured = {}

    def fake_main():
        captured["argv"] = list(sys.argv)
        return 0

    fake_module = types.ModuleType(module)
    fake_module.main = fake_main
    monkeypatch.setitem(sys.modules, module, fake_module)
    result = runner.invoke(webref_cli.app, [command, "--keyword", "routing"])
    assert result.exit_code == 0
    assert captured["argv"] == [module, "--keyword", "routing"]


def test_subcommand_help_forwards_to_the_wrapped_scripts_own_argparse_help():
    """--help must reach the wrapped script's own argparse (detailed, per-flag
    help), not get swallowed by Typer/Click's generic command help -- this is
    what the module docstring promises. Uses the REAL check_urls module
    (no monkeypatching) since this exercises actual argparse output."""
    result = runner.invoke(webref_cli.app, ["check-urls", "--help"])

    assert result.exit_code == 0
    assert "--concurrency" in result.output
    assert "--per-host-concurrency" in result.output
    # Typer's own generic help renders subcommand help text in an "Options"
    # panel; argparse's --help never does, so its absence is a good proxy for
    # "this is check_urls.py's own help, not webref_cli's".
    assert "Options ─" not in result.output
