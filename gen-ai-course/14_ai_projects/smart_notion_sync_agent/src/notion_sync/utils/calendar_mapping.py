"""Utility functions for mapping between Notion page properties and Google Calendar event payloads.

The mapping is based on the data model described in the implementation plan:
- Notion "Name" (title) -> Google Calendar "summary"
- Notion "Date" (date) -> Google Calendar "start" / "end" (dateTime in ISO format)
- Notion "Location" -> Google Calendar "location"
- Notion "Type" (select) -> Google Calendar "description" (used for categorisation)
- Hidden sync ID property is stored in Notion but not sent to Google.

Both functions accept a dictionary representing the Notion page properties as returned by the Notion API
and produce a dictionary suitable for the Google Calendar API.
"""

from datetime import datetime, timezone
from typing import Dict, Any
from ..config import settings

# Google Calendar expects ISO8601 timestamps with timezone information
def _to_iso(dt_str: str) -> str:
    """Convert a Notion date string (which may be a date or datetime) to an ISO8601 string.
    Notion returns dates in the format ``YYYY-MM-DD`` or ``YYYY-MM-DDTHH:MM:SSZ``.
    We normalise everything to UTC.
    """
    try:
        # Try full datetime first
        dt = datetime.fromisoformat(dt_str.rstrip("Z"))
    except ValueError:
        # Fallback to date only – treat as all‑day event
        dt = datetime.fromisoformat(dt_str)
    # Ensure timezone aware (UTC)
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.isoformat()

def notion_to_gcal(page: Dict[str, Any]) -> Dict[str, Any]:
    """Map a Notion page (properties dict) to a Google Calendar event payload.

    The *page* argument should be the ``properties`` field of a Notion page object.
    """
    # Title – Notion stores title as a list of rich text objects
    title_prop = page.get(settings.notion_title_key) or {}
    title = "".join(t.get("plain_text", "") for t in title_prop.get("title", []))

    # Date – Notion stores date objects under ``date``
    start_date_prop = (page.get(settings.notion_start_date_key) or {}).get("date") or {}
    end_date_prop = (page.get(settings.notion_end_date_key) or {}).get("date") or {}
    start_iso = _to_iso(start_date_prop.get("start")) if start_date_prop.get("start") else None
    end_iso = _to_iso(end_date_prop.get("start")) if end_date_prop.get("start") else None

    # Location – plain text
    location_prop = page.get(settings.notion_location_key) or {}
    location = "".join(t.get("plain_text", "") for t in location_prop.get("rich_text", []))

    # Type – select name used as description/category
    type_prop = page.get(settings.notion_type_key) or {}
    type_desc = (type_prop.get("select") or {}).get("name", "")

    event: Dict[str, Any] = {
        "summary": title,
        "description": type_desc,
        "location": location,
    }
    if start_iso:
        event["start"] = {"dateTime": start_iso, "timeZone": "UTC"}
    if end_iso:
        event["end"] = {"dateTime": end_iso, "timeZone": "UTC"}
    return event

def gcal_to_notion(event: Dict[str, Any]) -> Dict[str, Any]:
    """Map a Google Calendar event back to Notion properties.

    This is used for the bi‑directional update path.
    """
    # Title
    title = event.get("summary", "")
    # Description (used for Type)
    type_desc = event.get("description", "")
    # Location
    location = event.get("location", "")
    # Dates – Google returns ``dateTime`` for timed events and ``date`` for all-day events
    start_iso = event.get("start", {}).get("dateTime") or event.get("start", {}).get("date")
    end_iso = event.get("end", {}).get("dateTime") or event.get("end", {}).get("date")

    # Build Notion property structure matching the expected schema
    notion_props: Dict[str, Any] = {
        settings.notion_title_key: {"title": [{"type": "text", "text": {"content": title}}]},
        settings.notion_location_key: {"rich_text": [{"type": "text", "text": {"content": location}}]},
    }
    
    # Only add the Type select property if description exists
    if type_desc:
        notion_props[settings.notion_type_key] = {"select": {"name": type_desc}}
    if start_iso:
        notion_props[settings.notion_start_date_key] = {"date": {"start": start_iso}}
    if end_iso:
        notion_props[settings.notion_end_date_key] = {"date": {"start": end_iso}}
    return notion_props

