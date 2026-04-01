"""Tests for LangGraph node functions."""

import json
import pytest
from unittest.mock import MagicMock, patch

from langchain_core.messages import AIMessage, HumanMessage


def make_state(**kwargs):
    base = {
        "messages": [],
        "issue_type": None,
        "severity": None,
        "kb_chunks": [],
        "resolution_steps": [],
        "status": None,
        "feedback_signal": None,
        "retry_count": 0,
        "conversation_id": "test-conv-123",
    }
    base.update(kwargs)
    return base


# ---------------------------------------------------------------------------
# classifier_node
# ---------------------------------------------------------------------------

class TestClassifierNode:
    @patch("support.graph.nodes._get_llm")
    def test_valid_classification_billing(self, mock_get_llm):
        mock_llm = MagicMock()
        mock_llm.invoke.return_value = AIMessage(
            content='{"issue_type": "billing", "severity": "high"}'
        )
        mock_get_llm.return_value = mock_llm

        from support.graph.nodes import classifier_node

        state = make_state(messages=[HumanMessage(content="My invoice is wrong")])
        result = classifier_node(state)

        assert result["issue_type"] == "billing"
        assert result["severity"] == "high"

    @patch("support.graph.nodes._get_llm")
    def test_valid_classification_technical(self, mock_get_llm):
        mock_llm = MagicMock()
        mock_llm.invoke.return_value = AIMessage(
            content='{"issue_type": "technical", "severity": "critical"}'
        )
        mock_get_llm.return_value = mock_llm

        from support.graph.nodes import classifier_node

        state = make_state(messages=[HumanMessage(content="App keeps crashing")])
        result = classifier_node(state)

        assert result["issue_type"] == "technical"
        assert result["severity"] == "critical"

    @patch("support.graph.nodes._get_llm")
    def test_invalid_json_defaults_to_general_low(self, mock_get_llm):
        mock_llm = MagicMock()
        mock_llm.invoke.return_value = AIMessage(content="not valid json")
        mock_get_llm.return_value = mock_llm

        from support.graph.nodes import classifier_node

        state = make_state(messages=[HumanMessage(content="what?")])
        result = classifier_node(state)

        assert result["issue_type"] == "general"
        assert result["severity"] == "low"

    @patch("support.graph.nodes._get_llm")
    def test_empty_messages_uses_empty_string(self, mock_get_llm):
        mock_llm = MagicMock()
        mock_llm.invoke.return_value = AIMessage(
            content='{"issue_type": "general", "severity": "low"}'
        )
        mock_get_llm.return_value = mock_llm

        from support.graph.nodes import classifier_node

        state = make_state(messages=[])
        result = classifier_node(state)

        assert result["issue_type"] == "general"


# ---------------------------------------------------------------------------
# router_node
# ---------------------------------------------------------------------------

class TestRouterNode:
    def test_router_node_returns_empty_dict(self):
        from support.graph.nodes import router_node

        state = make_state(issue_type="billing")
        result = router_node(state)

        assert result == {}

    def test_router_node_handles_none_issue_type(self):
        from support.graph.nodes import router_node

        state = make_state(issue_type=None)
        result = router_node(state)

        assert result == {}


# ---------------------------------------------------------------------------
# retrieval_node
# ---------------------------------------------------------------------------

class TestRetrievalNode:
    @patch("support.graph.nodes.KnowledgeBaseSearch")
    def test_retrieval_returns_kb_chunks(self, mock_kb_class):
        mock_kb = MagicMock()
        mock_kb.search.return_value = ["chunk 1", "chunk 2", "chunk 3"]
        mock_kb_class.return_value = mock_kb

        from support.graph.nodes import retrieval_node

        state = make_state(messages=[HumanMessage(content="payment failed")])
        result = retrieval_node(state)

        assert result["kb_chunks"] == ["chunk 1", "chunk 2", "chunk 3"]
        mock_kb.search.assert_called_once_with("payment failed", top_k=5)

    @patch("support.graph.nodes.KnowledgeBaseSearch")
    def test_retrieval_with_no_messages_uses_empty_query(self, mock_kb_class):
        mock_kb = MagicMock()
        mock_kb.search.return_value = []
        mock_kb_class.return_value = mock_kb

        from support.graph.nodes import retrieval_node

        state = make_state(messages=[])
        result = retrieval_node(state)

        assert result["kb_chunks"] == []
        mock_kb.search.assert_called_once_with("", top_k=5)


# ---------------------------------------------------------------------------
# reasoner_node
# ---------------------------------------------------------------------------

