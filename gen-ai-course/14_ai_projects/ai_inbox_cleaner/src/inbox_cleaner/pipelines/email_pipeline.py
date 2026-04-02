from typing import Dict, List
from ..agents.classifier import ClassifierAgent
from ..agents.reply_drafter import ReplyDrafterAgent
from ..tools.gmail_tool import GmailTool
from ..utils.logger import logger
import httpx
from ..config import settings


CATEGORY_LABEL_MAP = {
    "security_job": "Jobs/Security",
    "real_estate_lead": "Leads/RE",
    "client_communication": "Clients",
    "job_application_response": "Applications",
    "newsletter": "Newsletter",
    "spam": "Spam",
}


class EmailPipeline:
    def __init__(self):
        self.classifier = ClassifierAgent()
        self.drafter = ReplyDrafterAgent()
        self.gmail = GmailTool()

    async def process_email(self, email_data: Dict) -> Dict:
        from_address = email_data.get("from", "")
        subject = email_data.get("subject", "")
        body = email_data.get("body", "")
        email_id = email_data.get("id", "unknown")

        classification = await self.classifier.classify(from_address, subject, body)
        actions = []

        category = classification.get("category", "newsletter")
        label = CATEGORY_LABEL_MAP.get(category, "Unsorted")

        if category != "spam":
            actions.append({"action": "label", "label": label})
            if classification.get("priority") == "high":
                actions.append({"action": "star"})

        if category == "job_application_response":
            actions.append(
                {"action": "slack_notify", "channel": "#job-alerts", "sent": True}
            )

        if category == "real_estate_lead":
            actions.append({"action": "notion_forward"})

        if classification.get("priority") == "high":
            draft = await self.drafter.draft_reply(from_address, subject, body)
            if draft:
                actions.append({"action": "draft_reply", "preview": draft[:100]})

        return {
            "email_id": email_id,
            "subject": subject,
            # "body": body,
            "from": from_address,
            "classification": classification,
            "actions_taken": actions,
        }

    async def sync_new_emails(self) -> List[Dict]:
        messages = self.gmail.list_messages(query="is:unread category:primary newer_than:7d", max_results=2)
        results = []
        for msg in messages:
            full_msg = self.gmail.get_message(msg["id"])
            if full_msg:
                email_data = self._parse_message(full_msg)
                email_data["id"] = msg["id"]
                result = await self.process_email(email_data)
                results.append(result)
        return results

    def _parse_message(self, message: Dict) -> Dict:
        headers = {
            h["name"].lower(): h["value"]
            for h in message.get("payload", {}).get("headers", [])
        }
        body = ""
        parts = message.get("payload", {}).get("parts", [])
        for part in parts:
            if part.get("mimeType") == "text/plain":
                import base64

                data = part.get("body", {}).get("data", "")
                if data:
                    body = base64.urlsafe_b64decode(data).decode(
                        "utf-8", errors="replace"
                    )
                    break
        return {
            "from": headers.get("from", ""),
            "subject": headers.get("subject", ""),
            "body": body,
        }

    async def notify_slack(self, message: str) -> bool:
        if not settings.slack_webhook_url:
            return False
        try:
            async with httpx.AsyncClient() as client:
                resp = await client.post(
                    settings.slack_webhook_url, json={"text": message}
                )
                return resp.status_code == 200
        except Exception as e:
            logger.error(f"Slack notification failed: {e}")
            return False
