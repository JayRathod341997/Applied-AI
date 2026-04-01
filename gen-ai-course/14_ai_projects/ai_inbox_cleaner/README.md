# AI Inbox Cleaner

## Overview

Gmail email classifier and auto-organizer that uses LLM-powered categorization to sort, label, and draft replies for incoming emails. Integrates with Notion CRM and Slack for seamless workflow automation.

## Architecture

```
Gmail Poller --> Classification Agent --> Action Router --> Notification
  (Gmail API)     (LLM categorize)        (label/archive/    (Slack/Notion)
                                          draft/forward)
```

## Flow

1. Gmail API polls for new messages (or push notification via webhook)
2. ChatGroq (llama-3.1-8b) classifies each email into categories
3. Actions applied based on category:
   - **Security Job** -> Label "Jobs/Security", star, forward to Notion
   - **Real Estate Lead** -> Label "Leads/RE", forward to Notion CRM
   - **Client Communication** -> Label "Clients", star if urgent
   - **Job Application Response** -> Label "Applications", Slack alert
   - **Spam/Irrelevant** -> Archive
4. ChatGroq (llama-3.3-70b) drafts simple replies for approval
5. Urgent emails trigger Slack notifications

## Key Functionality

- **Smart categorization:** 6 email categories with confidence scores
- **Auto-labeling:** Gmail labels applied automatically
- **Spam cleanup:** Archive irrelevant messages
- **Reply drafting:** LLM generates reply drafts for approval
- **Lead forwarding:** Real estate leads auto-pushed to Notion CRM
- **Daily digest:** Summary of categorized emails

## Sample Input

```
Triggered by: Gmail push notification or APScheduler poll
New email: {
  "from": "hr@allieduniversal.com",
  "subject": "Interview Invitation - Executive Protection Agent",
  "body": "Dear Candidate, We are pleased to invite you for an interview..."
}
```

## Sample Output

```json
{
  "email_id": "gmail_msg_abc123",
  "classification": {
    "category": "job_application_response",
    "confidence": 0.97,
    "priority": "high",
    "reasoning": "Interview invitation for applied EP position"
  },
  "actions_taken": [
    {"action": "label", "label": "Applications/Interview"},
    {"action": "star"},
    {"action": "slack_notify", "channel": "#job-alerts", "sent": true},
    {"action": "draft_reply", "draft_id": "gmail_draft_789", "preview": "Thank you for the invitation..."}
  ]
}
```

## Setup

1. `cd ai_inbox_cleaner && uv venv && uv sync`
2. Set `GROQ_API_KEY` from console.groq.com
3. Create GCP project -> Enable Gmail API -> Create OAuth2 credentials -> Set `GOOGLE_SERVICE_ACCOUNT_JSON`, `GMAIL_USER_EMAIL`
4. Set `NOTION_API_KEY` + relevant DB IDs
5. Set `SLACK_WEBHOOK_URL`
6. `cp .env.example .env` -> Fill all keys
7. `uv run uvicorn src.inbox_cleaner.main:app --reload --port 8018`
8. `curl -X POST http://localhost:8018/sync/trigger`

## Environment Variables

| Variable | Required | Description |
|----------|----------|-------------|
| `GROQ_API_KEY` | Yes | Groq API key |
| `GOOGLE_SERVICE_ACCOUNT_JSON` | Yes | Path to Google service account JSON |
| `GMAIL_USER_EMAIL` | Yes | Gmail address to monitor |
| `SLACK_WEBHOOK_URL` | No | Slack webhook for alerts |
