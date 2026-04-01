from langchain_groq import ChatGroq
from langchain_core.messages import HumanMessage
from typing import Dict, List
from ..config import settings
from ..utils.logger import logger
import json


PARSE_PROMPT = """Extract shift/schedule information from this OCR text.
Return a JSON array of events. Each event must have:
- title: string (e.g. "Security Shift - Main Gate")
- date: string (YYYY-MM-DD)
- start_time: string (HH:MM 24h format)
- end_time: string (HH:MM 24h format)
- location: string

OCR Text:
{ocr_text}

Return ONLY a JSON array, no other text:
"""


class ParserAgent:
    def __init__(self):
        self.llm = ChatGroq(
            model_name=settings.groq_model_primary,
            groq_api_key=settings.groq_api_key,
            temperature=0.1,
        )

    async def parse_schedule(self, ocr_text: str) -> List[Dict]:
        prompt = PARSE_PROMPT.format(ocr_text=ocr_text[:3000])
        try:
            response = await self.llm.ainvoke([HumanMessage(content=prompt)])
            return json.loads(response.content)
        except Exception as e:
            logger.error(f"Parse failed: {e}")
            return []
