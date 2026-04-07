from typing import Any, Dict, List, Optional, Callable
from ..tools.notion_client import NotionTool
from ..tools.google_calendar import GoogleCalendarTool
from ..agents.conflict_resolver import ConflictResolverAgent
from ..utils.logger import logger
from datetime import datetime
import hashlib
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
        self.resolver = ConflictResolverAgent()

    def _hash_content(self, data: Dict) -> str:
        content = str(sorted(data.items()))
        return hashlib.sha256(content.encode()).hexdigest()[:16]

    def _get_rich_text(self, props: Dict, key: str, default: str = "") -> str:
        """Safely extract rich text content from Notion properties."""
        return "".join(
            t.get("plain_text", "") for t in props.get(key, {}).get("rich_text", [])
        )

    def _get_title_text(self, props: Dict, key: str, default: str = "") -> str:
        """Safely extract title text from Notion properties."""
        return "".join(
            t.get("plain_text", "") for t in props.get(key, {}).get("title", [])
        )

    def _normalize_date(self, date_str: Optional[str]) -> Optional[str]:
        """Normalize date string for consistent comparison."""
        if not date_str:
            return None
        return date_str.replace("Z", "+00:00")[:19]

    def _check_if_changed(self, existing: Dict, new: Dict) -> bool:
        """Check if critical fields in Notion properties have changed."""
        try:
            # Define fields to check with their extractors
            title_key = settings.notion_title_key or "Name"
            location_key = settings.notion_location_key or "Location"
            type_key = settings.notion_type_key or "Type"
            start_date_key = settings.notion_start_date_key or "Start Date"

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
            new_type = new.get(type_key, {}).get("select", {}).get("name", "")
            old_type = existing.get(type_key, {}).get("select", {}).get("name", "")
            if new_type != old_type:
                return True

            # Check Start Date
            new_start = self._normalize_date(
                new.get(start_date_key, {}).get("date", {}).get("start")
            )
            old_start = self._normalize_date(
                existing.get(start_date_key, {}).get("date", {}).get("start")
            )
            if new_start != old_start:
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
            db = self.notion.client.databases.retrieve(
                database_id=settings.notion_calendar_db
            )
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
            events = self.notion.query_database(settings.notion_calendar_db, filter_dict)
            logger.info(f"Found {len(events)} new events to sync from Notion.")

            # Process in batches to avoid rate limits
            batch_size = 5
            for i in range(0, len(events), batch_size):
                batch = events[i : i + batch_size]
                tasks = []

                for page in batch:
                    page_id = page.get("id")
                    props = page.get("properties", {})
                    gcal_event = notion_to_gcal(props)

                    async def process_page(pid: str, event: Dict) -> bool:
                        try:
                            created = await self._create_calendar_event(
                                settings.google_calendar_id, event
                            )
                            if created and created.get("id"):
                                sync_prop = {
                                    settings.SYNC_ID_PROPERTY: {
                                        "rich_text": [
                                            {
                                                "type": "text",
                                                "text": {"content": created["id"]},
                                            }
                                        ]
                                    }
                                }
                                await self._update_notion_page(pid, sync_prop)
                                return True
                            return False
                        except Exception as e:
                            result["errors"].append(
                                f"Failed to create event for page {pid}: {str(e)}"
                            )
                            return False

                    tasks.append(process_page(page_id, gcal_event))

                # Wait for batch to complete
                batch_results = await asyncio.gather(*tasks)
                result["records_synced"] += sum(batch_results)

                # Rate limit delay between batches
                if i + batch_size < len(events):
                    await asyncio.sleep(0.5)

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

            # Filter valid events first
            valid_events = [e for e in events if e.get("id")]

            # Pre-fetch all existing sync IDs from Notion in one query
            all_pages = self.notion.query_database(settings.notion_calendar_db)
            sync_id_map = {
                self._get_rich_text(page["properties"], settings.SYNC_ID_PROPERTY): page
                for page in all_pages
                if self._get_rich_text(page["properties"], settings.SYNC_ID_PROPERTY)
            }

            for event in valid_events:
                event_id = event["id"]
                existing_page = sync_id_map.get(event_id)

                if not existing_page:
                    logger.info(
                        f"Creating new Notion page for calendar event: {event.get('summary')}"
                    )
                    notion_props = gcal_to_notion(event)
                    notion_props[settings.SYNC_ID_PROPERTY] = {
                        "rich_text": [{"type": "text", "text": {"content": event_id}}]
                    }

                    created = self.notion.create_page(
                        settings.notion_calendar_db, notion_props
                    )
                    if created:
                        result["records_synced"] += 1
                    else:
                        result["errors"].append(
                            f"Failed to create Notion page for event {event_id}"
                        )
                else:
                    page_id = existing_page["id"]
                    existing_props = existing_page["properties"]
                    new_notion_props = gcal_to_notion(event)

                    if self._check_if_changed(existing_props, new_notion_props):
                        logger.info(
                            f"Updating Notion page for event: {event.get('summary')}"
                        )
                        updated = self.notion.update_page(page_id, new_notion_props)
                        if updated:
                            result["records_synced"] += 1
                        else:
                            result["errors"].append(
                                f"Failed to update Notion page for event {event_id}"
                            )

            logger.info(
                f"Pull sync completed: {result['records_synced']} events processed"
            )
        except Exception as e:
            result["status"] = "error"
            result["errors"].append(str(e))
            logger.error(f"Calendar pull sync failed: {e}")
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
            if direction == "notion_to_source" or direction == "bidirectional":
                results["google_calendar"] = await self.initial_sync_calendar()

            if direction == "source_to_notion" or direction == "bidirectional":
                pull_result = await self.sync_calendar(direction)
                if direction == "bidirectional":
                    results["google_calendar"]["records_synced"] += pull_result.get(
                        "records_synced", 0
                    )
                    results["google_calendar"]["errors"].extend(
                        pull_result.get("errors", [])
                    )
                else:
                    results["google_calendar"] = pull_result

        # Handle other sources
        for source in ["google_drive", "gmail"]:
            if source in sources:
                results[source] = self._create_empty_result()

        return results
