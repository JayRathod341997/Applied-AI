from __future__ import annotations
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field
from datetime import datetime


class SyncRequest(BaseModel):
    action: str = Field(..., description="full_sync, incremental_sync, or source_sync")
    sources: Optional[List[str]] = Field(
        default=None,
        description="Sources to sync: google_calendar, google_drive, gmail",
    )
    direction: str = Field(
        default="bidirectional",
        description="notion_to_source, source_to_notion, or bidirectional",
    )


class SourceSyncResult(BaseModel):
    status: str
    records_synced: int = 0
    conflicts_resolved: int = 0
    errors: List[str] = []
    last_sync: str


class SyncResponse(BaseModel):
    sync_results: Dict[str, SourceSyncResult]
    health: Dict[str, Any]


class ConflictResolution(BaseModel):
    source: str
    record_id: str
    resolution: str
    reasoning: str
    merged_data: Dict[str, Any]


class HealthStatus(BaseModel):
    all_systems_healthy: bool
    uptime_hours: float
    error_rate: float
    next_sync: Optional[str] = None
    integrations: Dict[str, Dict[str, Any]] = {}
