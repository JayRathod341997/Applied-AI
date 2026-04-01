from typing import Any, Dict, List, Optional
from ..config import settings
from ..utils.logger import logger


class GmailTool:
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
                    scopes=["https://www.googleapis.com/auth/gmail.modify"],
                )
                self.service = build("gmail", "v1", credentials=credentials)
        except Exception as e:
            logger.warning(f"Gmail not configured: {e}")

    def list_messages(
        self, query: str = "is:unread", max_results: int = 50
    ) -> List[Dict]:
        if not self.service:
            return []
        try:
            result = (
                self.service.users()
                .messages()
                .list(
                    userId=settings.gmail_user_email or "me",
                    q=query,
                    maxResults=max_results,
                )
                .execute()
            )
            return result.get("messages", [])
        except Exception as e:
            logger.error(f"Gmail list failed: {e}")
            return []

    def get_message(self, message_id: str) -> Optional[Dict]:
        if not self.service:
            return None
        try:
            return (
                self.service.users()
                .messages()
                .get(
                    userId=settings.gmail_user_email or "me",
                    id=message_id,
                    format="full",
                )
                .execute()
            )
        except Exception as e:
            logger.error(f"Gmail get failed: {e}")
            return None

    def modify_labels(
        self,
        message_id: str,
        add_labels: List[str] = None,
        remove_labels: List[str] = None,
    ) -> bool:
        if not self.service:
            return False
        try:
            body = {}
            if add_labels:
                body["addLabelIds"] = add_labels
            if remove_labels:
                body["removeLabelIds"] = remove_labels
            self.service.users().messages().modify(
                userId=settings.gmail_user_email or "me",
                id=message_id,
                body=body,
            ).execute()
            return True
        except Exception as e:
            logger.error(f"Gmail label modify failed: {e}")
            return False

    def create_draft(self, to: str, subject: str, body: str) -> Optional[str]:
        if not self.service:
            return None
        try:
            import base64
            from email.mime.text import MIMEText

            message = MIMEText(body)
            message["to"] = to
            message["subject"] = subject
            raw = base64.urlsafe_b64encode(message.as_bytes()).decode()
            draft = (
                self.service.users()
                .drafts()
                .create(
                    userId=settings.gmail_user_email or "me",
                    body={"message": {"raw": raw}},
                )
                .execute()
            )
            return draft.get("id")
        except Exception as e:
            logger.error(f"Gmail draft failed: {e}")
            return None
