from notion_client import Client
from typing import Any, Dict, List, Optional
from ..config import settings
from ..utils.logger import logger


from notion_client import Client
from typing import Any, Dict, List, Optional
import logging

logger = logging.getLogger(__name__)


class NotionTool:
    def __init__(self):
        self.client = (
            Client(auth=settings.notion_api_key, notion_version="2022-06-28")
            if settings.notion_api_key
            else None
        )

    def query_database(
        self, database_id: str, filter_dict: Optional[Dict] = None
    ) -> List[Dict]:
        if not self.client:
            logger.warning("Notion client not configured")
            return []
        try:
            results = []
            has_more = True
            next_cursor = None

            while has_more:
                kwargs: Dict[str, Any] = {
                    "database_id": database_id,
                }
                if filter_dict:
                    kwargs["filter"] = filter_dict
                if next_cursor:
                    kwargs["start_cursor"] = next_cursor

                response = self.client.databases.query(**kwargs)
                results.extend(response.get("results", []))
                has_more = response.get("has_more", False)
                next_cursor = response.get("next_cursor")

            return results
        except Exception as e:
            logger.error(f"Notion query failed: {e}")
            return []

    def create_page(self, database_id: str, properties: Dict) -> Optional[Dict]:
        if not self.client:
            return None
        try:
            return self.client.pages.create(
                parent={"database_id": database_id},
                properties=properties,
            )
        except Exception as e:
            logger.error(f"Notion create failed: {e}")
            return None

    def update_page(self, page_id: str, properties: Dict) -> Optional[Dict]:
        if not self.client:
            return None
        try:
            return self.client.pages.update(page_id=page_id, properties=properties)
        except Exception as e:
            logger.error(f"Notion update failed: {e}")
            return None

    def get_page(self, page_id: str) -> Optional[Dict]:
        if not self.client:
            return None
        try:
            return self.client.pages.retrieve(page_id=page_id)
        except Exception as e:
            logger.error(f"Notion retrieve failed: {e}")
            return None

    def archive_page(self, page_id: str) -> bool:
        if not self.client:
            return False
        try:
            self.client.pages.update(page_id=page_id, archived=True)
            return True
        except Exception as e:
            logger.error(f"Notion archive failed: {e}")
            return False