from typing import Dict, List
from ..utils.logger import logger


class GrantScraper:
    async def scrape_grants_gov(self, keywords: List[str]) -> List[Dict]:
        logger.info("Scraping Grants.gov")
        return []

    async def scrape_sba(self) -> List[Dict]:
        logger.info("Scraping SBA.gov")
        return []

    async def scrape_all(self) -> List[Dict]:
        results = []
        results.extend(await self.scrape_grants_gov(["veteran", "small business"]))
        results.extend(await self.scrape_sba())
        return results
