from typing import Any, Dict, List, Optional, Callable
from ..tools.notion_client import NotionTool
from ..tools.google_calendar import GoogleCalendarTool
from ..utils.logger import logger
from datetime import datetime
import asyncio
from functools import wraps
from ..config import settings
from ..utils.calendar_mapping import notion_to_gcal, gcal_to_notion


def with_retry(retries: int = 3, delay: float = 1.0):
    """Retry decorator for API calls with exponential backoff."""

    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(*args, **kwargs) -> Any:
            last_exception = None
            for attempt in range(retries):
                try:
                    return await func(*args, **kwargs)
                except Exception as e:
                    last_exception = e
                    wait_time = delay * (2**attempt)
                    logger.warning(
                        f"Attempt {attempt + 1}/{retries} failed: {e}. Retrying in {wait_time}s..."
                    )
                    await asyncio.sleep(wait_time)
            logger.error(f"All {retries} attempts failed")
            raise last_exception

        return wrapper

    return decorator


class SyncEngine:
    def __init__(self):
        self.notion = NotionTool()
        self.calendar = GoogleCalendarTool()

    def _get_rich_text(self, props: Dict, key: str, default: str = "") -> str:
        """Safely extract rich text content from Notion properties."""
        return "".join(
            t.get("plain_text", "") for t in (props.get(key) or {}).get("rich_text", [])
        )

    def _get_title_text(self, props: Dict, key: str, default: str = "") -> str:
        """Safely extract title text from Notion properties."""
        return "".join(
            t.get("plain_text", "") for t in (props.get(key) or {}).get("title", [])
        )

    def _normalize_date(self, date_str: Optional[str]) -> Optional[str]:
        """Normalize date string to standard ISO format for consistent comparison."""
        if not date_str:
            return None
        try:
            # Handle both date-only and datetime strings
            # and normalize to UTC
            from datetime import timezone
            dt_str = date_str.replace("Z", "+00:00")
            dt = datetime.fromisoformat(dt_str)
            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=timezone.utc)
            else:
                dt = dt.astimezone(timezone.utc)
            # Standard string for comparison (ignore microseconds)
            return dt.strftime("%Y-%m-%dT%H:%M:%SZ")
        except Exception as e:
            logger.warning(f"Date normalization failed for '{date_str}': {e}")
            return date_str

    def _normalize_gcal_event(self, event: Dict[str, Any]) -> Dict[str, Any]:
        """Keep only comparable fields from Google event for change checks."""
        start = event.get("start", {}) or {}
        end = event.get("end", {}) or {}
        return {
            "summary": event.get("summary", ""),
            "description": event.get("description", ""),
            "location": event.get("location", ""),
            "start": {
                "dateTime": self._normalize_date(start.get("dateTime") or start.get("date")),
            },
            "end": {
                "dateTime": self._normalize_date(end.get("dateTime") or end.get("date")),
            },
        }

    def _check_if_changed(self, existing: Dict, new: Dict) -> bool:
        """Check if critical fields in Notion properties have changed."""
        try:
            # Define fields to check with their extractors
            title_key = settings.notion_title_key or "Name"
            location_key = settings.notion_location_key or "Location"
            type_key = settings.notion_type_key or "Type"
            start_date_key = settings.notion_start_date_key or "Start Date"
            end_date_key = settings.notion_end_date_key or "End Date"

            # Check Title
            if self._get_title_text(new, title_key) != self._get_title_text(
                existing, title_key
            ):
                return True

            # Check Location
            if self._get_rich_text(new, location_key) != self._get_rich_text(
                existing, location_key
            ):
                return True

            # Check Type
            new_type = ((new.get(type_key) or {}).get("select") or {}).get("name", "")
            old_type = ((existing.get(type_key) or {}).get("select") or {}).get("name", "")
            if new_type != old_type:
                return True

            # Check Start Date
            new_start = self._normalize_date(
                (new.get(start_date_key) or {}).get("date", {}).get("start")
            )
            old_start = self._normalize_date(
                (existing.get(start_date_key) or {}).get("date", {}).get("start")
            )
            if new_start != old_start:
                return True

            # Check End Date
            new_end = self._normalize_date(
                (new.get(end_date_key) or {}).get("date", {}).get("start")
            )
            old_end = self._normalize_date(
                (existing.get(end_date_key) or {}).get("date", {}).get("start")
            )
            if new_end != old_end:
                return True

        except Exception as e:
            logger.warning(f"Change detection failed: {e}")
            return True  # Fallback to update if uncertain
        return False

    @with_retry(retries=2)
    async def _create_calendar_event(
        self, calendar_id: str, event: Dict
    ) -> Optional[Dict]:
        """Create calendar event with retry logic."""
        return self.calendar.create_event(calendar_id, event)

    @with_retry(retries=2)
    async def _update_notion_page(self, page_id: str, props: Dict) -> Optional[Dict]:
        """Update Notion page with retry logic."""
        return self.notion.update_page(page_id, props)

    async def sync_calendar(self, direction: str = "bidirectional") -> Dict:
        """Unified Bi-directional Synchronization between Notion and Google Calendar.
        - Notion pages without Sync ID -> Created in GCal
        - GCal events without Notion page -> Created in Notion
        - Both exist -> Timestamp-based comparison and update
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

            # 1. Fetch data from both sources
            gcal_events = self.calendar.list_events(settings.google_calendar_id)
            notion_pages = self.notion.query_database(settings.notion_calendar_db)

            logger.info(
                f"Sync start: {len(gcal_events)} GCal events, {len(notion_pages)} Notion pages"
            )

            # 2. Map existing data by Sync ID / Event ID
            gcal_map = {e["id"]: e for e in gcal_events if e.get("id")}
            notion_map_by_sync_id = {}
            new_notion_pages = []

            for page in notion_pages:
                sync_id = self._get_rich_text(page["properties"], settings.SYNC_ID_PROPERTY)
                if sync_id:
                    notion_map_by_sync_id[sync_id] = page
                else:
                    new_notion_pages.append(page)

            # 3. Handle Notion pages NOT in GCal (New Notion items)
            if direction in ["notion_to_source", "bidirectional"]:
                for page in new_notion_pages:
                    logger.info(f"Creating GCal event for new Notion page: {page['id']}")
                    gcal_payload = notion_to_gcal(page["properties"])
                    created = await self._create_calendar_event(
                        settings.google_calendar_id, gcal_payload
                    )
                    if created and created.get("id"):
                        await self._update_notion_page(
                            page["id"],
                            {
                                settings.SYNC_ID_PROPERTY: {
                                    "rich_text": [
                                        {
                                            "type": "text",
                                            "text": {"content": created["id"]},
                                        }
                                    ]
                                }
                            },
                        )
                        result["records_synced"] += 1

            # 4. Handle GCal events NOT in Notion (New Calendar items)
            if direction in ["source_to_notion", "bidirectional"]:
                for event_id, event in gcal_map.items():
                    if event_id not in notion_map_by_sync_id:
                        logger.info(f"Creating Notion page for new GCal event: {event.get('summary')}")
                        notion_props = gcal_to_notion(event)
                        notion_props[settings.SYNC_ID_PROPERTY] = {
                            "rich_text": [{"type": "text", "text": {"content": event_id}}]
                        }
                        created = self.notion.create_page(
                            settings.notion_calendar_db, notion_props
                        )
                        if created:
                            result["records_synced"] += 1
                            # Add to map so we don't process it again in step 5
                            notion_map_by_sync_id[event_id] = created

            # 5. Handle updates for items that exist in both
            # Skip items we just created to avoid redundant processing
            processed_ids = set()

            for event_id, event in gcal_map.items():
                if event_id in notion_map_by_sync_id:
                    page = notion_map_by_sync_id[event_id]
                    page_id = page["id"]
                    
                    # Prevent double processing
                    if page_id in processed_ids:
                        continue
                    processed_ids.add(page_id)

                    # Get timestamps
                    notion_time = self._normalize_date(page.get("last_edited_time"))
                    gcal_time = self._normalize_date(event.get("updated"))
                    
                    if not notion_time or not gcal_time:
                        continue

                    # Compare and update based on direction and timestamps
                    if notion_time > gcal_time:
                        # Notion is newer
                        if direction in ["notion_to_source", "bidirectional"]:
                            desired_gcal = notion_to_gcal(page["properties"])
                            comparable_current = self._normalize_gcal_event(event)
                            comparable_desired = self._normalize_gcal_event(desired_gcal)
                            
                            if comparable_current != comparable_desired:
                                logger.info(f"Updating GCal from Notion (newer): {event_id}")
                                self.calendar.update_event(
                                    settings.google_calendar_id, event_id, desired_gcal
                                )
                                result["records_synced"] += 1
                    
                    elif gcal_time > notion_time:
                        # GCal is newer
                        if direction in ["source_to_notion", "bidirectional"]:
                            desired_notion = gcal_to_notion(event)
                            if self._check_if_changed(page["properties"], desired_notion):
                                logger.info(f"Updating Notion from GCal (newer): {event.get('summary')}")
                                await self._update_notion_page(page["id"], desired_notion)
                                result["records_synced"] += 1
                            else:
                                logger.debug(f"No changes detected for: {event.get('summary')}")

            logger.info(f"Sync completed: {result['records_synced']} records processed")
        except Exception as e:
            result["status"] = "error"
            result["errors"].append(str(e))
            logger.error(f"Sync failed: {e}")
        return result

    def _create_empty_result(self, status: str = "not_implemented") -> Dict[str, Any]:
        """Create standardized result dictionary."""
        return {
            "status": status,
            "records_synced": 0,
            "conflicts_resolved": 0,
            "errors": [],
            "last_sync": datetime.utcnow().isoformat() + "Z",
        }

    async def full_sync(self, sources: List[str], direction: str) -> Dict:
        results = {}

        if "google_calendar" in sources:
            results["google_calendar"] = await self.sync_calendar(direction)

        # Handle other sources
        for source in ["google_drive", "gmail"]:
            if source in sources:
                results[source] = self._create_empty_result()

        return results
