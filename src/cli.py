import argparse
import asyncio

from src.core.researcher import run_research_pipeline
from src.storage.repository import SQLiteStorage


def main():
    parser = argparse.ArgumentParser(prog="researcher")
    parser.add_argument("command", choices=["ask"])
    parser.add_argument("question")
    parser.add_argument("--no-cache", action="store_true")
    parser.add_argument("--sources", default="wiki,arxiv,web")
    args = parser.parse_args()

    if args.command == "ask":
        question = args.question.strip()

        if not question:
            print("Error: question cannot be empty.")
            return

        if len(question) > 500:
            print(f"Error: question is too long ({len(question)} chars). Max 500 characters.")
            return

        valid_sources = {"wiki", "arxiv", "web"}
        sources = [x.strip() for x in args.sources.split(",") if x.strip()]
        invalid = [s for s in sources if s not in valid_sources]

        if invalid:
            print(f"Error: unknown source(s) {invalid}. Valid options: wiki, arxiv, web.")
            return

        if not sources:
            print("Error: no valid sources specified.")
            return

        print(f"Question: {question}")
        print("Researching...")

        storage = SQLiteStorage("research_history.db")
        result = asyncio.run(
            run_research_pipeline(
                question=question,
                sources_to_include=sources,
                use_cache=not args.no_cache,
                storage=storage,
            )
        )

        print("\nAnswer:")
        print(result.answer)

        print("\nSources:")
        for citation in result.citations:
            source = citation.source
            print(f"[{citation.index}] {source.title}")
            print(f"    {source.url}")


if __name__ == "__main__":
    main()