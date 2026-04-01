from __future__ import annotations
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class EmailClassification(BaseModel):
    category: str
    confidence: float
    priority: str
    reasoning: str


class EmailAction(BaseModel):
    action: str
    label: Optional[str] = None
    sent: Optional[bool] = None
    preview: Optional[str] = None


class ClassifyRequest(BaseModel):
    email_id: Optional[str] = None
    from_address: str = ""
    subject: str = ""
    body: str = ""


class ClassifyResponse(BaseModel):
    email_id: str
    classification: EmailClassification
    actions_taken: List[EmailAction] = []


class SyncResponse(BaseModel):
    emails_processed: int
    classifications: List[ClassifyResponse]
    errors: List[str] = []
