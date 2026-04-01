from langchain_groq import ChatGroq
from langchain_core.messages import HumanMessage
from typing import Dict, List
from ..config import settings
from ..utils.logger import logger
import json


CONTENT_PROMPT = """Generate {variants} social media caption variants for this product on {platform}.

Product: {name}
Description: {description}
Target Audience: {audience}
Price: {price}

Requirements per variant:
- Instagram: 2-3 sentences + 5-8 hashtags (separate "hashtags" field)
- Twitter/X: Under 280 characters, punchy
- Facebook: 2-4 sentences, conversational

Return JSON array:
[{{"variant": "A", "caption": "...", "hashtags": "#tag1 #tag2"}}]
"""


class ContentGeneratorAgent:
    def __init__(self):
        self.llm = ChatGroq(
            model_name=settings.groq_model_quality,
            groq_api_key=settings.groq_api_key,
            temperature=0.6,
        )

    async def generate(
        self, product: Dict, platform: str, variants: int = 3
    ) -> List[Dict]:
        prompt = CONTENT_PROMPT.format(
            variants=variants,
            platform=platform,
            name=product.get("name", ""),
            description=product.get("description", ""),
            audience=product.get("target_audience", ""),
            price=product.get("price", ""),
        )
        try:
            response = await self.llm.ainvoke([HumanMessage(content=prompt)])
            return json.loads(response.content)
        except Exception as e:
            logger.error(f"Content generation failed: {e}")
            return []
