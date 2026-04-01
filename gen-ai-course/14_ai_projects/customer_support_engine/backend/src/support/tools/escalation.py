"""Cosmos DB escalation handler for human handoff tickets."""

from __future__ import annotations

import logging
import uuid
from datetime import datetime, timezone
from typing import TYPE_CHECKING

from azure.cosmos import CosmosClient, exceptions

if TYPE_CHECKING:
    from support.graph.state import SupportState

logger = logging.getLogger(__name__)


class EscalationHandler:
    """
    Persists escalation tickets to Azure Cosmos DB.

    Parameters
    ----------
    endpoint:
        Cosmos DB account URI.
    key:
        Primary or secondary master key.
    database_name:
        Name of the Cosmos DB database.
    container_name:
        Name of the container used to store escalation tickets.
    """

    def __init__(
        self,
        endpoint: str,
        key: str,
        database_name: str,
        container_name: str,
    ) -> None:
        client = CosmosClient(url=endpoint, credential=key)
        db = client.get_database_client(database_name)
        self._container = db.get_container_client(container_name)

    def create_ticket(self, state: "SupportState") -> str:
        """
        Persist an escalation ticket derived from the current graph state.

        Parameters
        ----------
        state:
            The current SupportState snapshot.

        Returns
        -------
        str
            The unique ticket ID assigned to this escalation.
        """
        ticket_id = f"ESC-{uuid.uuid4().hex[:8].upper()}"
        conversation_id = state.get("conversation_id", "unknown")

        # Serialize messages as plain dicts so Cosmos can store them
        serialized_messages = []
        for msg in state.get("messages", []):
            try:
                serialized_messages.append(
                    {"type": msg.__class__.__name__, "content": msg.content}
                )
            except AttributeError:
                serialized_messages.append({"type": "unknown", "content": str(msg)})

        ticket = {
            "id": ticket_id,
            "conversation_id": conversation_id,
            "issue_type": state.get("issue_type"),
            "severity": state.get("severity"),
            "resolution_steps": state.get("resolution_steps", []),
            "retry_count": state.get("retry_count", 0),
            "messages": serialized_messages,
            "status": "escalated",
            "created_at": datetime.now(timezone.utc).isoformat(),
        }

        try:
            self._container.upsert_item(ticket)
            logger.info("Escalation ticket %s saved to Cosmos DB", ticket_id)
        except exceptions.CosmosHttpResponseError as exc:
            logger.error("Failed to save escalation ticket: %s", exc, exc_info=True)

        return ticket_id
