from typing import Dict, List
from ..agents.filter_agent import FilterAgent
from ..agents.summarizer import SummarizerAgent
from ..tools.scraper import GrantScraper
from ..utils.logger import logger


class ResearchPipeline:
    def __init__(self):
        self.scraper = GrantScraper()
        self.filter_agent = FilterAgent()
        self.summarizer = SummarizerAgent()

    async def run(self, criteria: Dict) -> Dict:
        grants = await self.scraper.scrape_all()
        scored = await self.filter_agent.filter_grants(grants, criteria)
        relevant = [g for g in scored if g.get("relevance_score", 0) >= 70]
        return {
            "grants_found": len(grants),
            "grants_relevant": len(relevant),
            "grants_new": len(relevant),
            "grants": [
                {
                    "title": g.get("title", ""),
                    "source": g.get("source", ""),
                    "amount": g.get("amount", ""),
                    "deadline": g.get("deadline", ""),
                    "eligibility": g.get("eligibility", ""),
                    "application_url": g.get("application_url", ""),
                    "relevance_score": g.get("relevance_score", 0),
                    "notion_page_id": None,
                    "slack_notified": False,
                }
                for g in relevant
            ],
            "duplicates_skipped": 0,
        }
