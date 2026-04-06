from typing import Any, Dict, List, Optional
from ..tools.notion_client import NotionTool
from ..tools.google_calendar import GoogleCalendarTool
from ..agents.conflict_resolver import ConflictResolverAgent
from ..utils.logger import logger
from datetime import datetime
import hashlib
from ..config import settings
from ..utils.calendar_mapping import notion_to_gcal, gcal_to_notion


class SyncEngine:
    def __init__(self):
        self.notion = NotionTool()
        self.calendar = GoogleCalendarTool()
        self.resolver = ConflictResolverAgent()

    def _hash_content(self, data: Dict) -> str:
        content = str(sorted(data.items()))
        return hashlib.sha256(content.encode()).hexdigest()[:16]

    def _check_if_changed(self, existing: Dict, new: Dict) -> bool:
        """Simple check to see if critical fields in Notion properties have changed.
        Focuses on Name, Date, Location, and Type.
        """
        try:
            # 1. Check Title (Name)
            new_title = new.get(settings.notion_title_key or "Name", {}).get("title", [{}])[0].get("text", {}).get("content", "")
            old_title = "".join(t.get("plain_text", "") for t in existing.get(settings.notion_title_key or "Name", {}).get("title", []))
            if new_title != old_title:
                return True

            # 2. Check Location
            new_loc = new.get(settings.notion_location_key or "Location", {}).get("rich_text", [{}])[0].get("text", {}).get("content", "")
            old_loc = "".join(t.get("plain_text", "") for t in existing.get(settings.notion_location_key or "Location", {}).get("rich_text", []))
            if new_loc != old_loc:
                return True

            # 3. Check Type
            new_type = new.get(settings.notion_type_key or "Type", {}).get("select", {}).get("name", "")
            old_type = existing.get(settings.notion_type_key or "Type", {}).get("select", {}).get("name", "")
            if new_type != old_type:
                return True

            # 4. Check Start Date
            new_start = new.get(settings.notion_start_date_key or "Start Date", {}).get("date", {}).get("start", "")
            old_start = existing.get(settings.notion_start_date_key or "Start Date", {}).get("date", {}).get("start", "")
            # Normalise comparison (some might have Z or +00:00)
            if new_start and old_start:
                if new_start.replace("Z", "+00:00")[:19] != old_start.replace("Z", "+00:00")[:19]:
                    return True
            elif new_start != old_start:
                return True
                
        except Exception as e:
            logger.warning(f"Change detection failed: {e}")
            return True # Fallback to update if uncertain
        return False

    async def initial_sync_calendar(self) -> Dict:
        """Initial push: create Google events for Notion rows lacking a sync ID.
        Returns a result dict similar to sync_calendar.
        """
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

            # Verify sync ID property exists
            db = self.notion.client.databases.retrieve(database_id=settings.notion_calendar_db)
            if settings.SYNC_ID_PROPERTY not in db.get("properties", {}):
                error_msg = f"Property '{settings.SYNC_ID_PROPERTY}' is missing in Notion database. Please add it as a 'Rich Text' property."
                logger.error(error_msg)
                result["status"] = "error"
                result["errors"].append(error_msg)
                return result

            # Query Notion for pages where hidden sync ID property is empty
            filter_dict = {
                "property": settings.SYNC_ID_PROPERTY,
                "rich_text": {"is_empty": True},
            }
            pages = self.notion.query_database(settings.notion_calendar_db, filter_dict)
            logger.info(f"Found {len(pages)} new pages to sync from Notion.")
            for page in pages:
                page_id = page.get("id")
                props = page.get("properties", {})
                gcal_event = notion_to_gcal(props)
                created = self.calendar.create_event(settings.google_calendar_id, gcal_event)
                if created and created.get("id"):
                    # Store sync ID back to Notion
                    sync_prop = {settings.SYNC_ID_PROPERTY: {"rich_text": [{"type": "text", "text": {"content": created["id"]}}]}}
                    self.notion.update_page(page_id, sync_prop)
                    result["records_synced"] += 1
                else:
                    result["errors"].append(f"Failed to create event for Notion page {page_id}")
        except Exception as e:
            result["status"] = "error"
            result["errors"].append(str(e))
            logger.error(f"Initial calendar sync failed: {e}")
        return result


    async def sync_calendar(self, direction: str) -> Dict:
        """Synchronize Google Calendar events (Source to Notion).
        Checks if GCal events exist in Notion (by Sync ID); if not, creates them.
        """
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

            events = self.calendar.list_events(settings.google_calendar_id)
            logger.info(f"Retrieved {len(events)} events from Google Calendar")
            
            for event in events:
                event_id = event.get("id")
                if not event_id:
                    continue
                
                # Check if this event already exists in Notion
                filter_dict = {
                    "property": settings.SYNC_ID_PROPERTY,
                    "rich_text": {"equals": event_id},
                }
                existing_pages = self.notion.query_database(settings.notion_calendar_db, filter_dict)
                
                if not existing_pages:
                    logger.info(f"Creating new Notion page for calendar event: {event.get('summary')}")
                    # Map GCal -> Notion
                    notion_props = gcal_to_notion(event)
                    # Include the Sync ID
                    notion_props[settings.SYNC_ID_PROPERTY] = {
                        "rich_text": [{"type": "text", "text": {"content": event_id}}]
                    }
                    
                    created = self.notion.create_page(settings.notion_calendar_db, notion_props)
                    if created:
                        result["records_synced"] += 1
                    else:
                        result["errors"].append(f"Failed to create Notion page for event {event_id}")
                else:
                    # Update existing page if changed
                    existing_page = existing_pages[0]
                    page_id = existing_page.get("id")
                    existing_props = existing_page.get("properties", {})
                    
                    # Map current GCal event to Notion structure
                    new_notion_props = gcal_to_notion(event)
                    
                    if self._check_if_changed(existing_props, new_notion_props):
                        logger.info(f"Updating Notion page for event: {event.get('summary')}")
                        updated = self.notion.update_page(page_id, new_notion_props)
                        if updated:
                            result["records_synced"] += 1
                        else:
                            result["errors"].append(f"Failed to update Notion page for event {event_id}")
                    else:
                        # No changes detected
                        pass
                    
            logger.info(f"Pull sync completed: {result['records_synced']} events added to Notion")
        except Exception as e:
            result["status"] = "error"
            result["errors"].append(str(e))
            logger.error(f"Calendar pull sync failed: {e}")
        return result

    async def full_sync(self, sources: List[str], direction: str) -> Dict:
        results = {}
        if "google_calendar" in sources:
            if direction == "notion_to_source" or direction == "bidirectional":
                # First, ensure new Notion items are pushed to GCal
                results["google_calendar"] = await self.initial_sync_calendar()
            
            if direction == "source_to_notion" or direction == "bidirectional":
                # Then (or instead), perform the pull/sync from GCal
                # For now, we merge results if bidirectional
                pull_result = await self.sync_calendar(direction)
                if direction == "bidirectional":
                    results["google_calendar"]["records_synced"] += pull_result.get("records_synced", 0)
                else:
                    results["google_calendar"] = pull_result
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
