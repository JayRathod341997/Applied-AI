from typing import Any, Optional

from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError
from ..config import settings
from ..utils.logger import logger


class SlackTool:
    def __init__(self):
        self.client = (
            WebClient(token=settings.slack_bot_token)
            if settings.slack_bot_token
            else None
        )

    @staticmethod
    def _to_plain_dict(response: Any) -> dict:
        """Normalize Slack SDK responses to plain dicts."""
        if isinstance(response, dict):
            return response

        data = getattr(response, "data", None)
        if isinstance(data, dict):
            return data

        return dict(response)

    def post_message(
        self, channel: str, text: str, thread_ts: Optional[str] = None
    ) -> Optional[dict]:
        if not self.client:
            logger.warning("Slack client not configured")
            return None
        try:
            kwargs = {"channel": channel, "text": text}
            if thread_ts:
                kwargs["thread_ts"] = thread_ts
            response = self.client.chat_postMessage(**kwargs)
            return self._to_plain_dict(response)
        except Exception as e:
            logger.error(f"Slack message failed: {e}")
            return None

    def add_reaction(self, channel: str, name: str, timestamp: str) -> bool:
        if not self.client:
            return False
        try:
            self.client.reactions_add(
                channel=channel,
                name=name,
                timestamp=timestamp,
            )
            return True
        except SlackApiError as e:
            # Treat "already_reacted" as success because the desired state exists.
            if e.response and e.response.get("error") == "already_reacted":
                logger.info(
                    "Slack reaction '%s' already exists on %s in %s",
                    name,
                    timestamp,
                    channel,
                )
                return True
            logger.error(f"Slack reaction failed: {e}")
            return False
        except Exception as e:
            logger.error(f"Slack reaction failed: {e}")
            return False

    def get_channel_info(self, channel_id: str) -> Optional[dict]:
        if not self.client:
            return None
        try:
            response = self.client.conversations_info(channel=channel_id)
            return self._to_plain_dict(response)
        except Exception as e:
            logger.error(f"Slack channel info failed: {e}")
            return None

    def list_channels(self) -> list:
        if not self.client:
            return []
        try:
            channels = []
            cursor = None

            while True:
                kwargs = {
                    "types": "public_channel,private_channel",
                    "limit": 200,
                }
                if cursor:
                    kwargs["cursor"] = cursor

                response = self.client.conversations_list(**kwargs)
                response_data = self._to_plain_dict(response)
                channels.extend(response_data.get("channels", []))

                cursor = (
                    response_data.get("response_metadata", {}).get("next_cursor")
                    or None
                )
                if not cursor:
                    break

            return channels
        except Exception as e:
            logger.error(f"Slack list channels failed: {e}")
            return []
