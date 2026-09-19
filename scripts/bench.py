"""Benchmark: sequential vs parallel source fetching.

Usage:  python scripts/bench.py
"""

from __future__ import annotations

import asyncio
import statistics
import sys
import time
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import httpx  # noqa: E402

from src.services.ai_service import AIService  # noqa: E402

QUERY = "Quantum Entanglement"
RUNS = 3
TIMEOUT = 15.0


async def timed(name, coro):
    start = time.perf_counter()
    try:
        await coro
        ok = True
    except Exception:
        ok = False
    return name, time.perf_counter() - start, ok


def make_calls(svc, client):
    return [
        ("wikipedia", lambda: svc.fetch_wikipedia(QUERY, max_results=3, client=client)),
        ("arxiv", lambda: svc.fetch_arxiv(QUERY, max_results=3, client=client)),
        ("web", lambda: svc.fetch_web(QUERY, max_results=3, client=client)),
    ]


async def run_once():
    svc = AIService(timeout_seconds=TIMEOUT, use_cache=False)
    headers = {"User-Agent": "team1-research-assistant/1.0 (AI-ENG-110 coursework)"}
    async with httpx.AsyncClient(
        timeout=TIMEOUT, follow_redirects=True, headers=headers
    ) as client:
        calls = make_calls(svc, client)

        start = time.perf_counter()
        seq = [await timed(n, f()) for n, f in calls]
        seq_total = time.perf_counter() - start

        start = time.perf_counter()
        par = await asyncio.gather(*(timed(n, f()) for n, f in calls))
        par_total = time.perf_counter() - start

    return seq, seq_total, par, par_total


async def main():
    seq_totals, par_totals = [], []
    for i in range(1, RUNS + 1):
        seq, s_total, par, p_total = await run_once()
        seq_totals.append(s_total)
        par_totals.append(p_total)
        detail = ", ".join(f"{n}={t:.2f}s{'' if ok else '(failed)'}" for n, t, ok in seq)
        print(f"run {i}: sequential={s_total:.2f}s parallel={p_total:.2f}s  [{detail}]")

    s = statistics.mean(seq_totals)
    p = statistics.mean(par_totals)
    print()
    print(f"Query: {QUERY!r}, runs: {RUNS}, cache: off")
    print("| Mode       | Mean wall-clock (s) |")
    print("|------------|---------------------|")
    print(f"| Sequential | {s:.2f}                |")
    print(f"| Parallel   | {p:.2f}                |")
    print(f"Speedup: {s / p:.2f}x")


if __name__ == "__main__":
    asyncio.run(main())