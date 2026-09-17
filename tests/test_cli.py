"""Tests for src/cli.py — argument parsing and input validation."""

import subprocess
import sys
from unittest.mock import patch

from src import cli


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


def test_cli_passes_no_cache_option():
    mock_result = type(
        "Result",
        (),
        {
            "answer": "test answer",
            "citations": [],
        },
    )()

    with patch("src.cli.asyncio.run", return_value=mock_result) as mock_run:
        with patch("src.cli.run_research_pipeline") as mock_pipeline:
            mock_pipeline.return_value = mock_result

            with patch.object(
                sys,
                "argv",
                ["researcher", "ask", "test question", "--no-cache"],
            ):
                cli.main()

    mock_pipeline.assert_called_once_with(
        question="test question",
        sources_to_include=["wiki", "arxiv", "web"],
        use_cache=False,
    )