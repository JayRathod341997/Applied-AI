from langchain_groq import ChatGroq
from langchain_core.messages import HumanMessage
from typing import Dict
from ..config import settings
from ..utils.logger import logger
import json


QUALIFY_PROMPT = """Qualify this real estate lead. Score 0-100 and categorize as hot/warm/cold.

Lead Info:
Name: {name}
Email: {email}
Phone: {phone}
Message: {message}
Property Interest: {property_interest}
Budget Range: {budget_range}

Consider: budget clarity, timeline urgency, pre-approval status, specific criteria.

Return JSON:
{{
  "score": <0-100>,
  "category": "<hot|warm|cold>",
  "reasoning": "<brief explanation>"
}}
"""


class QualifierAgent:
    def __init__(self):
        self.llm = ChatGroq(
            model_name=settings.groq_model_primary,
            groq_api_key=settings.groq_api_key,
            temperature=0.2,
        )

    async def qualify(self, lead: Dict) -> Dict:
        prompt = QUALIFY_PROMPT.format(
            name=lead.get("name", ""),
            email=lead.get("email", ""),
            phone=lead.get("phone", ""),
            message=lead.get("message", ""),
            property_interest=lead.get("property_interest", ""),
            budget_range=lead.get("budget_range", ""),
        )
        try:
            response = await self.llm.ainvoke([HumanMessage(content=prompt)])
            return json.loads(response.content)
        except Exception as e:
            logger.error(f"Qualification failed: {e}")
            return {"score": 50, "category": "warm", "reasoning": f"Error: {e}"}
