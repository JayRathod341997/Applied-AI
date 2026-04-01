from notion_client import Client
from typing import Any, Dict, List, Optional
from ..config import settings
from ..utils.logger import logger


class NotionTool:
    def __init__(self):
        self.client = (
            Client(auth=settings.notion_api_key) if settings.notion_api_key else None
        )

    def query_database(
        self, database_id: str, filter_dict: Optional[Dict] = None
    ) -> List[Dict]:
        if not self.client:
            return []
        try:
            kwargs: Dict[str, Any] = {"database_id": database_id}
            if filter_dict:
                kwargs["filter"] = filter_dict
            return self.client.databases.query(**kwargs).get("results", [])
        except Exception as e:
            logger.error(f"Notion query failed: {e}")
            return []

    def create_page(self, database_id: str, properties: Dict) -> Optional[Dict]:
        if not self.client:
            return None
        try:
            return self.client.pages.create(
                parent={"database_id": database_id}, properties=properties
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
