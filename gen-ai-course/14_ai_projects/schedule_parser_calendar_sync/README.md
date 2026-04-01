# Schedule Parser & Calendar Sync Agent

## Overview

Parses schedule screenshots using Google Cloud Vision OCR and LLM extraction, then syncs extracted shifts to Google Calendar with configurable reminders.

## Architecture

```
Screenshot (PNG/JPG) --> Google Vision OCR --> LLM Extraction --> Google Calendar API
                           (text)               (structured          (events +
                                                events JSON)         reminders)
```

## Flow

1. User uploads schedule screenshot via `POST /parse-schedule`
2. Image preprocessed (deskew, contrast enhance via Pillow)
3. Google Vision OCR extracts raw text
4. ChatGroq (llama-3.3-70b) parses OCR text into structured shift data
5. Validation agent (llama-3.1-8b) cross-checks for anomalies
6. Google Calendar API creates events with 30/60-min pre-shift reminders
7. Deduplication prevents duplicate entries

## Setup

1. `cd schedule_parser_calendar_sync && uv venv && uv sync`
2. Create GCP project -> Enable Vision API + Calendar API -> Download service account JSON -> Set `GOOGLE_APPLICATION_CREDENTIALS`
3. Set `GROQ_API_KEY` from console.groq.com
4. `cp .env.example .env` -> Fill all keys
5. `uv run uvicorn src.schedule_parser.main:app --reload --port 8010`
6. `curl -X POST http://localhost:8010/parse-schedule -F "file=@schedule.png"`

## Environment Variables

| Variable | Required | Description |
|----------|----------|-------------|
| `GROQ_API_KEY` | Yes | Groq API key |
| `GOOGLE_APPLICATION_CREDENTIALS` | Yes | Path to GCP service account JSON |
| `GOOGLE_CALENDAR_ID` | No | Calendar ID (default: primary) |
