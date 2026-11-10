"""Shared pytest setup for testing writing-skill-web's scripts/*.py templates.

These tests exercise the templates exactly as they ship in this skill's
scripts/ directory. This is intentionally the ONLY place in the
writing-skill-web family that carries a test suite: skills DERIVED from these
templates (by copying scripts/*.py into their own directory) do not get a
copy of tests/ -- see tests/README.md for why.
"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

TESTS_DIR = Path(__file__).resolve().parent
FIXTURES_DIR = TESTS_DIR / "fixtures"
SCRIPTS_DIR = TESTS_DIR.parent / "scripts"

# Explicit sys.path insertion (rather than relying solely on the workspace's
# editable install) so these tests also run standalone, e.g.
# `python -m pytest skills/plugins/cc-knowledge/skills/writing-skill-web/tests` without a prior
# `uv sync` -- same approach as tools/tav-cli/tests.
sys.path.insert(0, str(SCRIPTS_DIR))


@pytest.fixture
def fixtures_dir() -> Path:
    return FIXTURES_DIR
