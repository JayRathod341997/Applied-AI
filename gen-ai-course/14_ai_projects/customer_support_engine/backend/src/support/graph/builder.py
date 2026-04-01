"""Assemble the LangGraph StateGraph for the customer support engine."""

from __future__ import annotations

from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph import END, StateGraph

from support.graph.edges import route_after_classifier, route_after_feedback, route_after_response
from support.graph.nodes import (
    classifier_node,
    escalation_node,
    feedback_evaluator_node,
    reasoner_node,
    response_generator_node,
    retrieval_node,
    router_node,
)
from support.graph.state import SupportState


def build_graph(checkpointer=None):
    """
    Build and compile the customer support LangGraph StateGraph.

    Parameters
    ----------
    checkpointer:
        A LangGraph checkpointer instance (e.g. CosmosDBCheckpointer or
        MemorySaver). Falls back to MemorySaver when None.

    Returns
    -------
    CompiledGraph
        The compiled, runnable LangGraph graph.
    """
    if checkpointer is None:
        checkpointer = MemorySaver()

    builder = StateGraph(SupportState)

    # ------------------------------------------------------------------
    # Register nodes
    # ------------------------------------------------------------------
    builder.add_node("classifier", classifier_node)

    # Three retrieval aliases that all map to the same function so that
    # conditional edges from the router can target distinct labels while
    # reusing the same logic.
    builder.add_node("billing_retrieval", retrieval_node)
    builder.add_node("technical_retrieval", retrieval_node)
    builder.add_node("general_retrieval", retrieval_node)

    builder.add_node("reasoner", reasoner_node)
    builder.add_node("response_generator", response_generator_node)
    builder.add_node("feedback_evaluator", feedback_evaluator_node)
    builder.add_node("escalation", escalation_node)

    # ------------------------------------------------------------------
    # Entry point
    # ------------------------------------------------------------------
    builder.set_entry_point("classifier")

    # ------------------------------------------------------------------
    # Conditional edges
    # ------------------------------------------------------------------

    # After classification: branch by issue_type → retrieval or greeting
    builder.add_conditional_edges(
        "classifier",
        route_after_classifier,
        {
            "billing_retrieval": "billing_retrieval",
            "technical_retrieval": "technical_retrieval",
            "general_retrieval": "general_retrieval",
            "response_generator": "response_generator",
        },
    )

    # Each retrieval branch converges on the reasoner
    builder.add_edge("billing_retrieval", "reasoner")
    builder.add_edge("technical_retrieval", "reasoner")
    builder.add_edge("general_retrieval", "reasoner")

    builder.add_edge("reasoner", "response_generator")
    
    # After response: skip feedback for greetings
    builder.add_conditional_edges(
        "response_generator",
        route_after_response,
        {
            "feedback_evaluator": "feedback_evaluator",
            "__end__": END,
        },
    )
    builder.add_edge("escalation", END)


    # After feedback: loop back to reasoner, escalate, or end
    builder.add_conditional_edges(
        "feedback_evaluator",
        route_after_feedback,
        {
            "reasoner": "reasoner",
            "escalation": "escalation",
            "__end__": END,
        },
    )

    return builder.compile(checkpointer=checkpointer)
