from __future__ import annotations

from typing import Annotated, Literal

from langgraph.graph.message import add_messages
from typing_extensions import TypedDict


class SupportState(TypedDict):
    # Conversation messages – merged with add_messages reducer
    messages: Annotated[list, add_messages]

    # Classification results
    issue_type: Literal["billing", "technical", "general", "greeting"] | None
    severity: Literal["low", "medium", "high", "critical"] | None

    # Knowledge retrieval
    kb_chunks: list[str]

    # Resolution output
    resolution_steps: list[str]
    status: Literal["open", "resolving", "resolved", "escalated"] | None

    # Feedback loop
    feedback_signal: Literal["helpful", "not_helpful"] | None
    retry_count: int

    # Tracing
    conversation_id: str
