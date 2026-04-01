"""Conditional edge routing functions for the customer support graph."""

from __future__ import annotations

from typing import Literal

from support.config import settings
from support.graph.state import SupportState


def route_after_classifier(
    state: SupportState,
) -> Literal["billing_retrieval", "technical_retrieval", "general_retrieval"]:
    """
    Branch on issue_type after classification.

    Each branch leads to the shared retrieval node but the label allows
    future per-type customisation without changing node logic.
    """
    issue_type = state.get("issue_type", "general")

    routes = {
        "billing": "billing_retrieval",
        "technical": "technical_retrieval",
        "general": "general_retrieval",
        "greeting": "response_generator",
    }
    return routes.get(issue_type, "general_retrieval")  # type: ignore[return-value]


def route_after_response(
    state: SupportState,
) -> Literal["feedback_evaluator", "__end__"]:
    """
    Decide whether to run feedback evaluation.
    Greetings skip feedback and just end.
    """
    if state.get("issue_type") == "greeting":
        return "__end__"
    return "feedback_evaluator"


def route_after_feedback(
    state: SupportState,
) -> Literal["reasoner", "escalation", "__end__"]:
    """
    Decide what to do after the feedback evaluator runs.

    - helpful         → end the conversation
    - not_helpful     → retry reasoning (up to MAX_RETRIES)
    - retries exceeded → escalate to human
    """
    signal = state.get("feedback_signal", "helpful")
    retry_count = state.get("retry_count", 0)

    if signal == "helpful":
        return "__end__"

    if retry_count >= settings.MAX_RETRIES:
        return "escalation"

    return "reasoner"
