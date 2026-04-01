"""Tests for EscalationHandler."""

import pytest
from unittest.mock import MagicMock, patch

from langchain_core.messages import AIMessage, HumanMessage

from support.tools.escalation import EscalationHandler


def make_state(**kwargs):
    base = {
        "messages": [HumanMessage(content="nothing worked"), AIMessage(content="escalating")],
        "issue_type": "technical",
        "severity": "high",
        "kb_chunks": [],
        "resolution_steps": ["Step 1", "Step 2"],
        "status": "escalated",
        "feedback_signal": "not_helpful",
        "retry_count": 3,
        "conversation_id": "conv-abc",
    }
    base.update(kwargs)
    return base


@pytest.fixture
def mock_cosmos():
    with patch("support.tools.escalation.CosmosClient") as mock_cls:
        mock_client = MagicMock()
        mock_db = MagicMock()
        mock_container = MagicMock()

        mock_cls.return_value = mock_client
        mock_client.get_database_client.return_value = mock_db
        mock_db.get_container_client.return_value = mock_container

        yield mock_container


class TestEscalationHandler:
    def test_create_ticket_returns_esc_prefixed_id(self, mock_cosmos):
        handler = EscalationHandler(
            endpoint="https://fake.cosmos.azure.com",
            key="fake-key",
            database_name="support_db",
            container_name="conversations",
        )
        ticket_id = handler.create_ticket(make_state())

        assert ticket_id.startswith("ESC-")
        assert len(ticket_id) == 12  # "ESC-" + 8 hex chars

    def test_create_ticket_calls_upsert(self, mock_cosmos):
        handler = EscalationHandler(
            endpoint="https://fake.cosmos.azure.com",
            key="fake-key",
            database_name="support_db",
            container_name="conversations",
        )
        handler.create_ticket(make_state())

        mock_cosmos.upsert_item.assert_called_once()

    def test_create_ticket_document_has_correct_fields(self, mock_cosmos):
        handler = EscalationHandler(
            endpoint="https://fake.cosmos.azure.com",
            key="fake-key",
            database_name="support_db",
            container_name="conversations",
        )
        state = make_state(
            conversation_id="test-conv",
            issue_type="billing",
            severity="critical",
            resolution_steps=["Step A"],
            retry_count=2,
        )
        handler.create_ticket(state)

        doc = mock_cosmos.upsert_item.call_args[0][0]
        assert doc["conversation_id"] == "test-conv"
        assert doc["issue_type"] == "billing"
        assert doc["severity"] == "critical"
        assert doc["resolution_steps"] == ["Step A"]
        assert doc["retry_count"] == 2
        assert doc["status"] == "escalated"

    def test_create_ticket_serializes_messages(self, mock_cosmos):
        handler = EscalationHandler(
            endpoint="https://fake.cosmos.azure.com",
            key="fake-key",
            database_name="support_db",
            container_name="conversations",
        )
        state = make_state(
            messages=[HumanMessage(content="help"), AIMessage(content="sorry")]
        )
        handler.create_ticket(state)

        doc = mock_cosmos.upsert_item.call_args[0][0]
        assert len(doc["messages"]) == 2
        assert doc["messages"][0]["type"] == "HumanMessage"
        assert doc["messages"][0]["content"] == "help"
        assert doc["messages"][1]["type"] == "AIMessage"

    def test_create_ticket_handles_cosmos_error_gracefully(self, mock_cosmos):
        from azure.cosmos import exceptions

        mock_cosmos.upsert_item.side_effect = exceptions.CosmosHttpResponseError(
            message="Service Unavailable"
        )

        handler = EscalationHandler(
            endpoint="https://fake.cosmos.azure.com",
            key="fake-key",
            database_name="support_db",
            container_name="conversations",
        )
        # Should not raise; just logs the error and still returns ticket_id
        ticket_id = handler.create_ticket(make_state())
        assert ticket_id.startswith("ESC-")
