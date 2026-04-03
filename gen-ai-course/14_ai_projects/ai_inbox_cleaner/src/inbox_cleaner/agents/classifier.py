from langchain_groq import ChatGroq
from langchain_core.messages import HumanMessage
from typing import Dict
from ..config import settings
from ..utils.logger import logger
from ..utils.exceptions import LLMClassificationError
import json
from ..models import EmailClassification


CLASSIFICATION_PROMPT = """Classify this email into one of these categories:
- security_job: Security/EP job postings, shift offers, job board alerts
- real_estate_lead: Real estate inquiries, property interest, buyer/seller leads
- client_communication: Business client messages, project updates
- job_application_response: Responses to job applications, interview invites
- newsletter: Newsletters, marketing, promotions
- spam: Irrelevant, phishing, junk

Also determine priority: high, medium, low

Email:
From: {from_address}
Subject: {subject}
Body: {body_snippet}

Return JSON:
{{
  "category": "<category>",
  "confidence": <0.0-1.0>,
  "priority": "<high|medium|low>",
  "reasoning": "<brief explanation>"
}}
"""


class ClassifierAgent:
    def __init__(self):
        self.llm = ChatGroq(
            model_name=settings.groq_model_fast,
            groq_api_key=settings.groq_api_key,
            temperature=0,
        )

    async def classify(self, from_address: str, subject: str, body: str) -> Dict:
        prompt = CLASSIFICATION_PROMPT.format(
            from_address=from_address,
            subject=subject,
            body_snippet=body[:1000],
        )
        try:
            structured_llm = self.llm.with_structured_output(EmailClassification)
            response = await structured_llm.ainvoke([HumanMessage(content=prompt)])
            return response.model_dump() if hasattr(response, 'model_dump') else response.dict()
        except Exception as e:
            logger.error(f"Classification failed: {e}")
            raise LLMClassificationError(f"Classification failed: {str(e)}")
