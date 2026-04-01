from typing import Dict, List
from ..utils.logger import logger


class JobScraper:
    async def scrape_indeed(
        self, query: str, location: str, max_results: int = 20
    ) -> List[Dict]:
        logger.info(f"Scraping Indeed: {query} in {location}")
        return []

    async def scrape_linkedin(
        self, query: str, location: str, max_results: int = 20
    ) -> List[Dict]:
        logger.info(f"Scraping LinkedIn: {query} in {location}")
        return []

    async def scrape_all(self, location: str, max_results: int = 20) -> List[Dict]:
        results = []
        results.extend(
            await self.scrape_indeed("executive protection", location, max_results)
        )
        results.extend(
            await self.scrape_linkedin("executive protection", location, max_results)
        )
        return results
