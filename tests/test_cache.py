"""Tests for the TTL cache."""

import time
import pytest

from src.services.cache import TTLCache


def test_cache_returns_none_when_empty():
    cache = TTLCache(ttl_seconds=60)
    assert cache.get("wiki", "anything") is None


def test_cache_stores_and_retrieves():
    cache = TTLCache(ttl_seconds=60)
    cache.set("wiki", "quantum computing", ["result"])
    assert cache.get("wiki", "quantum computing") == ["result"]


def test_cache_is_case_and_whitespace_insensitive():
    cache = TTLCache(ttl_seconds=60)
    cache.set("wiki", "Quantum Computing", ["result"])
    assert cache.get("wiki", "  quantum computing  ") == ["result"]


def test_cache_expires_after_ttl():
    cache = TTLCache(ttl_seconds=0.05)
    cache.set("wiki", "test", ["result"])
    time.sleep(0.1)
    assert cache.get("wiki", "test") is None


def test_cache_different_sources_dont_collide():
    cache = TTLCache(ttl_seconds=60)
    cache.set("wiki", "test", ["wiki_result"])
    cache.set("arxiv", "test", ["arxiv_result"])
    assert cache.get("wiki", "test") == ["wiki_result"]
    assert cache.get("arxiv", "test") == ["arxiv_result"]