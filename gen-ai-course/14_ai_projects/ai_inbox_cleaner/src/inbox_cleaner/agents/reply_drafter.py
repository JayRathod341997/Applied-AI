from langchain_groq import ChatGroq
from langchain_core.messages import HumanMessage
from typing import Optional
from ..config import settings
from ..utils.logger import logger


DRAFT_PROMPT = """Draft a brief, professional reply to this email. Keep it under 150 words.

Original email:
From: {from_address}
Subject: {subject}
Body: {body}

Draft a reply that is:
- Professional and concise
- Addresses the key points
- Leaves room for follow-up

Reply draft:
"""


class ReplyDrafterAgent:
    def __init__(self):
        self.llm = ChatGroq(
            model_name=settings.groq_model_primary,
            groq_api_key=settings.groq_api_key,
            temperature=0.4,
        )

    async def draft_reply(
        self, from_address: str, subject: str, body: str
    ) -> Optional[str]:
        prompt = DRAFT_PROMPT.format(
            from_address=from_address,
            subject=subject,
            body=body[:2000],
        )
        try:
            response = await self.llm.ainvoke([HumanMessage(content=prompt)])
            return response.content.strip()
        except Exception as e:
            logger.error(f"Draft failed: {e}")
            return None
