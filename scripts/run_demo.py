import asyncio
import json
from pathlib import Path
import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT_DIR))

from src.core.researcher import run_research_pipeline


async def main():
    questions_file = Path("data/research_questions.json")
    questions = json.loads(
        questions_file.read_text(encoding="utf-8")
    )["questions"]

    for item in questions:
        question = item["text"]

        print("=" * 80)
        print(f"{item['id']}: {question}")
        print("=" * 80)

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
