from typing import Dict, List
from ..utils.logger import logger


class RemoteJobScraper:
    async def scrape_weworkremotely(self, max_results: int = 50) -> List[Dict]:
        logger.info("Scraping We Work Remotely")
        return []

    async def scrape_remoteok(self, max_results: int = 50) -> List[Dict]:
        logger.info("Scraping Remote OK")
        return []

    async def scrape_remotive(self, max_results: int = 50) -> List[Dict]:
        logger.info("Scraping Remotive")
        return []

    async def scrape_all(self, max_results: int = 50) -> List[Dict]:
        results = []
        results.extend(await self.scrape_weworkremotely(max_results))
        results.extend(await self.scrape_remoteok(max_results))
        results.extend(await self.scrape_remotive(max_results))
        return results
