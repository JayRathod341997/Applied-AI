# EP Job Application Agent

## Overview

Automated Executive Protection job scraper that searches multiple job boards, filters by rate and location, generates tailored cover letters, and tracks applications in Notion.

## Setup

1. `cd ep_job_application_agent && uv venv && uv sync`
2. `uv run playwright install chromium`
3. Set `GROQ_API_KEY`
4. Create Notion "EP Jobs" database -> Set `NOTION_API_KEY` + `NOTION_EP_JOBS_DB`
5. Set `SLACK_WEBHOOK_URL`
6. `cp .env.example .env` -> Fill all keys
7. `uv run uvicorn src.ep_job_app.main:app --reload --port 8011`

## Test

```bash
curl -X POST http://localhost:8011/scrape-trigger \
  -H "Content-Type: application/json" \
  -d '{"min_rate_per_day":600,"location":"SF Bay Area","max_results":20}'
```
