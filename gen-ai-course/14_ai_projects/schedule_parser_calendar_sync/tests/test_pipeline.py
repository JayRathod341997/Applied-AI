import pytest
from schedule_parser.models import ParseScheduleResponse, ParsedEvent


def test_parsed_event():
    event = ParsedEvent(
        title="Security Shift - Main Gate",
        date="2026-04-02",
        start_time="06:00",
        end_time="14:00",
        location="Building A",
    )
    assert event.title == "Security Shift - Main Gate"
    assert event.date == "2026-04-02"


def test_parse_response():
    resp = ParseScheduleResponse(status="success", events_created=1)
    assert resp.status == "success"
    assert resp.events_created == 1
