from langchain_groq import ChatGroq
from langchain_core.messages import HumanMessage
from typing import Dict
from ..config import settings
from ..utils.logger import logger


RESUME_PROMPT = """Generate a tailored resume summary for this remote job application.

Job: {title} at {company}
Role Type: {role_type}

Candidate Profile:
{profile}

Write a 3-4 sentence professional summary that highlights relevant experience and skills for this specific role.

Summary:
"""


class ResumeGeneratorAgent:
    def __init__(self):
        self.llm = ChatGroq(
            model_name=settings.groq_model_primary,
            groq_api_key=settings.groq_api_key,
            temperature=0.3,
        )

    async def generate_summary(
        self, job: Dict, profile: str = "Experienced professional"
    ) -> str:
        prompt = RESUME_PROMPT.format(
            title=job.get("title", ""),
            company=job.get("company", ""),
            role_type=job.get("role_type", "Other"),
            profile=profile,
        )
        try:
            response = await self.llm.ainvoke([HumanMessage(content=prompt)])
            return response.content.strip()
        except Exception as e:
            logger.error(f"Resume generation failed: {e}")
            return ""
