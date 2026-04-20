# Smart Notion Sync Agent

## Overview

Central hub agent that provides bi-directional sync between Google Workspace (Calendar, Drive, Gmail) and Notion. Uses LLM-assisted conflict resolution when the same record is modified in both systems.

## Architecture

```
Google Calendar -+
Google Drive   --+
Gmail          --+--> Pipelines (LangGraph) --> Notion Command Center
Slack          --+      (conflict resolution,      (master DB)
                         change detection)
                               |
                               v
                         Health Dashboard
```

### Pipeline Structure

```
src/notion_sync/
â”œâ”€â”€ main.py                        # FastAPI app, routes, lifespan
â”œâ”€â”€ config.py                      # Settings via pydantic-settings
â”œâ”€â”€ models.py                      # Pydantic request/response models
â”œâ”€â”€ pipelines/
â”‚   â”œâ”€â”€ notion_sync.py             # Notion â†” Google Calendar sync (SyncEngine)
â”‚   â””â”€â”€ slack/
â”‚       â”œâ”€â”€ state.py               # SlackSyncState dataclass
â”‚       â”œâ”€â”€ nodes.py               # LangGraph node functions + routing
â”‚       â”œâ”€â”€ graphs.py              # Graph builders + compiled instances
â”‚       â””â”€â”€ __init__.py            # Public API: invoke_slack_to_notion, invoke_notion_to_slack
â”œâ”€â”€ tools/
â”‚   â”œâ”€â”€ notion_client.py           # Notion API wrapper
â”‚   â”œâ”€â”€ google_calendar.py         # Google Calendar API wrapper
â”‚   â””â”€â”€ slack_client.py            # Slack SDK wrapper
â””â”€â”€ utils/
    â”œâ”€â”€ logger.py
    â””â”€â”€ calendar_mapping.py        # Notion â†” GCal property translation
```

## Flow

1. Bi-directional sync between Google Workspace and Notion
2. Slack messages classified as tasks/notes -> Notion pages
3. Notion task changes polled and posted to Slack channel
4. Per-source polling or webhook receivers
5. Change detection via timestamps and content hashing
6. ChatGroq (llama-3.3-70b) resolves conflicts when same record modified in both systems
7. Batch sync with rate limiting and retry (exponential backoff)
8. Health dashboard shows sync status, error rates, data freshness

## Key Functionality

- **Bi-directional sync:** Notion <-> Google Calendar, Drive, Gmail
- **Slack sync:** Slack messages classified as tasks/notes -> Notion; Notion task changes -> Slack notifications
- **Conflict resolution:** LLM-assisted merge for conflicting edits
- **Change detection:** Timestamp + hash comparison
- **Error handling:** Retry with exponential backoff, dead letter queue
- **Health monitoring:** Per-integration status, last sync time, error count
- **Alerting:** Slack notification on sync failures

## Sample Input

```json
{
  "action": "full_sync",
  "sources": ["google_calendar", "google_drive", "gmail"],
  "direction": "bidirectional"
}
```

## Sample Output

```json
{
  "sync_results": {
    "google_calendar": {
      "status": "success",
      "records_synced": 12,
      "conflicts_resolved": 1,
      "direction": "notion->google",
      "last_sync": "2026-04-01T18:00:00Z"
    }
  },
  "health": {
    "all_systems_healthy": true,
    "uptime_hours": 720,
    "error_rate": 0.002,
    "next_sync": "2026-04-01T19:00:00Z"
  }
}
```

## Setup

1. `cd smart_notion_sync_agent`
2. `uv venv && uv sync`
3. Configure `.env` (see step-by-step below)
4. Run the API: `uv run uvicorn src.notion_sync.main:app --reload --port 8019`
5. Verify health: `curl http://localhost:8019/health`

## Running

Start the API server:
```bash
uv run uvicorn src.notion_sync.main:app --reload --port 8019
```

Run the initial sync script:
```bash
uv run scripts/initial_sync.py
```

Verify health:
```bash
curl http://localhost:8019/health
```

## .env Setup (Step-by-step)

`config.py` loads `.env` automatically from the project root, so you only need to create and fill that file.

1. Copy the template:
   - macOS/Linux: `cp .env.example .env`
   - PowerShell: `Copy-Item .env.example .env`
   - CMD: `copy .env.example .env`
2. Open `.env` and set required values:
   - `GROQ_API_KEY`
   - `NOTION_API_KEY`
   - `NOTION_TASKS_DB`, `NOTION_LEADS_DB`, `NOTION_JOBS_DB`, `NOTION_GRANTS_DB`, `NOTION_CALENDAR_DB`, `NOTION_FILES_DB`, `NOTION_NOTES_DB`
   - `GOOGLE_SERVICE_ACCOUNT_JSON` (absolute path recommended)
3. Optional Slack values (needed only for Slack features):
   - `SLACK_BOT_TOKEN`
   - `SLACK_SIGNING_SECRET`
   - `SLACK_SYNC_CHANNEL` (channel ID like `C0123456789`)
   - `SLACK_WEBHOOK_URL`
4. Save `.env` and start the app. The settings are loaded at startup.

## Slack Configuration

To get Slack credentials for the `.env` file:

### SLACK_BOT_TOKEN & SLACK_SIGNING_SECRET

1. Go to https://api.slack.com/apps
2. Click **Create New App** → Select "From scratch"
3. Name your app and pick a workspace
4. **Bot Token**: 
   - Go to **OAuth & Permissions**
   - Scroll to **Scopes** → add `chat:write`, `reactions:write`, `channels:read`
   - Click "Install to Workspace" at the top
   - Copy the **Bot User OAuth Token** (starts with `xoxb-`)
