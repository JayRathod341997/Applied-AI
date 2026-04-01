from langchain_groq import ChatGroq
from langchain_core.messages import HumanMessage
from typing import Dict
from ..config import settings
from ..utils.logger import logger


COVER_LETTER_PROMPT = """Write a professional cover letter for this Executive Protection position.

Job: {title} at {company}
Rate: {rate}
Location: {location}

Write a 150-200 word cover letter emphasizing:
- EP experience and certifications
- Discretion and professionalism
- Physical fitness and threat assessment skills

Cover letter:
"""


class CoverLetterAgent:
    def __init__(self):
        self.llm = ChatGroq(
            model_name=settings.groq_model_primary,
            groq_api_key=settings.groq_api_key,
            temperature=0.4,
        )

    async def generate(self, job: Dict) -> str:
        prompt = COVER_LETTER_PROMPT.format(
            title=job.get("title", ""),
            company=job.get("company", ""),
            rate=job.get("rate", ""),
            location=job.get("location", ""),
        )
        try:
            response = await self.llm.ainvoke([HumanMessage(content=prompt)])
            return response.content.strip()
        except Exception as e:
            logger.error(f"Cover letter generation failed: {e}")
            return ""
