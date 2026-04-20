from langgraph.graph import StateGraph, END

from .state import SlackSyncState
from .nodes import (
    ingest_node,
    classify_node,
    extract_node,
    task_node,
    note_node,
    slack_ack_node,
    poll_node,
    format_node,
    notify_node,
    route_classification,
    route_changes,
)


def build_slack_to_notion_graph():
    g = StateGraph(SlackSyncState)

    g.add_node("ingest", ingest_node)
    g.add_node("classify", classify_node)
    g.add_node("extract", extract_node)
    g.add_node("task", task_node)
    g.add_node("note", note_node)
    g.add_node("slack_ack", slack_ack_node)

    g.set_entry_point("ingest")
    g.add_edge("ingest", "classify")
    g.add_conditional_edges(
        "classify",
        route_classification,
        {"task": "extract", "note": "note", "skip": END},
    )
    g.add_edge("extract", "task")
    g.add_edge("task", "slack_ack")
    g.add_edge("note", "slack_ack")
    g.add_edge("slack_ack", END)

    return g.compile()


def build_notion_to_slack_graph():
    g = StateGraph(SlackSyncState)

    g.add_node("poll", poll_node)
    g.add_node("format", format_node)
    g.add_node("notify", notify_node)

    g.set_entry_point("poll")
    g.add_conditional_edges(
        "poll",
        route_changes,
        {"changed": "format", "no_changes": END},
    )
    g.add_edge("format", "notify")
    g.add_edge("notify", END)

    return g.compile()


slack_to_notion = build_slack_to_notion_graph()
notion_to_slack = build_notion_to_slack_graph()
