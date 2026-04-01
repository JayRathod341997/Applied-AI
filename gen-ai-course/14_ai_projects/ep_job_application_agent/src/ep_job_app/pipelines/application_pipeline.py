from typing import Dict, List
from ..agents.filter_agent import FilterAgent
from ..agents.cover_letter_agent import CoverLetterAgent
from ..tools.scraper import JobScraper
from ..tools.notion_tool import NotionTool
from ..utils.logger import logger
from datetime import datetime


class ApplicationPipeline:
    def __init__(self):
        self.scraper = JobScraper()
        self.filter_agent = FilterAgent()
        self.cover_letter_agent = CoverLetterAgent()
        self.notion = NotionTool()

    async def run(
        self, min_rate: int = 600, location: str = "SF Bay Area", max_results: int = 20
    ) -> Dict:
        jobs = await self.scraper.scrape_all(location, max_results)
        qualified = await self.filter_agent.filter_jobs(jobs, min_rate, location)

        applications = []
        for job in qualified[:max_results]:
            cover_letter = await self.cover_letter_agent.generate(job)
            notion_id = self.notion.create_job_entry(job)
            applications.append(
                {
                    "title": job.get("title", ""),
                    "company": job.get("company", ""),
                    "rate": job.get("rate", ""),
                    "location": job.get("location", ""),
                    "status": "applied",
                    "cover_letter_generated": bool(cover_letter),
                    "notion_page_id": notion_id,
                    "applied_at": datetime.utcnow().isoformat() + "Z",
                }
            )

        return {
            "jobs_found": len(jobs),
            "jobs_qualified": len(qualified),
            "applications_submitted": len(applications),
            "applications": applications,
            "skipped_duplicates": 0,
            "errors": [],
        }
