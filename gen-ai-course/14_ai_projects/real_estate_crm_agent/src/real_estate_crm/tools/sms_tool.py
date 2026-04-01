from ..config import settings
from ..utils.logger import logger


class SMSTool:
    def __init__(self):
        self.client = None
        self._init_client()

    def _init_client(self):
        try:
            if settings.twilio_account_sid and settings.twilio_auth_token:
                from twilio.rest import Client

                self.client = Client(
                    settings.twilio_account_sid, settings.twilio_auth_token
                )
        except Exception as e:
            logger.warning(f"Twilio not configured: {e}")

    def send_sms(self, to: str, body: str) -> bool:
        if not self.client:
            logger.warning("SMS not sent - Twilio not configured")
            return False
        try:
            message = self.client.messages.create(
                body=body,
                from_=settings.twilio_phone_number,
                to=to,
            )
            logger.info(f"SMS sent: {message.sid}")
            return True
        except Exception as e:
            logger.error(f"SMS failed: {e}")
            return False
