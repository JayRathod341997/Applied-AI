import pytest
from unittest.mock import patch, MagicMock
from notion_sync.models import SyncRequest, SyncResponse


def test_sync_request_defaults():
    req = SyncRequest(action="full_sync")
    assert req.direction == "bidirectional"
    assert req.sources is None


def test_sync_request_custom():
    req = SyncRequest(
        action="source_sync",
        sources=["google_calendar"],
        direction="notion_to_source",
    )
    assert req.sources == ["google_calendar"]
    assert req.direction == "notion_to_source"
