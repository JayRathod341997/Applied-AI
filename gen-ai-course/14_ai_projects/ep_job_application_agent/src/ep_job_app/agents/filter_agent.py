from langchain_groq import ChatGroq
from langchain_core.messages import HumanMessage
from typing import Dict, List
from ..config import settings
from ..utils.logger import logger
import json


FILTER_PROMPT = """Filter these Executive Protection job listings. Keep only jobs that match:
- Rate >= ${min_rate}/day
- Location: {location}
- Relevant to Executive Protection / Security

Jobs:
{jobs_json}

Return JSON array of qualified jobs:
[{{"title": "...", "company": "...", "rate": "...", "location": "...", "match_score": <0-100>}}]
"""


class FilterAgent:
    def __init__(self):
        self.llm = ChatGroq(
            model_name=settings.groq_model_fast,
            groq_api_key=settings.groq_api_key,
            temperature=0,
        )

    async def filter_jobs(
        self, jobs: List[Dict], min_rate: int, location: str
    ) -> List[Dict]:
        if not jobs:
            return []
        prompt = FILTER_PROMPT.format(
            min_rate=min_rate,
            location=location,
            jobs_json=json.dumps(jobs[:30], indent=2),
        )
        try:
            response = await self.llm.ainvoke([HumanMessage(content=prompt)])
            return json.loads(response.content)
        except Exception as e:
            logger.error(f"Filter failed: {e}")
            return jobs
