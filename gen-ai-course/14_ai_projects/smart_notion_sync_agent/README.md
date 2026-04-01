# Smart Notion Sync Agent

## Overview

Central hub agent that provides bi-directional sync between Google Workspace (Calendar, Drive, Gmail) and Notion. Uses LLM-assisted conflict resolution when the same record is modified in both systems.

## Architecture

```
Google Calendar -+
Google Drive   --+
Google          --+--> Sync Engine (LangGraph) --> Notion Command Center
Agent 1-9 Logs --+      (conflict resolution,        (master DB)
Slack          -+       change detection)
                              |
                              v
                        Health Dashboard
```

## Flow

1. Bi-directional sync between Google Workspace and Notion
2. Per-source polling or webhook receivers
3. Change detection via timestamps and content hashing
4. ChatGroq (llama-3.3-70b) resolves conflicts when same record modified in both systems
5. Batch sync with rate limiting and retry (exponential backoff)
6. Health dashboard shows sync status, error rates, data freshness

## Key Functionality

- **Bi-directional sync:** Notion <-> Google Calendar, Drive, Gmail
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

1. `cd smart_notion_sync_agent && uv venv && uv sync`
2. Set `GROQ_API_KEY` from console.groq.com
3. Create Notion master databases (Tasks, Leads, Jobs, Grants, Calendar, Files) -> Set `NOTION_API_KEY` + all DB IDs
4. Create GCP project -> Enable Calendar, Drive, Gmail APIs -> Create OAuth2 credentials -> Set `GOOGLE_SERVICE_ACCOUNT_JSON`
5. Set `SLACK_WEBHOOK_URL`
6. `cp .env.example .env` -> Fill all keys
7. `uv run uvicorn src.notion_sync.main:app --reload --port 8019`
8. `curl http://localhost:8019/health`
9. Deploy: `az acr build` -> `az containerapp create`

## Environment Variables

| Variable | Required | Description |
|----------|----------|-------------|
| `GROQ_API_KEY` | Yes | Groq API key |
| `NOTION_API_KEY` | Yes | Notion integration token |
| `NOTION_*_DB` | Yes | Notion database IDs |
| `GOOGLE_SERVICE_ACCOUNT_JSON` | Yes | Path to Google service account JSON |
| `SLACK_WEBHOOK_URL` | No | Slack webhook for alerts |
