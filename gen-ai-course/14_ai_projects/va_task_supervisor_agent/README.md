# VA Task Supervisor Agent

## Overview

Automated VA task assignment, monitoring, and performance reporting. Uses LLM to intelligently assign tasks based on VA skills and workload balance.

## Architecture

```
Notion DB (tasks) --> Task Monitor --> Assignment Agent --> Notification Engine --> Reporting
  (source of truth)    (poll/webhook)   (LLM prioritize)    (Slack/Email)         (daily/weekly)
```

## Setup

1. `cd va_task_supervisor_agent && uv venv && uv sync`
2. Set `GROQ_API_KEY` from console.groq.com
3. Create Notion databases (Tasks, VA Profiles) -> Set `NOTION_API_KEY`, `NOTION_TASKS_DB`, `NOTION_VA_PROFILES_DB`
4. Set `SLACK_WEBHOOK_URL` + `SLACK_BOT_TOKEN`
5. Set `SENDGRID_API_KEY`
6. `cp .env.example .env` -> Fill all keys
7. `uv run uvicorn src.va_supervisor.main:app --reload --port 8017`

## Test

```bash
curl -X POST http://localhost:8017/tasks/assign \
  -H "Content-Type: application/json" \
  -d '{"task":{"title":"Follow up with leads","priority":"high","skills_required":["crm"],"estimated_hours":2}}'
```
