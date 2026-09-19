from dotenv import load_dotenv
load_dotenv("topic-4-research-assistant/.env")

import asyncio
import json
import sys
import io
from pathlib import Path

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

ROOT_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT_DIR))

from src.core.researcher import run_research_pipeline

SIMPLIFIED_QUERIES = {
    "q1": "photosynthesis",
    "q2": "transformer deep learning",
    "q3": "2008 financial crisis",
    "q4": "fusion energy",
    "q5": "CRISPR gene editing",
}


async def main():
    questions_file = Path("data/research_questions.json")
    questions = json.loads(
        questions_file.read_text(encoding="utf-8")
    )["questions"]

    for item in questions:
        question = item["text"]
        simplified = SIMPLIFIED_QUERIES.get(item["id"], question)

        print("=" * 80)
        print(f"{item['id']}: {question}")
        print("=" * 80)

        try:
            result = await run_research_pipeline(
                question=simplified,
                sources_to_include=["wiki"],
            )
        except ValueError:
            print(f"(wiki-only failed, retrying full pipeline for: '{question}')")
            result = await run_research_pipeline(
                question=question,
                sources_to_include=["wiki", "arxiv", "web"],
            )

        print("\nAnswer:")
        print(result.answer)

        print("\nSources:")
        for citation in result.citations:
            source = citation.source
            print(f"[{citation.index}] {source.title}")
            print(f"    {source.url}")

        print()


if __name__ == "__main__":
    asyncio.run(main())