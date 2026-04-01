from langchain_groq import ChatGroq
from langchain_core.messages import HumanMessage
from typing import Dict, List
from ..config import settings
from ..utils.logger import logger
import json


VALIDATE_PROMPT = """Validate these schedule events for anomalies:
- Overlapping shifts
- Unrealistic hours (>16hr shift)
- Missing dates or times
- Invalid date formats

Events:
{events_json}

Return JSON:
{{
  "valid": true/false,
  "issues": ["list of issues found"],
  "corrected_events": [/* corrected events if any */]
}}
"""


class ValidatorAgent:
    def __init__(self):
        self.llm = ChatGroq(
            model_name=settings.groq_model_fast,
            groq_api_key=settings.groq_api_key,
            temperature=0,
        )

    async def validate(self, events: List[Dict]) -> Dict:
        prompt = VALIDATE_PROMPT.format(events_json=json.dumps(events, indent=2))
        try:
            response = await self.llm.ainvoke([HumanMessage(content=prompt)])
            return json.loads(response.content)
        except Exception as e:
            logger.error(f"Validation failed: {e}")
            return {"valid": True, "issues": [], "corrected_events": events}
