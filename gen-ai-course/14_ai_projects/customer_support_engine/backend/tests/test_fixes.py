import pytest
from unittest.mock import MagicMock, patch
from langchain_core.messages import AIMessage, HumanMessage
from fastapi.testclient import TestClient
from src.main import app
import core.graph_runner as graph_runner

@pytest.fixture
def client():
    original = graph_runner._graph
    mock_graph = MagicMock()
    graph_runner._graph = mock_graph
    yield TestClient(app)
    graph_runner._graph = original

def test_greeting_classification():
    from support.graph.nodes import classifier_node
    
    mock_llm = MagicMock()
    mock_llm.invoke.return_value = AIMessage(content='{"issue_type": "greeting", "severity": null}')
    
    with patch("support.graph.nodes._get_llm", return_value=mock_llm):
        state = {"messages": [HumanMessage(content="Hello there")], "issue_type": None, "severity": "low"}
        result = classifier_node(state)
        assert result["issue_type"] == "greeting"
        assert result["severity"] is None

def test_history_endpoint(client):
    mock_graph = graph_runner._graph
    mock_state = MagicMock()
    mock_state.values = {
        "messages": [
            HumanMessage(content="Hello", id="m1"),
            AIMessage(content="How can I help?", id="m2")
        ]
    }
    mock_graph.get_state.return_value = mock_state
    
    response = client.get("/support/history/test-conv")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 2
    assert data[0]["content"] == "Hello"
    assert data[1]["role"] == "assistant"

def test_run_graph_persistence():
    from core.graph_runner import run_graph
    mock_graph = MagicMock()
    with patch("core.graph_runner._graph", mock_graph):
        run_graph("conv-1", "hello")
        # Ensure only messages are passed
        args, kwargs = mock_graph.invoke.call_args
        assert "messages" in args[0]
        assert len(args[0]) == 1 # Only messages
        assert kwargs["config"]["configurable"]["thread_id"] == "conv-1"
