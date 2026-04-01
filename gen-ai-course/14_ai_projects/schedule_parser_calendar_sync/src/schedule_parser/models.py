from __future__ import annotations
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class ParsedEvent(BaseModel):
    title: str
    date: str
    start_time: str
    end_time: str
    location: str = ""
    calendar_event_id: Optional[str] = None
    reminder_set: Optional[str] = None


class ParseScheduleRequest(BaseModel):
    reminder_minutes: int = Field(
        default=30, description="Minutes before shift to set reminder"
    )
    calendar_id: str = Field(default="primary", description="Google Calendar ID")


class ParseScheduleResponse(BaseModel):
    status: str
    events_created: int = 0
    events: List[ParsedEvent] = []
    duplicates_skipped: int = 0
    ocr_confidence: float = 0.0
    processing_time_ms: int = 0
