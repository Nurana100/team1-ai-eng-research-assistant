"""Tests for src/cli.py — argument parsing and input validation."""

import subprocess
import sys


def run_cli(*args):
    """Run the CLI as a subprocess and capture output."""
    result = subprocess.run(
        [sys.executable, "-m", "src.cli", "ask", *args],
        capture_output=True,
        text=True,
        timeout=15,
    )

    return result


def test_cli_rejects_empty_question():
    result = run_cli("")

    assert "cannot be empty" in result.stdout


def test_cli_rejects_oversized_question():
    long_question = "a" * 501
    result = run_cli(long_question)

    assert "too long" in result.stdout


def test_cli_rejects_invalid_source():
    result = run_cli("--sources", "bogus", "test question")

    assert "unknown source" in result.stdout.lower()


def test_cli_rejects_empty_sources_list():
    result = run_cli("--sources", ",", "test question")

    assert "no valid sources" in result.stdout.lower()