from notion_client import Client
from typing import Any, Dict, Optional
from ..config import settings
from ..utils.logger import logger


class NotionTool:
    def __init__(self):
        self.client = (
            Client(auth=settings.notion_api_key) if settings.notion_api_key else None
        )

    def create_job_entry(self, job: Dict) -> Optional[str]:
        if not self.client or not settings.notion_ep_jobs_db:
            return None
        try:
            page = self.client.pages.create(
                parent={"database_id": settings.notion_ep_jobs_db},
                properties={
                    "Title": {"title": [{"text": {"content": job.get("title", "")}}]},
                    "Company": {
                        "rich_text": [{"text": {"content": job.get("company", "")}}]
                    },
                    "Rate": {"rich_text": [{"text": {"content": job.get("rate", "")}}]},
                    "Status": {"select": {"name": job.get("status", "applied")}},
                },
            )
            return page.get("id")
        except Exception as e:
            logger.error(f"Notion create failed: {e}")
            return None
