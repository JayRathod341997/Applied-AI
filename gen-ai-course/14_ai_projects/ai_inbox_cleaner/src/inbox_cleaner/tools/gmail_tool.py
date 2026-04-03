from typing import Any, Dict, List, Optional
from ..config import settings
from ..utils.logger import logger
from ..utils.exceptions import GmailIntegrationError


class GmailTool:
    def __init__(self):
        self.service = None
        self._init_service()

    def _init_service(self):
        # Initialize Gmail API client using OAuth 2.0 flow.
        try:
            import os
            from google.auth.transport.requests import Request
            from google.oauth2.credentials import Credentials
            from google_auth_oauthlib.flow import InstalledAppFlow
            from googleapiclient.discovery import build

            SCOPES = ["https://www.googleapis.com/auth/gmail.modify"]
            creds = None
            
            # The file token.json stores the user's access and refresh tokens, and is
            # created automatically when the authorization flow completes for the first time.
            if os.path.exists("token.json"):
                creds = Credentials.from_authorized_user_file("token.json", SCOPES)
            
            # If there are no (valid) credentials available, let the user log in.
            if not creds or not creds.valid:
                if creds and creds.expired and creds.refresh_token:
                    creds.refresh(Request())
                else:
                    if os.path.exists(settings.google_client_secrets_json):
                        flow = InstalledAppFlow.from_client_secrets_file(
                            settings.google_client_secrets_json, SCOPES
                        )
                        creds = flow.run_local_server(port=0)
                    else:
                        logger.warning("No client secrets file found at %s. Please download it from Google Cloud Console.", settings.google_client_secrets_json)
                        return
                        
                # Save the credentials for the next run
                with open("token.json", "w") as token:
                    token.write(creds.to_json())

            self.service = build("gmail", "v1", credentials=creds)
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
            raise GmailIntegrationError(f"Gmail list failed: {str(e)}")

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
            raise GmailIntegrationError(f"Gmail get failed: {str(e)}")

    def get_or_create_label(self, label_name: str) -> Optional[str]:
        if not self.service:
            return None
        try:
            results = self.service.users().labels().list(userId=settings.gmail_user_email or "me").execute()
            labels = results.get("labels", [])
            for label in labels:
                if label["name"].lower() == label_name.lower():
                    return label["id"]
            
            # Create if not exists
            new_label = {
                "name": label_name,
                "labelListVisibility": "labelShow",
                "messageListVisibility": "show"
            }
            created_label = self.service.users().labels().create(
                userId=settings.gmail_user_email or "me", 
                body=new_label
            ).execute()
            return created_label["id"]
        except Exception as e:
            logger.error(f"Gmail label get/create failed: {e}")
            raise GmailIntegrationError(f"Gmail label get/create failed: {str(e)}")

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
            raise GmailIntegrationError(f"Gmail label modify failed: {str(e)}")

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
            raise GmailIntegrationError(f"Gmail draft failed: {str(e)}")
