# AI Inbox Cleaner

**AI Inbox Cleaner Agent**: _Monitors designated Gmail inboxes, intelligently filters and tags emails related to security jobs, real estate leads, client communications, and job applications. Archives spam/irrelevant messages and potentially drafts simple replies for approval._

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
3. Create GCP project -> Enable Gmail API -> Create OAuth2 credentials (Desktop App) -> Download JSON and set `GOOGLE_CLIENT_SECRETS_JSON` (defaults to `credentials.json`)
4. Set `NOTION_API_KEY` + relevant DB IDs
5. Set `SLACK_BOT_TOKEN`
6. `cp .env.example .env` -> Fill all keys
7. `uv run uvicorn src.inbox_cleaner.main:app --reload --port 8018`
8. `curl -X POST http://localhost:8018/sync/trigger`


## Setup with Notion
1. Go to https://www.notion.so/profile/integrations
2. Click + New integration
3. Select workspace, name it AI Inbox Cleaner, then create it
4. Open the integration details page
5. Click Show / Reveal under Internal Integration Token
6. Copy token and set in .env:

## Setup with Slack
1. Go to https://api.slack.com/apps
2. Click Create New App -> From scratch
3. App name: AI Inbox Cleaner (or similar), pick your workspace
4. In left menu, open **OAuth & Permissions**
5. Under **Bot Token Scopes**, click **Add an OAuth Scope** and add `chat:write`, `chat:write.public`
6. Scroll up, click **Install to Workspace**, and Allow
7. Copy the generated **Bot User OAuth Token** (starts with `xoxb-`)
8. In Slack, make sure the bot is invited to required channels like `#job-alerts`, `#newsletter-alerts`, and `#exceptions` (type `/invite @<Your_Bot_Name>`).
9. Set the token in `.env`: `SLACK_BOT_TOKEN="xoxb-..."`

## Setup with Gmail
1. Go to Google Cloud Console
2. Top navbar → choose your project (or create a new one)
3. APIs & Services → OAuth consent screen -> Configure consent screen (External)
4. Add the `https://www.googleapis.com/auth/gmail.modify` scope
5. Add your `@gmail.com` email to the Test users list and Save
6. APIs & Services → Credentials → Create Credentials → OAuth client ID
7. Application type: **Desktop app**, Name: "AI Inbox Cleaner"
8. Click Create and then Download JSON
9. Save the downloaded file as `credentials.json` in the root of the project (or set the `GOOGLE_CLIENT_SECRETS_JSON` env variable).

## Environment Variables

| Variable | Required | Description |
|----------|----------|-------------|
| `GROQ_API_KEY` | Yes | Groq API key |
| `GOOGLE_CLIENT_SECRETS_JSON` | No | Path to Google OAuth client secrets JSON (defaults to `credentials.json`) |
| `GMAIL_USER_EMAIL` | No | Gmail address to monitor (defaults to `me`) |
| `SLACK_BOT_TOKEN` | No | Slack bot token for alerts & error reporting (`xoxb-...`) |
