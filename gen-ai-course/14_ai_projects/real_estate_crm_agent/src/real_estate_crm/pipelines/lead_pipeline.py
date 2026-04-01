from typing import Dict, Optional
from datetime import datetime
from ..agents.qualifier import QualifierAgent
from ..tools.sms_tool import SMSTool
from ..tools.email_tool import EmailTool
from ..utils.logger import logger
from ..config import settings
import uuid


WELCOME_SMS = "Hi {name}, thanks for your interest in finding a property! We'll be in touch shortly with options matching your criteria."

WELCOME_EMAIL = """
<html><body>
<h2>Thank you for your interest, {name}!</h2>
<p>We received your inquiry and our team is reviewing your requirements.</p>
<p>We'll be in touch within 24 hours with properties matching your criteria.</p>
<p>Best regards,<br>JMG Real Estate Team</p>
</body></html>
"""


class LeadPipeline:
    def __init__(self):
        self.qualifier = QualifierAgent()
        self.sms = SMSTool()
        self.email = EmailTool()

    async def process_lead(self, lead_data: Dict) -> Dict:
        lead_id = f"lead_{datetime.utcnow().strftime('%Y%m%d')}_{uuid.uuid4().hex[:6]}"
        qualification = await self.qualifier.qualify(lead_data)
        sms_sent = self.sms.send_sms(
            to=lead_data.get("phone", ""),
            body=WELCOME_SMS.format(name=lead_data.get("name", "")),
        )
        email_sent = self.email.send_email(
            to=lead_data.get("email", ""),
            subject="Thank you for your inquiry - JMG Real Estate",
            html_content=WELCOME_EMAIL.format(name=lead_data.get("name", "")),
        )
        return {
            "lead_id": lead_id,
            "qualification": qualification,
            "follow_up_sequence": {
                "status": "initiated",
                "day_0_sms": "sent" if sms_sent else "failed",
                "day_0_email": "sent" if email_sent else "failed",
                "next_touchpoint": "Day 1: Property match email",
            },
            "notion_page_id": None,
            "sales_team_notified": qualification.get("category") == "hot",
        }
