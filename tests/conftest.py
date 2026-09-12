"""Shared test scaffolding for the research assistant.

The suite is graded on running offline, so nothing in here may touch the
network or read a real API key.
"""


from __future__ import annotations

import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

CREDENTIAL_ENV_VARS = (
    "ANTHROPIC_API_KEY",
    "OPENAI_API_KEY",
    "GOOGLE_API_KEY",
    "TAVILY_API_KEY",
    "SERPER_API_KEY",
)


@pytest.fixture(autouse=True)
def scrub_credentials(monkeypatch: pytest.MonkeyPatch) -> None:
    """Hide every real key from the tests.

    Autouse on purpose: if a stub is ever forgotten, the call underneath fails
    with a missing-key error instead of quietly spending someone's quota.
    """
    for name in CREDENTIAL_ENV_VARS:
        monkeypatch.delenv(name, raising=False)
