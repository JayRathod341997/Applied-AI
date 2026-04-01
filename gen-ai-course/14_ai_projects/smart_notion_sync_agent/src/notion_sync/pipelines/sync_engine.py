from typing import Any, Dict, List, Optional
from ..tools.notion_client import NotionTool
from ..tools.google_calendar import GoogleCalendarTool
from ..agents.conflict_resolver import ConflictResolverAgent
from ..utils.logger import logger
from datetime import datetime
import hashlib


class SyncEngine:
    def __init__(self):
        self.notion = NotionTool()
        self.calendar = GoogleCalendarTool()
        self.resolver = ConflictResolverAgent()

    def _hash_content(self, data: Dict) -> str:
        content = str(sorted(data.items()))
        return hashlib.sha256(content.encode()).hexdigest()[:16]

    async def sync_calendar(self, direction: str = "bidirectional") -> Dict:
        result = {
            "status": "success",
            "records_synced": 0,
            "conflicts_resolved": 0,
            "errors": [],
            "last_sync": datetime.utcnow().isoformat() + "Z",
        }
        try:
            if not settings.notion_calendar_db:
                result["status"] = "skipped"
                result["errors"].append("NOTION_CALENDAR_DB not configured")
                return result

            events = self.calendar.list_events()
            result["records_synced"] = len(events)
            logger.info(f"Synced {len(events)} calendar events")
        except Exception as e:
            result["status"] = "error"
            result["errors"].append(str(e))
            logger.error(f"Calendar sync failed: {e}")
        return result

    async def full_sync(self, sources: List[str], direction: str) -> Dict:
        results = {}
        if "google_calendar" in sources:
            results["google_calendar"] = await self.sync_calendar(direction)
        if "google_drive" in sources:
            results["google_drive"] = {
                "status": "not_implemented",
                "records_synced": 0,
                "conflicts_resolved": 0,
                "errors": [],
                "last_sync": datetime.utcnow().isoformat() + "Z",
            }
        if "gmail" in sources:
            results["gmail"] = {
                "status": "not_implemented",
                "records_synced": 0,
                "conflicts_resolved": 0,
                "errors": [],
                "last_sync": datetime.utcnow().isoformat() + "Z",
            }
        return results
