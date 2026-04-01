"""Shared LangGraph instance and synchronous invocation helper."""

from __future__ import annotations

import logging
from typing import Any, Dict, Optional

from langchain_core.messages import HumanMessage

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Singleton graph instance – set during application lifespan startup
# ---------------------------------------------------------------------------

_graph = None


def set_graph(graph: Any) -> None:
    """Store the compiled graph after startup initialisation."""
    global _graph
    _graph = graph


def get_graph() -> Optional[Any]:
    """Return the compiled graph, or None if not yet initialised."""
    return _graph


def run_graph(conversation_id: str, user_message: str) -> Dict[str, Any]:
    """Invoke the LangGraph synchronously for a given conversation."""
    config = {"configurable": {"thread_id": conversation_id}}

    # Only pass the new message; LangGraph + Checkpointer handles the rest
    input_data = {
        "messages": [HumanMessage(content=user_message)],
    }

    result = _graph.invoke(input_data, config=config)
    return result
