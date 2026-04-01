from typing import Dict, List
from ..agents.classifier import ClassifierAgent
from ..agents.resume_generator import ResumeGeneratorAgent
from ..tools.scraper import RemoteJobScraper
from ..utils.logger import logger
from collections import Counter


class JobPipeline:
    def __init__(self):
        self.scraper = RemoteJobScraper()
        self.classifier = ClassifierAgent()
        self.resume_gen = ResumeGeneratorAgent()

    async def run(
        self, role_types: List[str], max_applications: int, generate_resume: bool
    ) -> Dict:
        jobs = await self.scraper.scrape_all()
        classified = await self.classifier.classify(jobs)

        role_counts = Counter(j.get("role_type", "Other") for j in classified)
        filtered = [j for j in classified if j.get("role_type") in role_types]

        applications = []
        for job in filtered[:max_applications]:
            summary = ""
            if generate_resume:
                summary = await self.resume_gen.generate_summary(job)
            applications.append(
                {
                    "title": job.get("title", ""),
                    "company": job.get("company", ""),
                    "source": "scraped",
                    "match_score": int(job.get("confidence", 0.5) * 100),
                    "resume_generated": bool(summary),
                    "resume_path": "",
                    "cover_letter_path": "",
                    "status": "submitted",
                    "notion_page_id": None,
                }
            )

        return {
            "listings_scraped": len(jobs),
            "roles_classified": dict(role_counts),
            "applications_submitted": len(applications),
            "applications": applications,
            "weekly_report_generated": "",
        }
