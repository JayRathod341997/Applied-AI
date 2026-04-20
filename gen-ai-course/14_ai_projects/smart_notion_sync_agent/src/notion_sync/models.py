from __future__ import annotations
from enum import Enum
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field
from datetime import datetime


class SyncAction(str, Enum):
    FULL_SYNC = "full_sync"
    INCREMENTAL_SYNC = "incremental_sync"
    SOURCE_SYNC = "source_sync"

    @classmethod
    def __members__(cls):
        return {name: member.value for name, member in super().__members__.items()}


class SyncSource(str, Enum):
    GOOGLE_CALENDAR = "google_calendar"
    GOOGLE_DRIVE = "google_drive"
    GMAIL = "gmail"

    @classmethod
    def __members__(cls):
        return {name: member.value for name, member in super().__members__.items()}


class SyncDirection(str, Enum):
    NOTION_TO_SOURCE = "notion_to_source"
    SOURCE_TO_NOTION = "source_to_notion"
    BIDIRECTIONAL = "bidirectional"

    @classmethod
    def __members__(cls):
        return {name: member.value for name, member in super().__members__.items()}


class SyncRequest(BaseModel):
    action: SyncAction = Field(..., description="Type of sync to perform")
    sources: Optional[List[SyncSource]] = Field(
        default=None,
        description="Sources to sync",
    )
    direction: SyncDirection = Field(
        default=SyncDirection.BIDIRECTIONAL,
        description="Direction of sync",
    )

    model_config = {
        "use_enum_values": True,
        "json_schema_extra": {
            "examples": [
                {
                    "action": "full_sync",
                    "sources": ["google_calendar"],
                    "direction": "bidirectional",
                }
            ]
        },
    }


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


class SlackEventRequest(BaseModel):
    type: str = Field(..., description="Slack event type (e.g. url_verification, event_callback)")
    challenge: Optional[str] = Field(default=None, description="Challenge token for URL verification")
    event: Optional[Dict[str, Any]] = Field(default=None, description="Slack event payload")

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "type": "event_callback",
                    "event": {
                        "type": "message",
                        "text": "Fix the login bug by EOD",
                        "user": "U12345",
                        "channel": "C12345",
                        "ts": "1712345678.000100",
                    },
                }
            ]
        }
    }


class HealthStatus(BaseModel):
    all_systems_healthy: bool
    uptime_hours: float
    error_rate: float
    next_sync: Optional[str] = None
    integrations: Dict[str, Dict[str, Any]] = {}
