from typing import Optional, Literal
from dataclasses import dataclass, field


@dataclass
class SlackSyncState:
    slack_event: Optional[dict] = None
    message_text: str = ""
    channel_id: str = ""
    thread_ts: Optional[str] = None
    user_id: str = ""
    classification: Optional[Literal["task", "note", "skip"]] = None
    notion_page_id: Optional[str] = None

    # Extracted structured task fields (populated by extract_node)
    task_name: Optional[str] = None
    task_due_date: Optional[str] = None
    task_priority: Optional[str] = None
    task_related_job: Optional[str] = None
    task_related_lead: Optional[str] = None

    notion_changes: list[dict] = field(default_factory=list)
    slack_message: Optional[str] = None
    target_channel: Optional[str] = None


# Tracks last seen property values per Notion page ID for field-level diffing
_last_property_snapshot: dict[str, dict[str, str | None]] = {}
