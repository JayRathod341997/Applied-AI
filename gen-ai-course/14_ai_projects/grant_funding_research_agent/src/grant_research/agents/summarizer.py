from langchain_groq import ChatGroq
from langchain_core.messages import HumanMessage
from typing import Dict
from ..config import settings
from ..utils.logger import logger
import json


SUMMARIZE_PROMPT = """Extract structured information from this grant listing:

{grant_text}

Return JSON:
{{
  "title": "...",
  "amount": "...",
  "deadline": "YYYY-MM-DD",
  "eligibility": "...",
  "application_url": "..."
}}
"""


class SummarizerAgent:
    def __init__(self):
        self.llm = ChatGroq(
            model_name=settings.groq_model_primary,
            groq_api_key=settings.groq_api_key,
            temperature=0.2,
        )

    async def summarize(self, grant_text: str) -> Dict:
        prompt = SUMMARIZE_PROMPT.format(grant_text=grant_text[:3000])
        try:
            response = await self.llm.ainvoke([HumanMessage(content=prompt)])
            return json.loads(response.content)
        except Exception as e:
            logger.error(f"Summarize failed: {e}")
            return {}
