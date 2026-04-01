"""Tests for FastAPI endpoints."""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from fastapi.testclient import TestClient
from langchain_core.messages import AIMessage, HumanMessage


@pytest.fixture
def client():
    """Create a test client with the graph pre-initialised."""
    import core.graph_runner as graph_runner
    import src.main as main_module

    mock_graph = MagicMock()

    # Patch graph_runner._graph directly – this is what get_graph() reads
    original = graph_runner._graph
    graph_runner._graph = mock_graph

    test_client = TestClient(main_module.app, raise_server_exceptions=False)
    test_client._mock_graph = mock_graph

    yield test_client

    graph_runner._graph = original


class TestHealthEndpoint:
    def test_health_returns_ok(self, client):
        response = client.get("/health")
        assert response.status_code == 200
        assert response.json()["status"] == "ok"
        assert response.json()["service"] == "customer-support-engine"


class TestStartSupportEndpoint:
    def _setup_graph(self, client, reply="Here is your answer.", issue_type="general", severity="low"):
        mock_graph = client._mock_graph
        mock_graph.invoke.return_value = {
            "messages": [AIMessage(content=reply)],
            "issue_type": issue_type,
            "severity": severity,
            "status": "resolved",
        }

    def test_start_returns_reply(self, client):
        self._setup_graph(client, reply="Try restarting your device.")
        response = client.post("/support/start", json={"message": "my device is broken"})

        assert response.status_code == 200
        data = response.json()
        assert "Try restarting" in data["reply"]
        assert "conversation_id" in data

    def test_start_generates_conversation_id_when_not_provided(self, client):
        self._setup_graph(client)
        response = client.post("/support/start", json={"message": "hello"})

        assert response.status_code == 200
        data = response.json()
        assert data["conversation_id"] is not None
        assert len(data["conversation_id"]) > 0

    def test_start_uses_provided_conversation_id(self, client):
        self._setup_graph(client)
        response = client.post(
            "/support/start",
            json={"message": "hello", "conversation_id": "my-convo-id"},
        )

        assert response.status_code == 200
        assert response.json()["conversation_id"] == "my-convo-id"

    def test_start_returns_issue_type_and_severity(self, client):
        self._setup_graph(client, issue_type="billing", severity="high")
        response = client.post("/support/start", json={"message": "wrong charge"})

        data = response.json()
        assert data["issue_type"] == "billing"
        assert data["severity"] == "high"

    def test_start_returns_fallback_reply_when_no_ai_messages(self, client):
        client._mock_graph.invoke.return_value = {
            "messages": [HumanMessage(content="user message only")],
            "issue_type": "general",
            "severity": "low",
            "status": "resolved",
        }
        response = client.post("/support/start", json={"message": "hello"})

        assert response.status_code == 200
        assert "could not process" in response.json()["reply"]

    def test_start_returns_503_when_graph_not_initialised(self, client):
        import core.graph_runner as graph_runner
        original = graph_runner._graph
        graph_runner._graph = None

        try:
            response = client.post("/support/start", json={"message": "hello"})
            assert response.status_code == 503
        finally:
            graph_runner._graph = original

    def test_start_returns_500_on_graph_exception(self, client):
        client._mock_graph.invoke.side_effect = RuntimeError("LLM timeout")
        response = client.post("/support/start", json={"message": "hello"})

        assert response.status_code == 500
