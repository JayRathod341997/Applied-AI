from __future__ import annotations
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class PipelineRequest(BaseModel):
    action: str = "run_pipeline"
    role_types: List[str] = ["CSR", "Admin", "VA"]
    max_applications: int = 10
    generate_resume: bool = True


class Application(BaseModel):
    title: str
    company: str
    source: str = ""
    match_score: int = 0
    resume_generated: bool = False
    resume_path: str = ""
    cover_letter_path: str = ""
    status: str = "pending"
    notion_page_id: Optional[str] = None


class PipelineResponse(BaseModel):
    listings_scraped: int = 0
    roles_classified: Dict[str, int] = {}
    applications_submitted: int = 0
    applications: List[Application] = []
    weekly_report_generated: str = ""
