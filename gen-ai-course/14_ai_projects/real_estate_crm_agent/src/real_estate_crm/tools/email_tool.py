from ..config import settings
from ..utils.logger import logger


class EmailTool:
    def __init__(self):
        self.client = None
        self._init_client()

    def _init_client(self):
        try:
            if settings.sendgrid_api_key:
                import sendgrid

                self.client = sendgrid.SendGridAPIClient(
                    api_key=settings.sendgrid_api_key
                )
        except Exception as e:
            logger.warning(f"SendGrid not configured: {e}")

    def send_email(
        self,
        to: str,
        subject: str,
        html_content: str,
        from_email: str = "noreply@example.com",
    ) -> bool:
        if not self.client:
            logger.warning("Email not sent - SendGrid not configured")
            return False
        try:
            from sendgrid.helpers.mail import Mail

            message = Mail(
                from_email=from_email,
                to_emails=to,
                subject=subject,
                html_content=html_content,
            )
            response = self.client.send(message)
            logger.info(f"Email sent: {response.status_code}")
            return response.status_code in (200, 201, 202)
        except Exception as e:
            logger.error(f"Email failed: {e}")
            return False
