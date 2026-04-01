# Real Estate CRM Assistant

## Overview

Automated real estate lead qualification and follow-up system. Receives leads via webhook, qualifies them using LLM analysis, and initiates multi-touch SMS + email drip campaigns.

## Architecture

```
Lead Webhook --> LLM Qualifier --> Follow-Up Engine --> Twilio SMS + SendGrid Email
                 (score/classify)   (APScheduler)       (automated sequences)
                                              |
                                              v
                                         Notion CRM (update)
```

## Setup

1. `cd real_estate_crm_agent && uv venv && uv sync`
2. Set `GROQ_API_KEY` from console.groq.com
3. Create Twilio account -> Set `TWILIO_ACCOUNT_SID`, `TWILIO_AUTH_TOKEN`, `TWILIO_PHONE_NUMBER`
4. Create SendGrid account -> Set `SENDGRID_API_KEY`
5. Create Notion "JMG Leads" database -> Set `NOTION_API_KEY` + `NOTION_LEADS_DB`
6. `cp .env.example .env` -> Fill all keys
7. `uv run uvicorn src.real_estate_crm.main:app --reload --port 8013`

## Test

```bash
curl -X POST http://localhost:8013/webhook/lead \
  -H "Content-Type: application/json" \
  -d '{"name":"Test Lead","email":"test@test.com","phone":"+14155551234","message":"Looking for a home"}'
```
