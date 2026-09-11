import asyncio

class ResearchService:

    def __init__(self):
        pass

    async def fetch_all(self, question: str) -> dict:
        # TODO: call ai.sources.fetch_wikipedia(question)
        # TODO: call ai.sources.fetch_arxiv(question)
        # TODO: call ai.sources.fetch_web(question)
        return {
            "wikipedia": [],
            "arxiv": [],
            "web": [],
        }

    async def answer(self, question: str) -> str:
        sources = await self.fetch_all(question)
        # TODO: call ai.synthesizer.synthesize(question, sources)
        return f"Placeholder answer for: {question}"