from langchain_groq import ChatGroq
from langchain_core.messages import HumanMessage
from typing import Any, Dict
from ..config import settings
from ..utils.logger import logger
import json


CONFLICT_RESOLUTION_PROMPT = """You are a data conflict resolver. Two systems have modified the same record differently.

Source A (Notion):
{notion_data}

Source B ({source_name}):
{source_data}

Resolve the conflict by merging the best of both. Return JSON:
{{
  "resolution": "use_a|use_b|merge",
  "reasoning": "why this resolution",
  "merged_data": {{...merged record...}}
}}
"""


class ConflictResolverAgent:
    def __init__(self):
        self.llm = ChatGroq(
            model_name=settings.groq_model_primary,
            groq_api_key=settings.groq_api_key,
            temperature=0.1,
        )

    async def resolve(
        self, notion_data: Dict, source_data: Dict, source_name: str
    ) -> Dict:
        prompt = CONFLICT_RESOLUTION_PROMPT.format(
            notion_data=json.dumps(notion_data, indent=2),
            source_name=source_name,
            source_data=json.dumps(source_data, indent=2),
        )
        try:
            response = await self.llm.ainvoke([HumanMessage(content=prompt)])
            return json.loads(response.content)
        except Exception as e:
            logger.error(f"Conflict resolution failed: {e}")
            return {
                "resolution": "use_a",
                "reasoning": f"Error in resolution, defaulting to Notion: {e}",
                "merged_data": notion_data,
            }
