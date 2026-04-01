from typing import Any, Dict, List, Optional
from ..config import settings
from ..utils.logger import logger


class GoogleCalendarTool:
    def __init__(self):
        self.service = None
        self._init_service()

    def _init_service(self):
        try:
            from google.oauth2 import service_account
            from googleapiclient.discovery import build

            if settings.google_service_account_json:
                credentials = service_account.Credentials.from_service_account_file(
                    settings.google_service_account_json,
                    scopes=["https://www.googleapis.com/auth/calendar"],
                )
                self.service = build("calendar", "v3", credentials=credentials)
        except Exception as e:
            logger.warning(f"Google Calendar not configured: {e}")

    def list_events(
        self, calendar_id: str = "primary", max_results: int = 100
    ) -> List[Dict]:
        if not self.service:
            return []
        try:
            result = (
                self.service.events()
                .list(
                    calendarId=calendar_id,
                    maxResults=max_results,
                    singleEvents=True,
                    orderBy="startTime",
                )
                .execute()
            )
            return result.get("items", [])
        except Exception as e:
            logger.error(f"Calendar list failed: {e}")
            return []

    def create_event(self, calendar_id: str, event: Dict) -> Optional[Dict]:
        if not self.service:
            return None
        try:
            return (
                self.service.events()
                .insert(calendarId=calendar_id, body=event)
                .execute()
            )
        except Exception as e:
            logger.error(f"Calendar create failed: {e}")
            return None

    def update_event(
        self, calendar_id: str, event_id: str, event: Dict
    ) -> Optional[Dict]:
        if not self.service:
            return None
        try:
            return (
                self.service.events()
                .update(calendarId=calendar_id, eventId=event_id, body=event)
                .execute()
            )
        except Exception as e:
            logger.error(f"Calendar update failed: {e}")
            return None
