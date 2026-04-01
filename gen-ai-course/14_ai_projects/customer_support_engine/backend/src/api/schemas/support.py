"""Request and response schemas for the support endpoints."""

from __future__ import annotations

from typing import Optional

from pydantic import BaseModel


class StartRequest(BaseModel):
    message: str
    conversation_id: Optional[str] = None


class StartResponse(BaseModel):
    conversation_id: str
    reply: str
    issue_type: Optional[str] = None
    severity: Optional[str] = None
    status: Optional[str] = None


class HistoryItem(BaseModel):
    id: str
    role: str
    content: str
    timestamp: Optional[str] = None
    issue_type: Optional[str] = None
    severity: Optional[str] = None
    status: Optional[str] = None
