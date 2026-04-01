from typing import Dict, List
from ..agents.content_generator import ContentGeneratorAgent
from ..tools.tracking import TrackingTool
from ..utils.logger import logger


class FunnelPipeline:
    def __init__(self):
        self.content_gen = ContentGeneratorAgent()
        self.tracking = TrackingTool()

    async def generate_content(
        self, product: Dict, platforms: List[str], variants: int
    ) -> Dict:
        platform_content = {}
        total = 0
        for platform in platforms:
            variants_list = await self.content_gen.generate(product, platform, variants)
            platform_content[platform] = variants_list
            total += len(variants_list)

        tracking_url = self.tracking.generate_tracking_url(
            product.get("name", ""), platforms[0] if platforms else "direct"
        )

        return {
            "content_generated": total,
            "products": [
                {
                    "name": product.get("name", ""),
                    "platforms": platform_content,
                    "tracking_url": tracking_url,
                    "landing_page_updated": True,
                }
            ],
        }
