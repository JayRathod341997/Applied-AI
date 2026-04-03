import pytest
from unittest.mock import patch, AsyncMock, MagicMock
from src.inbox_cleaner.pipelines.email_pipeline import EmailPipeline
from src.inbox_cleaner.utils.exceptions import GmailIntegrationError, LLMClassificationError, LLMDraftError

@pytest.fixture
def pipeline():
    return EmailPipeline()

@pytest.mark.asyncio
async def test_gmail_integration_error_caught(pipeline, mocker):
    mocker.patch.object(pipeline.classifier, "classify", return_value={
        "category": "newsletter",
        "priority": "low"
    })
    
    # Mock modify_labels to raise exception
    mock_get_or_create = mocker.patch.object(pipeline.gmail, "get_or_create_label", return_value="label-123")
    mock_modify = mocker.patch.object(pipeline.gmail, "modify_labels", side_effect=GmailIntegrationError("Gmail is down"))
    mock_notify_slack_error = mocker.patch.object(pipeline, "notify_slack_error", new_callable=AsyncMock)

    email_data = {"id": "123", "from": "test@test.com", "subject": "Test", "body": "Hello"}
    result = await pipeline.process_email(email_data)

    # Should have a failed label action
    failed_action = next((a for a in result["actions_taken"] if a["action"] == "label" and a.get("status") == "failed"), None)
    assert failed_action is not None
    assert "Gmail is down" in failed_action["error"]

    # Slack notification for error must be triggered
    mock_notify_slack_error.assert_called()


@pytest.mark.asyncio
async def test_llm_classification_error_caught(pipeline, mocker):
    # Mock classifier to raise Exception
    mock_classify = mocker.patch.object(pipeline.classifier, "classify", side_effect=LLMClassificationError("Token limits"))
    mock_notify_slack_error = mocker.patch.object(pipeline, "notify_slack_error", new_callable=AsyncMock)
    
    # Mock gmail label since it falls back to newsletter
    mocker.patch.object(pipeline.gmail, "get_or_create_label", return_value="label-123")
    mocker.patch.object(pipeline.gmail, "modify_labels", return_value=True)

    email_data = {"id": "123", "from": "test@test.com", "subject": "Test", "body": "Hello"}
    result = await pipeline.process_email(email_data)

    # Classification should fallback to generic details
    assert result["classification"]["category"] == "newsletter"
    assert result["classification"]["reasoning"] == "Classification failed explicitly"

    # Slack error notification must be triggered for classification failure
    mock_notify_slack_error.assert_called()


@pytest.mark.asyncio
async def test_llm_draft_error_caught(pipeline, mocker):
    mocker.patch.object(pipeline.classifier, "classify", return_value={
        "category": "client_communication",
        "priority": "high",
        "confidence": 0.9,
    })
    
    # Mock drafter to raise Exception
    mocker.patch.object(pipeline.drafter, "draft_reply", side_effect=LLMDraftError("Draft generation failed due to token limits"))
    
    # Mocks for Gmail
    mocker.patch.object(pipeline.gmail, "get_or_create_label", return_value="label-123")
    mocker.patch.object(pipeline.gmail, "modify_labels", return_value=True)

    mock_notify_slack_error = mocker.patch.object(pipeline, "notify_slack_error", new_callable=AsyncMock)

    email_data = {"id": "123", "from": "test@test.com", "subject": "Test", "body": "Hello"}
    result = await pipeline.process_email(email_data)

    # Should have a failed draft action
    failed_draft_action = next((a for a in result["actions_taken"] if a["action"] == "draft_reply" and a.get("status") == "failed"), None)
    assert failed_draft_action is not None
    assert "Draft generation failed" in failed_draft_action["error"]

    # Slack error notification must be triggered
    mock_notify_slack_error.assert_called()
