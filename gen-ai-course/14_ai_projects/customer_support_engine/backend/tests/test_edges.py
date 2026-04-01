"""Tests for graph routing edge functions."""

import pytest
from unittest.mock import patch

from support.graph.edges import route_after_classifier, route_after_feedback


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
        "conversation_id": "test-123",
    }
    base.update(kwargs)
    return base


class TestRouteAfterClassifier:
    def test_billing_routes_to_billing_retrieval(self):
        state = make_state(issue_type="billing")
        assert route_after_classifier(state) == "billing_retrieval"

    def test_technical_routes_to_technical_retrieval(self):
        state = make_state(issue_type="technical")
        assert route_after_classifier(state) == "technical_retrieval"

    def test_general_routes_to_general_retrieval(self):
        state = make_state(issue_type="general")
        assert route_after_classifier(state) == "general_retrieval"

    def test_unknown_issue_type_defaults_to_general(self):
        state = make_state(issue_type="unknown_type")
        assert route_after_classifier(state) == "general_retrieval"

    def test_none_issue_type_defaults_to_general(self):
        state = make_state(issue_type=None)
        assert route_after_classifier(state) == "general_retrieval"


class TestRouteAfterFeedback:
    def test_helpful_signal_ends_conversation(self):
        state = make_state(feedback_signal="helpful", retry_count=0)
        assert route_after_feedback(state) == "__end__"

    def test_not_helpful_below_max_retries_goes_to_reasoner(self):
        with patch("support.graph.edges.settings") as mock_settings:
            mock_settings.MAX_RETRIES = 3
            state = make_state(feedback_signal="not_helpful", retry_count=1)
            assert route_after_feedback(state) == "reasoner"

    def test_not_helpful_at_max_retries_escalates(self):
        with patch("support.graph.edges.settings") as mock_settings:
            mock_settings.MAX_RETRIES = 3
            state = make_state(feedback_signal="not_helpful", retry_count=3)
            assert route_after_feedback(state) == "escalation"

    def test_not_helpful_exceeding_max_retries_escalates(self):
        with patch("support.graph.edges.settings") as mock_settings:
            mock_settings.MAX_RETRIES = 3
            state = make_state(feedback_signal="not_helpful", retry_count=5)
            assert route_after_feedback(state) == "escalation"

    def test_none_signal_falls_through_to_reasoner(self):
        # None is stored as a key so .get() returns None (not the default "helpful")
        # None != "helpful" and retry_count < MAX_RETRIES → routes to reasoner
        with patch("support.graph.edges.settings") as mock_settings:
            mock_settings.MAX_RETRIES = 3
            state = make_state(feedback_signal=None, retry_count=0)
            assert route_after_feedback(state) == "reasoner"
