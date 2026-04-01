import pytest
from unittest.mock import AsyncMock, patch
from inbox_cleaner.models import ClassifyRequest, ClassifyResponse


def test_classify_request():
    req = ClassifyRequest(
        from_address="hr@company.com",
        subject="Interview Invitation",
        body="We are pleased to invite you...",
    )
    assert req.from_address == "hr@company.com"


def test_classify_response():
    resp = ClassifyResponse(
        email_id="msg_123",
        classification={
            "category": "job_application_response",
            "confidence": 0.95,
            "priority": "high",
            "reasoning": "Interview invitation",
        },
        actions_taken=[],
    )
    assert resp.email_id == "msg_123"
    assert resp.classification["category"] == "job_application_response"
