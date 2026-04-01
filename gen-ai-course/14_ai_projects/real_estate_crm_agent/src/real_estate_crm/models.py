from __future__ import annotations
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class LeadInput(BaseModel):
    source: str = "website_form"
    name: str
    email: str
    phone: str
    message: str = ""
    property_interest: str = ""
    budget_range: str = ""


class Qualification(BaseModel):
    score: int = Field(..., ge=0, le=100)
    category: str
    reasoning: str


class FollowUpSequence(BaseModel):
    status: str
    day_0_sms: str = ""
    day_0_email: str = ""
    next_touchpoint: str = ""


class LeadResponse(BaseModel):
    lead_id: str
    qualification: Qualification
    follow_up_sequence: FollowUpSequence
    notion_page_id: Optional[str] = None
    sales_team_notified: bool = False