class TestReasonerNode:
    @patch("support.graph.nodes._get_llm")
    def test_reasoner_returns_steps_list(self, mock_get_llm):
        mock_llm = MagicMock()
        mock_llm.invoke.return_value = AIMessage(
            content='["Step 1: Check account", "Step 2: Verify payment"]'
        )
        mock_get_llm.return_value = mock_llm

        from support.graph.nodes import reasoner_node

        state = make_state(
            messages=[HumanMessage(content="can't log in")],
            kb_chunks=["Reset password instructions..."],
        )
        result = reasoner_node(state)

        assert result["resolution_steps"] == ["Step 1: Check account", "Step 2: Verify payment"]

    @patch("support.graph.nodes._get_llm")
    def test_reasoner_handles_non_json_response(self, mock_get_llm):
        mock_llm = MagicMock()
        mock_llm.invoke.return_value = AIMessage(content="Try resetting your password.")
        mock_get_llm.return_value = mock_llm

        from support.graph.nodes import reasoner_node

        state = make_state(messages=[HumanMessage(content="help")])
        result = reasoner_node(state)

        assert isinstance(result["resolution_steps"], list)
        assert len(result["resolution_steps"]) == 1

    @patch("support.graph.nodes._get_llm")
    def test_reasoner_uses_kb_context(self, mock_get_llm):
        mock_llm = MagicMock()
        mock_llm.invoke.return_value = AIMessage(content='["Step 1: Follow KB guide"]')
        mock_get_llm.return_value = mock_llm

        from support.graph.nodes import reasoner_node

        state = make_state(
            messages=[HumanMessage(content="billing issue")],
            kb_chunks=["billing guide chunk"],
        )
        reasoner_node(state)

        call_args = mock_llm.invoke.call_args[0][0]
        human_msg = next(m for m in call_args if isinstance(m, HumanMessage))
        assert "billing guide chunk" in human_msg.content


# ---------------------------------------------------------------------------
# response_generator_node
# ---------------------------------------------------------------------------

class TestResponseGeneratorNode:
    @patch("support.graph.nodes._get_llm")
    def test_response_generator_returns_ai_message(self, mock_get_llm):
        mock_llm = MagicMock()
        mock_llm.invoke.return_value = AIMessage(
            content="Thank you for reaching out! Here's how to fix your issue..."
        )
        mock_get_llm.return_value = mock_llm

        from support.graph.nodes import response_generator_node

        state = make_state(
            resolution_steps=["Step 1: Do this", "Step 2: Do that"],
            issue_type="technical",
            severity="medium",
        )
        result = response_generator_node(state)

        assert result["status"] == "resolved"
        assert len(result["messages"]) == 1
        assert isinstance(result["messages"][0], AIMessage)
        assert "Thank you" in result["messages"][0].content


# ---------------------------------------------------------------------------
# feedback_evaluator_node
# ---------------------------------------------------------------------------

class TestFeedbackEvaluatorNode:
    @patch("support.graph.nodes._get_llm")
    def test_helpful_signal_does_not_increment_retry(self, mock_get_llm):
        mock_llm = MagicMock()
        mock_llm.invoke.return_value = AIMessage(content='{"signal": "helpful"}')
        mock_get_llm.return_value = mock_llm

        from support.graph.nodes import feedback_evaluator_node

        state = make_state(
            messages=[HumanMessage(content="Thanks, that worked!")],
            retry_count=0,
        )
        result = feedback_evaluator_node(state)

        assert result["feedback_signal"] == "helpful"
        assert result["retry_count"] == 0

    @patch("support.graph.nodes._get_llm")
    def test_not_helpful_increments_retry_count(self, mock_get_llm):
        mock_llm = MagicMock()
        mock_llm.invoke.return_value = AIMessage(content='{"signal": "not_helpful"}')
        mock_get_llm.return_value = mock_llm

        from support.graph.nodes import feedback_evaluator_node

        state = make_state(
            messages=[HumanMessage(content="This didn't help at all")],
            retry_count=1,
        )
        result = feedback_evaluator_node(state)

        assert result["feedback_signal"] == "not_helpful"
        assert result["retry_count"] == 2

    @patch("support.graph.nodes._get_llm")
    def test_invalid_json_defaults_to_helpful(self, mock_get_llm):
        mock_llm = MagicMock()
        mock_llm.invoke.return_value = AIMessage(content="not json")
        mock_get_llm.return_value = mock_llm

        from support.graph.nodes import feedback_evaluator_node

        state = make_state(messages=[HumanMessage(content="ok")])
        result = feedback_evaluator_node(state)

        assert result["feedback_signal"] == "helpful"
