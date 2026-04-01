from __future__ import annotations
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class ScrapeRequest(BaseModel):
    trigger: str = "manual"
    min_rate_per_day: int = 600
    location: str = "SF Bay Area"
    max_results: int = 20


class JobApplication(BaseModel):
    title: str
    company: str
    rate: str = ""
    location: str = ""
    status: str = "pending"
    cover_letter_generated: bool = False
    notion_page_id: Optional[str] = None
    applied_at: Optional[str] = None


class ScrapeResponse(BaseModel):
    jobs_found: int = 0
    jobs_qualified: int = 0
    applications_submitted: int = 0
    applications: List[JobApplication] = []
    skipped_duplicates: int = 0
    errors: List[str] = []
