from langchain_groq import ChatGroq
from langchain_core.messages import HumanMessage
from typing import Dict, List
from ..config import settings
from ..utils.logger import logger
import json


FILTER_PROMPT = """Score these grants for relevance based on criteria:
- Veteran-owned: {veteran_owned}
- Business type: {business_type}
- Industries: {industries}
- Min amount: ${min_amount}

Grants:
{grants_json}

Return JSON array:
[{{"title": "...", "relevance_score": <0-100>, "reasoning": "..."}}]
"""


class FilterAgent:
    def __init__(self):
        self.llm = ChatGroq(
            model_name=settings.groq_model_fast,
            groq_api_key=settings.groq_api_key,
            temperature=0,
        )

    async def filter_grants(self, grants: List[Dict], criteria: Dict) -> List[Dict]:
        if not grants:
            return []
        prompt = FILTER_PROMPT.format(
            veteran_owned=criteria.get("veteran_owned", False),
            business_type=criteria.get("business_type", "small_business"),
            industries=criteria.get("industry", []),
            min_amount=criteria.get("min_amount", 0),
            grants_json=json.dumps(grants[:20], indent=2),
        )
        try:
            response = await self.llm.ainvoke([HumanMessage(content=prompt)])
            return json.loads(response.content)
        except Exception as e:
            logger.error(f"Filter failed: {e}")
            return grants
