import argparse
import asyncio

from src.core.researcher import run_research_pipeline


def main():
    parser = argparse.ArgumentParser(prog="researcher")
    parser.add_argument("command", choices=["ask"])
    parser.add_argument("question")
    parser.add_argument("--no-cache", action="store_true")
    parser.add_argument("--sources", default="wiki,arxiv,web")
    args = parser.parse_args()

    if args.command == "ask":
        sources = [x.strip() for x in args.sources.split(",") if x.strip()]

        print(f"Question: {args.question}")
        print("Researching...")

        result = asyncio.run(
            run_research_pipeline(
                question=args.question,
                sources_to_include=sources,
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
