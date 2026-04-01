import httpx
from ..config import settings
from ..utils.logger import logger


class SlackTool:
    async def send_message(self, message: str, channel: str = None) -> bool:
        if not settings.slack_webhook_url:
            return False
        try:
            async with httpx.AsyncClient() as client:
                resp = await client.post(
                    settings.slack_webhook_url, json={"text": message}
                )
                return resp.status_code == 200
        except Exception as e:
            logger.error(f"Slack send failed: {e}")
            return False

    async def send_dm(self, user_id: str, message: str) -> bool:
        if not settings.slack_bot_token:
            return False
        try:
            async with httpx.AsyncClient() as client:
                resp = await client.post(
                    "https://slack.com/api/chat.postMessage",
                    headers={"Authorization": f"Bearer {settings.slack_bot_token}"},
                    json={"channel": user_id, "text": message},
                )
                return resp.json().get("ok", False)
        except Exception as e:
            logger.error(f"Slack DM failed: {e}")
            return False
