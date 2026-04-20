import datetime as dt
import sys
import types

if "notion_client" not in sys.modules:
    notion_client_stub = types.ModuleType("notion_client")

    class _DummyNotionClient:
        def __init__(self, *args, **kwargs):
            pass

    notion_client_stub.Client = _DummyNotionClient
    sys.modules["notion_client"] = notion_client_stub

if "slack_sdk" not in sys.modules:
    slack_sdk_stub = types.ModuleType("slack_sdk")
    slack_sdk_errors_stub = types.ModuleType("slack_sdk.errors")

    class _DummyWebClient:
        def __init__(self, *args, **kwargs):
            pass

    class _DummySlackApiError(Exception):
        def __init__(self, *args, response=None, **kwargs):
            super().__init__(*args)
            self.response = response

    slack_sdk_stub.WebClient = _DummyWebClient
    slack_sdk_errors_stub.SlackApiError = _DummySlackApiError

    sys.modules["slack_sdk"] = slack_sdk_stub
    sys.modules["slack_sdk.errors"] = slack_sdk_errors_stub

from notion_sync.pipelines.slack import nodes
from notion_sync.pipelines.slack.state import (
    SlackSyncState,
    _last_property_snapshot,
)


class _FixedDate:
    @classmethod
    def today(cls):
        return dt.date(2026, 4, 15)


def test_poll_node_uses_due_date_filter(monkeypatch):
    _last_property_snapshot.clear()
    monkeypatch.setattr(nodes, "date", _FixedDate)
    monkeypatch.setattr(nodes.settings, "notion_tasks_db", "tasks_db", raising=False)

    called = {}

    def fake_query(database_id, filter_dict=None):
        called["database_id"] = database_id
        called["filter_dict"] = filter_dict
        return []

    monkeypatch.setattr(nodes.notion, "query_database", fake_query)

    state = nodes.poll_node(SlackSyncState())

    assert state.notion_changes == []
    assert called["database_id"] == "tasks_db"
    assert called["filter_dict"] == {
        "property": "Due Date",
        "date": {"equals": "2026-04-15"},
    }


def test_poll_node_change_detection_still_works(monkeypatch):
    _last_property_snapshot.clear()
    monkeypatch.setattr(nodes, "date", _FixedDate)
    monkeypatch.setattr(nodes.settings, "notion_tasks_db", "tasks_db", raising=False)

    page = {"id": "page_1", "last_edited_time": "2026-04-15T09:00:00Z"}

    def fake_query(database_id, filter_dict=None):
        return [page]

    monkeypatch.setattr(nodes.notion, "query_database", fake_query)

    first = nodes.poll_node(SlackSyncState())
    second = nodes.poll_node(SlackSyncState())

    assert len(first.notion_changes) == 1
    assert first.notion_changes[0]["id"] == "page_1"
    assert second.notion_changes == []


def test_poll_node_missing_tasks_db_returns_no_changes(monkeypatch):
    _last_property_snapshot.clear()
    monkeypatch.setattr(nodes.settings, "notion_tasks_db", "", raising=False)

    called = {"query": False}

    def fake_query(database_id, filter_dict=None):
        called["query"] = True
        return []

    monkeypatch.setattr(nodes.notion, "query_database", fake_query)

    state = nodes.poll_node(SlackSyncState())

    assert state.notion_changes == []
    assert called["query"] is False


def test_format_node_includes_old_and_new_values():
    state = SlackSyncState(
        notion_changes=[
            {
                "properties": {
                    "Name": {"title": [{"plain_text": "Prepare report"}]},
                    "Status": {"select": {"name": "Done"}},
                },
                "_field_changes": [
                    {"field": "Status", "old": "In Progress", "new": "Done"},
                    {"field": "Priority", "old": "High", "new": "Low"},
                ],
            }
        ]
    )

    updated = nodes.format_node(state)

    assert "*Prepare report* -> Done" in updated.slack_message
    assert "Status: Old: In Progress | New: Done" in updated.slack_message
    assert "Priority: Old: High | New: Low" in updated.slack_message
