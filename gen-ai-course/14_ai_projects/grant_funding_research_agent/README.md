# Grant & Funding Research Agent

## Overview

Automated grant and funding opportunity research. Scrapes multiple sources (Grants.gov, SBA, veteran-focused directories), scores relevance using LLM, and tracks opportunities in Notion.

## Setup

1. `cd grant_funding_research_agent && uv venv && uv sync`
2. `uv run playwright install chromium`
3. Set `GROQ_API_KEY`
4. Create Notion "Grants" database -> Set `NOTION_API_KEY` + `NOTION_GRANTS_DB`
5. Set `SLACK_WEBHOOK_URL`
6. `cp .env.example .env` -> Fill all keys
7. `uv run uvicorn src.grant_research.main:app --reload --port 8016`

## Test

```bash
curl -X POST http://localhost:8016/research/run \
  -H "Content-Type: application/json" \
  -d '{"criteria":{"veteran_owned":true,"min_amount":5000}}'
```