5. **Signing Secret**: 
   - Go to **Basic Information**
   - Scroll to **App Credentials** → Copy **Signing Secret**

### SLACK_SYNC_CHANNEL

1. In Slack, right-click your channel
2. Select **Copy link** → extract the channel ID (e.g., `C0123456789` from the URL)
3. Or right-click channel → **View channel details** → copy the ID at the bottom

### SLACK_WEBHOOK_URL

1. Go to **Incoming Webhooks** in your Slack app settings
2. Toggle "Activate Incoming Webhooks" to **On**
3. Click **Add New Webhook to Workspace**
4. Select the channel → Click **Allow**
5. Copy the webhook URL (starts with `https://hooks.slack.com/`)

### Verify Slack App

1. Open Slack → Apps → select your app.
2. The app's display name is shown there.
3. In a channel, type `@` and search your app name to confirm how it appears.
4. Alternatively, go to api.slack.com/apps → your app → App Home → check Display Name / Bot name.

---

## Notion Database Setup

### Notes Database Properties

The Notes database requires these properties:

| Property | Type |
|----------|------|
| `Name` | Title |
| `Tags` | Multi-select |
| `Source` | Rich text |

---

## Environment Variables

| Variable | Required | Description |
|----------|----------|-------------|
| `GROQ_API_KEY` | Yes | Groq API key |
| `GROQ_MODEL_PRIMARY` | No | LLM model name (default: `llama-3.3-70b-versatile`) |
| `NOTION_API_KEY` | Yes | Notion integration token |
| `NOTION_TASKS_DB` | Yes | Notion Tasks database ID |
| `NOTION_LEADS_DB` | Yes | Notion Leads database ID |
| `NOTION_JOBS_DB` | Yes | Notion Jobs database ID |
| `NOTION_GRANTS_DB` | Yes | Notion Grants database ID |
| `NOTION_CALENDAR_DB` | Yes | Notion Calendar database ID |
| `NOTION_FILES_DB` | Yes | Notion Files database ID |
| `NOTION_NOTES_DB` | Yes | Notion Notes database ID |
| `GOOGLE_SERVICE_ACCOUNT_JSON` | Yes | Path to Google service account JSON |
| `GOOGLE_CALENDAR_ID` | No | Target Google Calendar ID (default: `primary`) |
| `SLACK_BOT_TOKEN` | No | Slack bot token (`xoxb-...`) for posting/reactions |
| `SLACK_SIGNING_SECRET` | No | Slack signing secret for event verification |
| `SLACK_SYNC_CHANNEL` | No | Channel ID to post Notion updates |
| `SLACK_WEBHOOK_URL` | No | Slack webhook URL for alerts |
| `APP_ENV` | No | App environment (default: `development`) |
| `LOG_LEVEL` | No | Logging level (default: `INFO`) |

## Features

- Initial sync of Notion Calendar to Google Calendar
- Biâ€‘directional sync with LLMâ€‘assisted conflict resolution
- Hidden `Sync ID` property for tracking Google event IDs
- **Slack sync:** LLM classifies Slack messages as tasks/notes, creates Notion pages, polls Notion for task changes and posts to Slack
- Mapping utilities (`calendar_mapping.py`) for seamless data translation
- Detailed health monitoring and error reporting

## Initial Sync Instructions

1. Verify the hidden sync property name in `src/notion_sync/config.py` (default `Sync ID`).
2. Run the initial sync script to populate Google Calendar with existing Notion milestones and store the event IDs back in Notion:
   ```bash
   uv run scripts/initial_sync.py
   ```
   *If you prefer to trigger via the API, send a POST to `/sync/trigger` with `{ "action": "initial_sync" }`.*
3. After the script completes, check your Google Calendar for the newly created events and confirm that each Notion page now contains the `Sync ID` property populated with the corresponding Google event ID.
4. Subsequent runs of the regular sync will keep both systems in sync and resolve conflicts using the LLM.

## Share your Calendar with the Service Account
1. Open your Google Calendar.
2. On the left, find the calendar you want to sync to (usually your name), click the three dots â‹® next to it, and select Settings and sharing.
3. Scroll down to "Share with specific people or groups".
4. Click Add people and paste the Service Account email found in your credentials.json: service-acc@openclaw-bot-491510.iam.gserviceaccount.com
5. Set the permission to "Make changes to events".



## SLACK_BOT_TOKEN & SLACK_SIGNING_SECRET
1. Go to https://api.slack.com/apps
2. Click Create New App → Select "From scratch"
3. Name your app and pick a workspace
4. Bot Token: Go to OAuth & Permissions → scroll to Scopes → add chat:write, reactions:write, channels:read → Click "Install to Workspace" at top → Copy the Bot User OAuth Token (starts with xoxb-)
5. Signing Secret: Go to Basic Information → scroll to App 
Credentials → Copy Signing Secret


## SLACK_SYNC_CHANNEL
1. In Slack, right-click your channel → Copy link → extract the channel ID (e.g., C0123456789 from https://yourworkspace.slack.com/archives/C0123456789)
2. Or right-click channel → View channel details → copy the ID at the bottom


## SLACK_WEBHOOK_URL
1. Go to Incoming Webhooks in your app settings
2. Toggle "Activate Incoming Webhooks" to On
3. Click Add New Webhook to Workspace
4. Select the channel → Click Allow
5. Copy the webhook URL (starts with https://hooks.slack.com/)