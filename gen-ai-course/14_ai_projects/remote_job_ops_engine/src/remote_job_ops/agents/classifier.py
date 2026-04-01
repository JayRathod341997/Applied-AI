from langchain_groq import ChatGroq
from langchain_core.messages import HumanMessage
from typing import Dict, List
from ..config import settings
from ..utils.logger import logger
import json


CLASSIFY_PROMPT = """Classify these remote job listings into role types:
- CSR: Customer Service Representative
- Admin: Administrative Assistant
- VA: Virtual Assistant
- Ops: Operations Coordinator
- Other: Doesn't fit above categories

Jobs:
{jobs_json}

Return JSON array:
[{{"title": "...", "company": "...", "role_type": "<CSR|Admin|VA|Ops|Other>", "confidence": <0-1>}}]
"""


class ClassifierAgent:
    def __init__(self):
        self.llm = ChatGroq(
            model_name=settings.groq_model_fast,
            groq_api_key=settings.groq_api_key,
            temperature=0,
        )

    async def classify(self, jobs: List[Dict]) -> List[Dict]:
        if not jobs:
            return []
        prompt = CLASSIFY_PROMPT.format(jobs_json=json.dumps(jobs[:30], indent=2))
        try:
            response = await self.llm.ainvoke([HumanMessage(content=prompt)])
            return json.loads(response.content)
        except Exception as e:
            logger.error(f"Classification failed: {e}")
            return [
                {
                    "title": j.get("title", ""),
                    "company": j.get("company", ""),
                    "role_type": "Other",
                    "confidence": 0,
                }
                for j in jobs
            ]
