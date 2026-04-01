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

            if settings.google_application_credentials:
                credentials = service_account.Credentials.from_service_account_file(
                    settings.google_application_credentials,
                    scopes=["https://www.googleapis.com/auth/calendar"],
                )
                self.service = build("calendar", "v3", credentials=credentials)
        except Exception as e:
            logger.warning(f"Google Calendar not configured: {e}")

    def create_event(
        self, calendar_id: str, event: Dict, reminder_minutes: int = 30
    ) -> Optional[str]:
        if not self.service:
            return None
        try:
            event_body = {
                "summary": event.get("title", "Shift"),
                "location": event.get("location", ""),
                "start": {
                    "dateTime": f"{event['date']}T{event['start_time']}:00",
                    "timeZone": "America/Los_Angeles",
                },
                "end": {
                    "dateTime": f"{event['date']}T{event['end_time']}:00",
                    "timeZone": "America/Los_Angeles",
                },
                "reminders": {
                    "useDefault": False,
                    "overrides": [
                        {"method": "popup", "minutes": reminder_minutes},
                    ],
                },
            }
            created = (
                self.service.events()
                .insert(calendarId=calendar_id, body=event_body)
                .execute()
            )
            return created.get("id")
        except Exception as e:
            logger.error(f"Calendar create failed: {e}")
            return None

    def list_events(
        self, calendar_id: str, time_min: str = None, time_max: str = None
    ) -> List[Dict]:
        if not self.service:
            return []
        try:
            kwargs: Dict[str, Any] = {
                "calendarId": calendar_id,
                "singleEvents": True,
                "orderBy": "startTime",
            }
            if time_min:
                kwargs["timeMin"] = time_min
            if time_max:
                kwargs["timeMax"] = time_max
            result = self.service.events().list(**kwargs).execute()
            return result.get("items", [])
        except Exception as e:
            logger.error(f"Calendar list failed: {e}")
            return []
