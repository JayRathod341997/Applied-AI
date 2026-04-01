from __future__ import annotations
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class ResearchCriteria(BaseModel):
    veteran_owned: bool = False
    business_type: str = "small_business"
    industry: List[str] = []
    min_amount: int = 0


class ResearchRequest(BaseModel):
    action: str = "run_research"
    criteria: ResearchCriteria


class Grant(BaseModel):
    title: str
    source: str = ""
    amount: str = ""
    deadline: str = ""
    eligibility: str = ""
    application_url: str = ""
    relevance_score: int = 0
    notion_page_id: Optional[str] = None
    slack_notified: bool = False


class ResearchResponse(BaseModel):
    grants_found: int = 0
    grants_relevant: int = 0
    grants_new: int = 0
    grants: List[Grant] = []
    duplicates_skipped: int = 0
