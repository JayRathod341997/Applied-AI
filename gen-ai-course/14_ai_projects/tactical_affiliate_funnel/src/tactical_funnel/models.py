from __future__ import annotations
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class Product(BaseModel):
    name: str
    description: str = ""
    affiliate_link: str
    target_audience: str = ""
    price: str = ""


class ContentVariant(BaseModel):
    variant: str
    caption: str
    hashtags: str = ""


class PlatformContent(BaseModel):
    instagram: List[ContentVariant] = []
    twitter: List[ContentVariant] = []
    facebook: List[ContentVariant] = []


class GenerateRequest(BaseModel):
    action: str = "generate_content"
    product: Product
    platforms: List[str] = ["instagram", "twitter", "facebook"]
    variants_per_platform: int = 3


class ProductResult(BaseModel):
    name: str
    platforms: Dict[str, List[ContentVariant]] = {}
    tracking_url: str = ""
    landing_page_updated: bool = False


class GenerateResponse(BaseModel):
    content_generated: int = 0
    products: List[ProductResult] = []
