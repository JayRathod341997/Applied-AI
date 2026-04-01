from ..config import settings
from ..utils.logger import logger
from urllib.parse import urlencode


class TrackingTool:
    def generate_tracking_url(
        self, product_name: str, platform: str, campaign: str = "spring2026"
    ) -> str:
        slug = product_name.lower().replace(" ", "-")
        params = urlencode(
            {
                "utm_source": platform,
                "utm_campaign": campaign,
                "utm_medium": "affiliate",
            }
        )
        return f"{settings.tracking_domain}/go/{slug}?{params}"
