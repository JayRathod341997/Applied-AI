# Remote Job Ops Engine

## Overview

Scrapes remote job boards (We Work Remotely, Remote OK, Remotive), classifies roles using LLM, generates tailored resumes, and tracks applications.

## Setup

1. `cd remote_job_ops_engine && uv venv && uv sync`
2. `uv run playwright install chromium`
3. Set `GROQ_API_KEY`
4. Create Notion "Remote Jobs" database -> Set `NOTION_API_KEY` + `NOTION_REMOTE_JOBS_DB`
5. `cp .env.example .env` -> Fill all keys
6. `uv run uvicorn src.remote_job_ops.main:app --reload --port 8012`

## Test

```bash
curl -X POST http://localhost:8012/pipeline/run \
  -H "Content-Type: application/json" \
  -d '{"role_types":["VA"]}'
```
