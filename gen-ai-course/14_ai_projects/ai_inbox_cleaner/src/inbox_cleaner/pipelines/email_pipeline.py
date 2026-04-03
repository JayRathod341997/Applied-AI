from typing import Dict, List
from ..agents.classifier import ClassifierAgent
from ..agents.reply_drafter import ReplyDrafterAgent
from ..tools.gmail_tool import GmailTool
from ..utils.logger import logger
import httpx
from ..config import settings
import traceback
from ..utils.exceptions import SlackIntegrationError


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

        try:
            classification = await self.classifier.classify(from_address, subject, body)
        except Exception as e:
            await self.notify_slack_error(e, f"Classifying email {email_id}")
            classification = {"category": "newsletter", "priority": "low", "confidence": 0.0, "reasoning": "Classification failed explicitly"}

        actions = []
        category = classification.get("category", "newsletter")
        label = CATEGORY_LABEL_MAP.get(category, "Unsorted")

        if category != "spam":
            try:
                label_id = self.gmail.get_or_create_label(label)
                if label_id:
                    self.gmail.modify_labels(email_id, add_labels=[label_id])
                    actions.append({"action": "label", "label": label, "status": "executed"})
                else:
                    actions.append({"action": "label", "label": label, "status": "failed"})
            except Exception as e:
                actions.append({"action": "label", "label": label, "status": "failed", "error": str(e)})
                await self.notify_slack_error(e, f"Applying label '{label}' to email {email_id}")

            if classification.get("priority") == "high":
                try:
                    self.gmail.modify_labels(email_id, add_labels=["STARRED"])
                    actions.append({"action": "star", "status": "executed"})
                except Exception as e:
                    actions.append({"action": "star", "status": "failed", "error": str(e)})
                    await self.notify_slack_error(e, f"Starring email {email_id}")

        if category == "job_application_response":
            success = await self.notify_slack(
                email_id=email_id,
                subject=subject,
                from_address=from_address,
                classification=classification,
                channel="#job-alerts"
            )
            actions.append(
                {"action": "slack_notify", "channel": "#job-alerts", "status": "executed" if success else "failed"}
            )

        if category == "newsletter":
            success = await self.notify_slack(
                email_id=email_id,
                subject=subject,
                from_address=from_address,
                classification=classification,
                channel="#newsletter-alerts"
            )
            actions.append(
                {"action": "slack_notify", "channel": "#newsletter-alerts", "status": "executed" if success else "failed"}
            )

        if category == "real_estate_lead":
            actions.append({"action": "notion_forward", "status": "pending"})

        if classification.get("priority") == "high":
            try:
                draft = await self.drafter.draft_reply(from_address, subject, body)
                if draft:
                    draft_id = self.gmail.create_draft(to=from_address, subject=f"Re: {subject}", body=draft)
                    actions.append({"action": "draft_reply", "preview": draft[:100], "status": "executed" if draft_id else "failed"})
            except Exception as e:
                actions.append({"action": "draft_reply", "status": "failed", "error": str(e)})
                await self.notify_slack_error(e, f"Drafting reply to email {email_id}")

        # Mark as read by removing UNREAD label
        try:
            self.gmail.modify_labels(email_id, remove_labels=["UNREAD"])
            actions.append({"action": "mark_read", "status": "executed"})
        except Exception as e:
            actions.append({"action": "mark_read", "status": "failed", "error": str(e)})
            await self.notify_slack_error(e, f"Marking email {email_id} as read")

        return {
            "email_id": email_id,
            "subject": subject,
            # "body": body,
            "from": from_address,
            "classification": classification,
            "actions_taken": actions,
        }

    async def sync_new_emails(self) -> List[Dict]:
        messages = self.gmail.list_messages(query="is:unread category:primary newer_than:31d", max_results=2)
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

    async def notify_slack(self, email_id: str, subject: str, from_address: str, classification: Dict, channel: str = None) -> bool:
        if not settings.slack_bot_token:
            return False
        try:
            category_title = classification.get('category', 'email').replace('_', ' ').title()
            blocks = [
                {
                    "type": "header",
                    "text": {
                        "type": "plain_text",
                        "text": f"New {category_title}",
                        "emoji": True
                    }
                },
                {
                    "type": "section",
                    "fields": [
                        {"type": "mrkdwn", "text": f"*From:*\n{from_address}"},
                        {"type": "mrkdwn", "text": f"*Email ID:*\n{email_id}"}
                    ]
                },
                {
                    "type": "section",
                    "text": {"type": "mrkdwn", "text": f"*Subject:*\n{subject}"}
                },
                {
                    "type": "section",
                    "fields": [
                        {"type": "mrkdwn", "text": f"*Category:*\n{classification.get('category', 'N/A')}"},
                        {"type": "mrkdwn", "text": f"*Priority:*\n{classification.get('priority', 'N/A')}"},
                        {"type": "mrkdwn", "text": f"*Confidence:*\n{classification.get('confidence', 'N/A')}"}
                    ]
                },
                {
                    "type": "section",
                    "text": {"type": "mrkdwn", "text": f"*Reasoning:*\n{classification.get('reasoning', 'No reasoning provided.')}"}
                }
            ]

            payload = {
                "text": f"New {category_title}: {subject}",
                "blocks": blocks
            }
            if channel:
                payload["channel"] = channel
            headers = {
                "Authorization": f"Bearer {settings.slack_bot_token}",
                "Content-Type": "application/json"
            }
            async with httpx.AsyncClient() as client:
                resp = await client.post(
                    "https://slack.com/api/chat.postMessage", json=payload, headers=headers
                )
                if resp.status_code != 200 or not resp.json().get("ok", False):
                    error_msg = resp.json().get("error", "Unknown error")
                    raise SlackIntegrationError(f"HTTP {resp.status_code}: {error_msg}")
                return True
        except SlackIntegrationError as e:
            logger.error(f"Slack notification failed: {e}")
            await self.notify_slack_error(e, f"Slack notification to {channel}")
            return False
        except Exception as e:
            logger.error(f"Slack notification failed: {e}")
            return False

    async def notify_slack_error(self, exc: Exception, context: str) -> bool:
        if not settings.slack_bot_token:
            return False
        try:
            exc_type = type(exc).__name__
            tb_str = "".join(traceback.format_exception(type(exc), exc, exc.__traceback__))
            # Slack text limits: 3000 chars for text blocks
            if len(tb_str) > 2000:
                tb_str = tb_str[-2000:]
                
            blocks = [
                {
                    "type": "header",
                    "text": {
                        "type": "plain_text",
                        "text": f"🚨 Application Error: {exc_type}",
                        "emoji": True
                    }
                },
                {
                    "type": "section",
                    "fields": [
                        {"type": "mrkdwn", "text": f"*Context:*\n{context}"},
                        {"type": "mrkdwn", "text": f"*Type:*\n{exc_type}"}
                    ]
                },
                {
                    "type": "section",
                    "text": {"type": "mrkdwn", "text": f"*Description:*\n`{str(exc)}`"}
                },
                {
                    "type": "section",
                    "text": {"type": "mrkdwn", "text": f"*Traceback:*\n```\n{tb_str}\n```"}
                }
            ]
            payload = {
                "text": f"Error: {exc_type} - {context}",
                "blocks": blocks,
                "channel": "#exceptions"
            }
            headers = {
                "Authorization": f"Bearer {settings.slack_bot_token}",
                "Content-Type": "application/json"
            }
            async with httpx.AsyncClient() as client:
                await client.post(
                    "https://slack.com/api/chat.postMessage", json=payload, headers=headers
                )
        except Exception as e:
            logger.error(f"Failed to post error to Slack: {e}")
            return False
