# 10 Operational AI Agents — Master Implementation Plan

## Overview

This plan covers the design, development, and deployment of 10 standalone AI agent projects under `gen-ai-course/14_ai_projects/`. Each agent follows the established Azure Container Apps pattern (FastAPI + LangChain/LangGraph) with **Groq** for LLM inference and real API integrations for external services.

---

## Architecture Standards (All Agents)

### Shared Stack

| Layer | Technology |
|-------|-----------|
| **LLM Inference** | Groq (`langchain-groq` → `ChatGroq`) |
| **Primary Model** | `llama-3.3-70b-versatile` (~280 tps, $0.59/M input) |
| **Fast/Cheap Model** | `llama-3.1-8b-instant` (~560 tps, $0.05/M input) |
| **High-Quality Model** | `openai/gpt-oss-120b` (~500 tps, $0.15/M input) |
| **Embeddings** | `sentence-transformers` (local, free) |
| **Orchestration** | LangChain or LangGraph |
| **API** | FastAPI (async) |
| **Deployment** | Azure Container Apps |
| **Config** | pydantic-settings + `.env` |
| **Package Manager** | UV |
| **IaC** | Bicep templates |

### Groq LangChain Integration Pattern

```python
from langchain_groq import ChatGroq

# Primary agent (best quality/cost balance)
llm = ChatGroq(model_name="llama-3.3-70b-versatile", temperature=0.3)

# Fast classification/filtering
llm_fast = ChatGroq(model_name="llama-3.1-8b-instant", temperature=0)

# High-quality content generation
llm_quality = ChatGroq(model_name="openai/gpt-oss-120b", temperature=0.5)
```

### Embeddings Strategy

Since Groq does not offer embedding models, use one of:
1. **`sentence-transformers`** (local, free, no API needed) — `all-MiniLM-L6-v2` or `all-mpnet-base-v2`
2. **OpenAI Embeddings API** (if Azure OpenAI is still available for embeddings only)

### Standard Project Structure (Per Agent)

```
<agent_name>/
├── .env.example
├── .gitignore
├── pyproject.toml
├── README.md          # Detailed: arch, flow, functionality, sample I/O, setup
├── INTERVIEW.md
├── infra/
│   └── main.bicep
├── src/
│   └── <module>/
│       ├── __init__.py
│       ├── main.py         # FastAPI app
│       ├── config.py       # pydantic-settings (Groq config)
│       ├── agents/
│       ├── tools/
│       ├── pipelines/
│       └── utils/
│           ├── __init__.py
│           └── logger.py
└── tests/
```

---

## Agent 1: Schedule Parser & Calendar Sync Agent

**Folder:** `schedule_parser_calendar_sync/`
**Port:** 8010
**LLM:** `llama-3.3-70b-versatile` (extraction), `llama-3.1-8b-instant` (validation)

### Architecture

```
Screenshot (PNG/JPG) --> Google Vision OCR --> LLM Extraction --> Google Calendar API
                           (text)               (structured          (events +
                                                events JSON)         reminders)
```

### Flow

1. User uploads schedule screenshot via `POST /parse-schedule`
2. Image preprocessed (deskew, contrast enhance via Pillow)
3. Google Vision OCR extracts raw text
4. `ChatGroq` (llama-3.3-70b) parses OCR text into structured shift data
5. Validation agent (llama-3.1-8b) cross-checks for anomalies
6. Google Calendar API creates events with 30/60-min pre-shift reminders
7. Deduplication prevents duplicate entries

### Key Functionality

- **OCR preprocessing:** Auto-rotate, denoise, enhance contrast
- **Smart parsing:** Handles varied schedule formats (tables, lists, calendars)
- **Multi-shift support:** Day/night shifts, split shifts, on-call
- **Calendar sync:** Create/update/delete events, handle recurring shifts
- **Reminder system:** Configurable pre-shift reminders (15/30/60 min)

### Sample Input

```
POST /parse-schedule
Content-Type: multipart/form-data

file: [schedule_screenshot.png]
reminder_minutes: 30
calendar_id: primary
```

### Sample Output

```json
{
  "status": "success",
  "events_created": 5,
  "events": [
    {
      "title": "Security Shift - Main Gate",
      "date": "2026-04-02",
      "start_time": "06:00",
      "end_time": "14:00",
      "location": "Building A, Main Gate",
      "calendar_event_id": "abc123xyz",
      "reminder_set": "30 minutes before"
    },
    {
      "title": "Security Shift - Parking Lot",
      "date": "2026-04-03",
      "start_time": "14:00",
      "end_time": "22:00",
      "location": "Parking Structure B",
      "calendar_event_id": "def456uvw",
      "reminder_set": "30 minutes before"
    }
  ],
  "duplicates_skipped": 1,
  "ocr_confidence": 0.94,
  "processing_time_ms": 3200
}
```

### Setup Steps

1. **Clone & install:** `cd schedule_parser_calendar_sync && uv venv && uv sync`
2. **Google Cloud Vision:** Create GCP project -> Enable Vision API -> Download service account JSON -> Set `GOOGLE_APPLICATION_CREDENTIALS`
3. **Google Calendar:** Enable Calendar API -> Create OAuth2 credentials -> Set `GOOGLE_CALENDAR_ID`
4. **Groq API:** Get key from `console.groq.com` -> Set `GROQ_API_KEY`
5. **Configure:** `cp .env.example .env` -> Fill all keys
6. **Run:** `uv run uvicorn src.schedule_parser.main:app --reload --port 8010`
7. **Test:** `curl -X POST http://localhost:8010/parse-schedule -F "file=@schedule.png"`
8. **Deploy:** `az acr build` -> `az containerapp create`

### Dependencies

```
langchain-groq>=0.1.0
langchain-core>=0.2.0
google-cloud-vision>=3.5.0
google-api-python-client>=2.100.0
google-auth-oauthlib>=1.2.0
Pillow>=10.0.0
fastapi>=0.111.0
uvicorn[standard]>=0.29.0
pydantic>=2.7.0
pydantic-settings>=2.2.0
python-multipart>=0.0.9
```

### Azure Resources

- Azure Container Apps (hosting)
- Azure Blob Storage (temp image storage)

---

## Agent 2: Executive Protection (EP) Job Application Agent

**Folder:** `ep_job_application_agent/`
**Port:** 8011
**LLM:** `llama-3.3-70b-versatile` (cover letters), `llama-3.1-8b-instant` (filtering)

### Architecture

```
APScheduler --> Job Board Scraper --> LLM Filter --> Auto-Apply --> Notion/Slack
                 (Playwright)         (qualify)      (Playwright)    (track/notify)
```

### Flow

1. APScheduler triggers every 2-4 hours
2. Playwright scrapes target job boards (Indeed, LinkedIn, EP-specific sites)
3. `ChatGroq` (llama-3.1-8b) filters: rate >= $600/day, location = SF Bay Area
4. Relevance scoring (0-100) against EP skill profile
5. `ChatGroq` (llama-3.3-70b) generates tailored cover letter
6. Playwright auto-fills application forms
7. Results logged to Notion database, Slack notification sent

### Key Functionality

- **Multi-board scraping:** Indeed, LinkedIn, EP-specific job sites
- **Smart filtering:** Rate, location, skill match, clearance requirements
- **Auto-application:** Form filling, resume upload, cover letter submission
- **Deduplication:** Prevents re-applying to same positions
- **Status tracking:** Applied, interview, rejected, offered

### Sample Input

```json
{
  "trigger": "scheduled",
  "min_rate_per_day": 600,
  "location": "SF Bay Area",
  "max_results": 20
}
```

### Sample Output

```json
{
  "jobs_found": 47,
  "jobs_qualified": 8,
  "applications_submitted": 5,
  "applications": [
    {
      "title": "Executive Protection Agent",
      "company": "Allied Universal",
      "rate": "$750/day",
      "location": "San Francisco, CA",
      "status": "applied",
      "cover_letter_generated": true,
      "notion_page_id": "abc123",
      "applied_at": "2026-04-01T14:30:00Z"
    }
  ],
  "skipped_duplicates": 3,
  "errors": []
}
```

### Setup Steps

1. **Clone & install:** `cd ep_job_application_agent && uv venv && uv sync`
2. **Install browsers:** `uv run playwright install chromium`
3. **Groq API:** Set `GROQ_API_KEY`
4. **Notion:** Create integration at notion.so/my-integrations -> Create "EP Jobs" database -> Set `NOTION_API_KEY` + `NOTION_EP_JOBS_DB`
5. **Slack:** Create webhook at api.slack.com -> Set `SLACK_WEBHOOK_URL`
6. **Profile:** Create `data/profile.json` with resume details, skills, certifications
7. **Configure:** `cp .env.example .env` -> Fill all keys
8. **Run:** `uv run uvicorn src.ep_job_app.main:app --reload --port 8011`
9. **Test:** `curl -X POST http://localhost:8011/scrape-trigger`
10. **Deploy:** `az acr build` -> `az containerapp create`

### Dependencies

```
langchain-groq>=0.1.0
langgraph>=0.0.40
playwright>=1.40.0
notion-client>=2.2.0
slack_sdk>=3.30.0
apscheduler>=3.10.0
fastapi>=0.111.0
uvicorn[standard]>=0.29.0
pydantic>=2.7.0
pydantic-settings>=2.2.0
```

---

## Agent 3: Remote Job Ops Engine

**Folder:** `remote_job_ops_engine/`
**Port:** 8012
**LLM:** `llama-3.3-70b-versatile` (resume/cover letter), `llama-3.1-8b-instant` (classification)

### Architecture

```
Job Board Scrapers --> Role Classifier --> Resume Generator --> Auto-Apply --> Notion/Airtable
  (Playwright+BS4)       (LLM classify)    (LLM + PDF gen)     (Playwright)    (tracking)
```

### Flow

1. Playwright + BeautifulSoup scrape We Work Remotely, Remote OK, Remotive
2. `ChatGroq` (llama-3.1-8b) classifies: CSR, Admin, VA, Ops roles
3. Match score calculated against candidate profile
4. `ChatGroq` (llama-3.3-70b) customizes resume + generates cover letter
5. ReportLab generates PDF application packet
6. Playwright submits application
7. Sync to Notion/Airtable, generate weekly lead report

### Key Functionality

- **Multi-source scraping:** 4+ remote job boards with rate limiting
- **Role classification:** CSR, Admin, VA, Ops with confidence score
- **Resume tailoring:** Skills reordering, keyword optimization, summary customization
- **PDF generation:** Professional resume + cover letter PDF
- **Lead reports:** Weekly summary with conversion metrics

### Sample Input

```json
{
  "action": "run_pipeline",
  "role_types": ["CSR", "Admin", "VA"],
  "max_applications": 10,
  "generate_resume": true
}
```

### Sample Output

```json
{
  "listings_scraped": 124,
  "roles_classified": {"CSR": 18, "Admin": 12, "VA": 9, "Other": 85},
  "applications_submitted": 7,
  "applications": [
    {
      "title": "Virtual Assistant - Real Estate",
      "company": "Belay Solutions",
      "source": "We Work Remotely",
      "match_score": 92,
      "resume_generated": true,
      "resume_path": "output/resume_belay_20260401.pdf",
      "cover_letter_path": "output/cover_belay_20260401.pdf",
      "status": "submitted",
      "notion_page_id": "page_abc"
    }
  ],
  "weekly_report_generated": "output/weekly_report_2026_W14.pdf"
}
```

### Setup Steps

1. **Clone & install:** `cd remote_job_ops_engine && uv venv && uv sync`
2. **Install browsers:** `uv run playwright install chromium`
3. **Groq API:** Set `GROQ_API_KEY`
4. **Notion:** Create "Remote Jobs" database -> Set `NOTION_API_KEY` + `NOTION_REMOTE_JOBS_DB`
5. **Airtable (optional):** Create base -> Set `AIRTABLE_API_KEY` + `AIRTABLE_BASE_ID`
6. **Candidate profile:** Create `data/candidate_profile.json` with resume data, skills, experience
7. **Configure:** `cp .env.example .env`
8. **Run:** `uv run uvicorn src.remote_job_ops.main:app --reload --port 8012`
9. **Test:** `curl -X POST http://localhost:8012/pipeline/run -d '{"role_types": ["VA"]}'`
10. **Deploy:** `az acr build` -> `az containerapp create`

### Dependencies

```
langchain-groq>=0.1.0
langgraph>=0.0.40
playwright>=1.40.0
beautifulsoup4>=4.12.0
notion-client>=2.2.0
pyairtable>=2.2.0
reportlab>=4.1.0
weasyprint>=60.0
fastapi>=0.111.0
uvicorn[standard]>=0.29.0
pydantic>=2.7.0
pydantic-settings>=2.2.0
```

---

## Agent 4: Real Estate CRM Assistant

**Folder:** `real_estate_crm_agent/`
**Port:** 8013
**LLM:** `llama-3.3-70b-versatile` (qualification), `llama-3.1-8b-instant` (template selection)

### Architecture

```
Lead Webhook --> LLM Qualifier --> Follow-Up Engine --> Twilio SMS + SendGrid Email
                 (score/classify)   (APScheduler)       (automated sequences)
                                              |
                                              v
                                         Notion CRM (update)
```

### Flow

1. Lead received via `POST /webhook/lead` (form submission, Zillow feed, CSV import)
2. `ChatGroq` (llama-3.3-70b) qualifies: budget, timeline, intent, property type
3. Lead classified as hot/warm/cold
4. Follow-up sequence triggered via APScheduler:
   - Day 0: Welcome SMS (Twilio) + Email (SendGrid)
   - Day 1: Property match email
   - Day 3: Follow-up SMS
   - Day 7: Nurture email
5. Hot leads flagged in Notion CRM for sales team

### Key Functionality

- **Multi-source intake:** Webhook, CSV import, Zillow API feed
- **LLM qualification:** Budget analysis, timeline urgency, intent detection
- **Automated sequences:** 4-touch SMS + email drip campaign
- **Hot lead flagging:** Auto-notify sales team for high-value prospects
- **Activity logging:** Every touchpoint recorded in Notion

### Sample Input

```json
{
  "source": "website_form",
  "name": "Sarah Chen",
  "email": "sarah@example.com",
  "phone": "+14155551234",
  "message": "Looking for a 3BR home in Oakland, budget around $800K, pre-approved for mortgage, want to buy within 3 months",
  "property_interest": "Single Family",
  "budget_range": "$750K-$850K"
}
```

### Sample Output

```json
{
  "lead_id": "lead_20260401_001",
  "qualification": {
    "score": 92,
    "category": "hot",
    "reasoning": "Pre-approved mortgage, specific budget range, 3-month timeline, clear property criteria"
  },
  "follow_up_sequence": {
    "status": "initiated",
    "day_0_sms": "sent",
    "day_0_email": "sent",
    "next_touchpoint": "2026-04-02T10:00:00Z (property match email)"
  },
  "notion_page_id": "notion_xyz789",
  "sales_team_notified": true
}
```

### Setup Steps

1. **Clone & install:** `cd real_estate_crm_agent && uv venv && uv sync`
2. **Groq API:** Set `GROQ_API_KEY`
3. **Twilio:** Create account -> Get SID, Auth Token, Phone Number -> Set `TWILIO_ACCOUNT_SID`, `TWILIO_AUTH_TOKEN`, `TWILIO_PHONE_NUMBER`
4. **SendGrid:** Create account -> Generate API key -> Verify sender -> Set `SENDGRID_API_KEY`
5. **Notion:** Create "JMG Leads" database with fields (name, email, phone, score, category, status, last_contact) -> Set `NOTION_API_KEY` + `NOTION_LEADS_DB`
6. **Configure:** `cp .env.example .env`
7. **Run:** `uv run uvicorn src.real_estate_crm.main:app --reload --port 8013`
8. **Test:** `curl -X POST http://localhost:8013/webhook/lead -H "Content-Type: application/json" -d '{"name":"Test Lead","email":"test@test.com","phone":"+14155551234","message":"Looking for a home"}'`
9. **Deploy:** `az acr build` -> `az containerapp create`

### Dependencies

```
langchain-groq>=0.1.0
langchain-core>=0.2.0
twilio>=9.0.0
sendgrid>=6.11.0
notion-client>=2.2.0
apscheduler>=3.10.0
fastapi>=0.111.0
uvicorn[standard]>=0.29.0
pydantic>=2.7.0
pydantic-settings>=2.2.0
```

---

## Agent 5: Tactical Affiliate Funnel

**Folder:** `tactical_affiliate_funnel/`
**Port:** 8014
**LLM:** `openai/gpt-oss-120b` (high-quality copy), `llama-3.1-8b-instant` (variants)

### Architecture

```
Product Catalog --> Content Generator --> Landing Page Sync --> Performance Tracker
  (Notion/JSON)      (LLM per platform)    (Jinja2/Notion)      (UTM + clicks)
```

### Flow

1. Product catalog loaded from Notion DB or JSON (name, description, affiliate link, images)
2. `ChatGroq` (gpt-oss-120b) generates platform-specific captions (Instagram, X, Facebook)
3. Landing page content drafted and synced (via Notion or direct HTML)
4. Affiliate links injected with UTM tracking parameters
5. Click tracking via redirect endpoint, conversion logging
6. Daily/weekly performance metrics compiled

### Key Functionality

- **Multi-platform content:** Instagram, X/Twitter, Facebook, email copy
- **A/B variants:** Generate 3 caption variants per product per platform
- **Landing page sync:** Jinja2 templates or Notion-based content management
- **Click tracking:** UTM-parameterized redirect URLs with analytics
- **Revenue attribution:** Track which content drives conversions

### Sample Input

```json
{
  "action": "generate_content",
  "product": {
    "name": "Ranger Coffee - Tactical Roast",
    "description": "Veteran-owned small-batch coffee, dark roast, tactical packaging",
    "affiliate_link": "https://rangercoffee.com/ref/agent5",
    "target_audience": "Veterans, LEO, first responders",
    "price": "$18.99"
  },
  "platforms": ["instagram", "twitter", "facebook"],
  "variants_per_platform": 3
}
```

### Sample Output

```json
{
  "content_generated": 9,
  "products": [
    {
      "name": "Ranger Coffee - Tactical Roast",
      "platforms": {
        "instagram": [
          {"variant": "A", "caption": "Fuel your mission. Ranger Coffee -- veteran-owned, small-batch, built for those who serve. Link in bio.", "hashtags": "#veteranowned #tacticalcoffee #rangernation"},
          {"variant": "B", "caption": "Dark roast. Dark hours. Ranger Coffee keeps you locked in. Veteran-owned.", "hashtags": "#coffee #veteran #firstresponder"},
          {"variant": "C", "caption": "Every bag supports veteran-owned business. Ranger Coffee -- taste the mission.", "hashtags": "#supportvets #tacticalgear #coffee"}
        ],
        "twitter": [],
        "facebook": []
      },
      "tracking_url": "https://yourdomain.com/go/ranger-coffee?utm_source=instagram&utm_campaign=spring2026",
      "landing_page_updated": true
    }
  ]
}
```

### Setup Steps

1. **Clone & install:** `cd tactical_affiliate_funnel && uv venv && uv sync`
2. **Groq API:** Set `GROQ_API_KEY`
3. **Notion:** Create "Products" database (name, description, affiliate_link, images, target_audience) -> Set `NOTION_API_KEY` + `NOTION_PRODUCTS_DB`
4. **Domain (optional):** Set up redirect tracking domain -> Set `TRACKING_DOMAIN`
5. **Configure:** `cp .env.example .env`
6. **Run:** `uv run uvicorn src.tactical_funnel.main:app --reload --port 8014`
7. **Test:** `curl -X POST http://localhost:8014/generate-content -H "Content-Type: application/json" -d '{"product":{"name":"Test Knife","affiliate_link":"https://example.com/ref/test"},"platforms":["instagram"]}'`
8. **Deploy:** `az acr build` -> `az containerapp create`

### Dependencies

```
langchain-groq>=0.1.0
langchain-core>=0.2.0
notion-client>=2.2.0
httpx>=0.27.0
fastapi>=0.111.0
uvicorn[standard]>=0.29.0
pydantic>=2.7.0
pydantic-settings>=2.2.0
jinja2>=3.1.0
```

---

## Agent 6: Timesheet Compliance & Reporting

**Folder:** `timesheet_compliance_agent/`
**Port:** 8015
**LLM:** `llama-3.3-70b-versatile` (reconciliation), `llama-3.1-8b-instant` (validation)

### Architecture

```
Data Sources --> Validation Agent --> Report Generator --> Distribution
(API/CSV/OCR)     (cross-check)        (PDF weekly)        (Email/Notion)
```

### Flow

1. Ingest timesheet data from: platform APIs, CSV/Excel uploads, screenshot OCR
2. `ChatGroq` (llama-3.3-70b) reconciles across platforms, detects discrepancies
3. Pay rate verification, overtime calculation, compliance checks
4. WeasyPrint generates weekly PDF reports (per-employer breakdown)
5. Email distribution via SendGrid, log to Notion, store in Blob Storage

### Key Functionality

- **Multi-source ingestion:** APIs, CSV, Excel, OCR screenshots
- **Cross-platform reconciliation:** Match hours across employer systems
- **Discrepancy detection:** Flag mismatches in hours, rates, dates
- **PDF reports:** Professional weekly summaries with breakdowns
- **Compliance tracking:** Overtime flags, rate verification

### Sample Input

```json
{
  "action": "generate_weekly_report",
  "week_ending": "2026-03-29",
  "employee_id": "JR-001",
  "data_sources": [
    {"type": "csv", "path": "data/timesheets/employer_a_week14.csv"},
    {"type": "api", "platform": "shiftboard"},
    {"type": "ocr", "image_path": "data/screenshots/employer_b_schedule.png"}
  ]
}
```

### Sample Output

```json
{
  "report_generated": "output/weekly_report_2026_W14_JR001.pdf",
  "summary": {
    "total_hours": 52.5,
    "total_earnings": 2887.50,
    "employers": [
      {"name": "Securitas", "hours": 40, "rate": "$55/hr", "earnings": 2200.00},
      {"name": "Allied Universal", "hours": 12.5, "rate": "$55/hr", "earnings": 687.50}
    ],
    "overtime_hours": 12.5,
    "discrepancies_found": 1,
    "discrepancies": [
      {"employer": "Allied Universal", "issue": "Reported 14hrs but platform shows 12.5hrs", "severity": "warning"}
    ]
  },
  "distribution": {
    "email_sent": true,
    "notion_page_id": "timesheet_page_abc",
    "blob_stored": "timesheets/2026/W14_JR001.pdf"
  }
}
```

### Setup Steps

1. **Clone & install:** `cd timesheet_compliance_agent && uv venv && uv sync`
2. **Groq API:** Set `GROQ_API_KEY`
3. **Google Vision (optional OCR):** Set `GOOGLE_APPLICATION_CREDENTIALS`
4. **SendGrid:** Set `SENDGRID_API_KEY`
5. **Notion:** Create "Timesheets" database -> Set `NOTION_API_KEY` + `NOTION_TIMESHEETS_DB`
6. **Configure:** `cp .env.example .env`
7. **Run:** `uv run uvicorn src.timesheet_compliance.main:app --reload --port 8015`
8. **Test:** `curl -X POST http://localhost:8015/reports/generate -H "Content-Type: application/json" -d '{"week_ending":"2026-03-29","employee_id":"JR-001"}'`
9. **Deploy:** `az acr build` -> `az containerapp create`

### Dependencies

```
langchain-groq>=0.1.0
langchain-core>=0.2.0
google-cloud-vision>=3.5.0
weasyprint>=60.0
reportlab>=4.1.0
openpyxl>=3.1.0
sendgrid>=6.11.0
notion-client>=2.2.0
fastapi>=0.111.0
uvicorn[standard]>=0.29.0
pydantic>=2.7.0
pydantic-settings>=2.2.0
```

---

## Agent 7: Grant & Funding Research

**Folder:** `grant_funding_research_agent/`
**Port:** 8016
**LLM:** `llama-3.3-70b-versatile` (summarization), `llama-3.1-8b-instant` (filtering)

### Architecture

```
APScheduler --> Grant Scrapers --> Relevance Filter --> Summarizer --> Notion + Slack
  (daily)        (multi-source)     (LLM score)        (LLM extract)   (notify)
```

### Flow

1. APScheduler triggers daily/weekly crawl
2. Scrapers hit Grants.gov API, SBA.gov, veteran-focused directories
3. `ChatGroq` (llama-3.1-8b) scores relevance (veteran-owned, small business, industry)
4. `ChatGroq` (llama-3.3-70b) extracts: eligibility, deadline, amount, application URL
5. Dedup against previously seen grants
6. Push to Notion grants database, Slack alert for high-value opportunities

### Key Functionality

- **Multi-source scraping:** Grants.gov, SBA, state programs, private foundations
- **Relevance scoring:** Veteran status, business size, industry match
- **Detail extraction:** Eligibility, deadline, amount, contacts
- **Deduplication:** Hash-based comparison with historical grants
- **Alerting:** Slack notifications for grants > $10K

### Sample Input

```json
{
  "action": "run_research",
  "criteria": {
    "veteran_owned": true,
    "business_type": "small_business",
    "industry": ["security", "real_estate", "technology"],
    "min_amount": 5000
  }
}
```

### Sample Output

```json
{
  "grants_found": 23,
  "grants_relevant": 7,
  "grants_new": 4,
  "grants": [
    {
      "title": "SBA Veteran-Owned Business Grant 2026",
      "source": "SBA.gov",
      "amount": "$25,000",
      "deadline": "2026-06-15",
      "eligibility": "Veteran-owned small business, 2+ years in operation, under 500 employees",
      "application_url": "https://sba.gov/grants/veteran-2026",
      "relevance_score": 95,
      "notion_page_id": "grant_page_xyz",
      "slack_notified": true
    }
  ],
  "duplicates_skipped": 3
}
```

### Setup Steps

1. **Clone & install:** `cd grant_funding_research_agent && uv venv && uv sync`
2. **Install browsers:** `uv run playwright install chromium`
3. **Groq API:** Set `GROQ_API_KEY`
4. **Notion:** Create "Grants" database -> Set `NOTION_API_KEY` + `NOTION_GRANTS_DB`
5. **Slack:** Set `SLACK_WEBHOOK_URL`
6. **Configure:** `cp .env.example .env`
7. **Run:** `uv run uvicorn src.grant_research.main:app --reload --port 8016`
8. **Test:** `curl -X POST http://localhost:8016/research/run -H "Content-Type: application/json" -d '{"criteria":{"veteran_owned":true}}'`
9. **Deploy:** `az acr build` -> `az containerapp create`

### Dependencies

```
langchain-groq>=0.1.0
langgraph>=0.0.40
playwright>=1.40.0
beautifulsoup4>=4.12.0
httpx>=0.27.0
notion-client>=2.2.0
slack_sdk>=3.30.0
apscheduler>=3.10.0
fastapi>=0.111.0
uvicorn[standard]>=0.29.0
pydantic>=2.7.0
pydantic-settings>=2.2.0
```

---

## Agent 8: VA Task Supervisor

**Folder:** `va_task_supervisor_agent/`
**Port:** 8017
**LLM:** `llama-3.3-70b-versatile` (assignment logic), `llama-3.1-8b-instant` (summaries)

### Architecture

```
Notion DB (tasks) --> Task Monitor --> Assignment Agent --> Notification Engine --> Reporting
  (source of truth)    (poll/webhook)   (LLM prioritize)    (Slack/Email)         (daily/weekly)
```

### Flow

1. Poll Notion task database (or receive webhook on changes)
2. Detect new tasks, overdue items, status changes
3. `ChatGroq` (llama-3.3-70b) suggests assignment based on VA skills + workload
4. Slack DM reminders for overdue/due-soon tasks
5. Daily progress digest via email
6. Weekly completion report with VA performance metrics

### Key Functionality

- **Smart assignment:** LLM balances workload across VAs based on skills
- **Automated reminders:** Overdue alerts, due-soon warnings
- **Progress tracking:** Completion rates, average turnaround time
- **Daily digest:** Email summary of today's tasks + yesterday's completions
- **Weekly report:** VA performance metrics, bottleneck identification

### Sample Input

```json
{
  "action": "assign_task",
  "task": {
    "title": "Follow up with 5 real estate leads",
    "priority": "high",
    "due_date": "2026-04-02",
    "skills_required": ["crm", "communication", "real_estate"],
    "estimated_hours": 2
  }
}
```

### Sample Output

```json
{
  "assignment": {
    "task_id": "task_abc123",
    "assigned_to": "Maria (VA-02)",
    "reasoning": "Maria has CRM experience, current workload is 6hrs (lowest), real estate background",
    "current_workload": {"Maria": 6, "James": 12, "Priya": 9}
  },
  "notifications": {
    "slack_dm_sent": true,
    "notion_assigned": true
  },
  "daily_digest": {
    "tasks_due_today": 4,
    "tasks_overdue": 1,
    "tasks_completed_yesterday": 7
  }
}
```

### Setup Steps

1. **Clone & install:** `cd va_task_supervisor_agent && uv venv && uv sync`
2. **Groq API:** Set `GROQ_API_KEY`
3. **Notion:** Create "VA Tasks" database (title, assignee, due_date, status, priority, skills_required) + "VA Profiles" database (name, skills, current_workload) -> Set `NOTION_API_KEY`, `NOTION_TASKS_DB`, `NOTION_VA_PROFILES_DB`
4. **Slack:** Set `SLACK_WEBHOOK_URL` + `SLACK_BOT_TOKEN`
5. **SendGrid:** Set `SENDGRID_API_KEY`
6. **Configure:** `cp .env.example .env`
7. **Run:** `uv run uvicorn src.va_supervisor.main:app --reload --port 8017`
8. **Test:** `curl http://localhost:8017/tasks/overdue`
9. **Deploy:** `az acr build` -> `az containerapp create`

### Dependencies

```
langchain-groq>=0.1.0
langchain-core>=0.2.0
notion-client>=2.2.0
slack_sdk>=3.30.0
sendgrid>=6.11.0
apscheduler>=3.10.0
fastapi>=0.111.0
uvicorn[standard]>=0.29.0
pydantic>=2.7.0
pydantic-settings>=2.2.0
```

---

## Agent 9: AI Inbox Cleaner

**Folder:** `ai_inbox_cleaner/`
**Port:** 8018
**LLM:** `llama-3.1-8b-instant` (classification, fast), `llama-3.3-70b-versatile` (draft replies)

### Architecture

```
Gmail Poller --> Classification Agent --> Action Router --> Notification
  (Gmail API)     (LLM categorize)        (label/archive/    (Slack/Notion)
                                          draft/forward)
```

### Flow

1. Gmail API polls for new messages (or push notification via webhook)
2. `ChatGroq` (llama-3.1-8b) classifies each email into categories
3. Actions applied based on category:
   - **Security Job** -> Label "Jobs/Security", star, forward to Notion
   - **Real Estate Lead** -> Label "Leads/RE", forward to Notion CRM
   - **Client Communication** -> Label "Clients", star if urgent
   - **Job Application Response** -> Label "Applications", Slack alert
   - **Spam/Irrelevant** -> Archive
4. `ChatGroq` (llama-3.3-70b) drafts simple replies for approval
5. Urgent emails trigger Slack notifications

### Key Functionality

- **Smart categorization:** 6 email categories with confidence scores
- **Auto-labeling:** Gmail labels applied automatically
- **Spam cleanup:** Archive irrelevant messages
- **Reply drafting:** LLM generates reply drafts for approval
- **Lead forwarding:** Real estate leads auto-pushed to Notion CRM
- **Daily digest:** Summary of categorized emails

### Sample Input

```
Triggered by: Gmail push notification or APScheduler poll
New email: {
  "from": "hr@allieduniversal.com",
  "subject": "Interview Invitation - Executive Protection Agent",
  "body": "Dear Candidate, We are pleased to invite you for an interview..."
}
```

### Sample Output

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
    {"action": "notion_forward", "page_id": "app_page_xyz"},
    {"action": "draft_reply", "draft_id": "gmail_draft_789", "preview": "Thank you for the invitation. I am available for an interview on..."}
  ]
}
```

### Setup Steps

1. **Clone & install:** `cd ai_inbox_cleaner && uv venv && uv sync`
2. **Groq API:** Set `GROQ_API_KEY`
3. **Gmail API:** Create GCP project -> Enable Gmail API -> Create OAuth2 credentials -> Set `GOOGLE_SERVICE_ACCOUNT_JSON`, `GMAIL_USER_EMAIL`
4. **Notion:** Set `NOTION_API_KEY` + relevant DB IDs
5. **Slack:** Set `SLACK_WEBHOOK_URL`
6. **Configure:** `cp .env.example .env`
7. **Run:** `uv run uvicorn src.inbox_cleaner.main:app --reload --port 8018`
8. **Test:** `curl -X POST http://localhost:8018/sync/trigger`
9. **Deploy:** `az acr build` -> `az containerapp create`

### Dependencies

```
langchain-groq>=0.1.0
langgraph>=0.0.40
google-api-python-client>=2.100.0
google-auth-oauthlib>=1.2.0
notion-client>=2.2.0
slack_sdk>=3.30.0
apscheduler>=3.10.0
fastapi>=0.111.0
uvicorn[standard]>=0.29.0
pydantic>=2.7.0
pydantic-settings>=2.2.0
```

---

## Agent 10: Smart Notion Sync Agent (Central Hub)

**Folder:** `smart_notion_sync_agent/`
**Port:** 8019
**LLM:** `llama-3.3-70b-versatile` (conflict resolution)

### Architecture

```
Google Calendar -+
Google Drive   --+
Gmail          --+--> Sync Engine (LangGraph) --> Notion Command Center
Agent 1-9 Logs --+      (conflict resolution,        (master DB)
Slack          -+       change detection)
                              |
                              v
                        Health Dashboard
```

### Flow

1. Bi-directional sync between Google Workspace and Notion
2. Per-source polling or webhook receivers
3. Change detection via timestamps and content hashing
4. `ChatGroq` (llama-3.3-70b) resolves conflicts when same record modified in both systems
5. Batch sync with rate limiting and retry (exponential backoff)
6. Health dashboard shows sync status, error rates, data freshness

### Key Functionality

- **Bi-directional sync:** Notion <-> Google Calendar, Drive, Gmail
- **Conflict resolution:** LLM-assisted merge for conflicting edits
- **Change detection:** Timestamp + hash comparison
- **Error handling:** Retry with exponential backoff, dead letter queue
- **Health monitoring:** Per-integration status, last sync time, error count
- **Alerting:** Slack notification on sync failures

### Sample Input

```json
{
  "action": "full_sync",
  "sources": ["google_calendar", "google_drive", "gmail"],
  "direction": "bidirectional"
}
```

### Sample Output

```json
{
  "sync_results": {
    "google_calendar": {
      "status": "success",
      "records_synced": 12,
      "conflicts_resolved": 1,
      "direction": "notion->google",
      "last_sync": "2026-04-01T18:00:00Z"
    },
    "google_drive": {
      "status": "success",
      "files_synced": 8,
      "new_files": 2,
      "updated_files": 1,
      "last_sync": "2026-04-01T18:00:00Z"
    },
    "gmail": {
      "status": "success",
      "labels_synced": 156,
      "new_classified": 3,
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

### Setup Steps

1. **Clone & install:** `cd smart_notion_sync_agent && uv venv && uv sync`
2. **Groq API:** Set `GROQ_API_KEY`
3. **Notion:** Create master databases (Tasks, Leads, Jobs, Grants, Calendar, Files) -> Set `NOTION_API_KEY` + all DB IDs
4. **Google Workspace:** Create GCP project -> Enable Calendar, Drive, Gmail APIs -> Create OAuth2 credentials -> Set `GOOGLE_SERVICE_ACCOUNT_JSON`
5. **Slack:** Set `SLACK_WEBHOOK_URL`
6. **Configure:** `cp .env.example .env`
7. **Run:** `uv run uvicorn src.notion_sync.main:app --reload --port 8019`
8. **Test:** `curl http://localhost:8019/health` + `curl -X POST http://localhost:8019/sync/trigger`
9. **Deploy:** `az acr build` -> `az containerapp create`

### Dependencies

```
langchain-groq>=0.1.0
langgraph>=0.0.40
notion-client>=2.2.0
google-api-python-client>=2.100.0
google-auth-oauthlib>=1.2.0
slack_sdk>=3.30.0
apscheduler>=3.10.0
fastapi>=0.111.0
uvicorn[standard]>=0.29.0
pydantic>=2.7.0
pydantic-settings>=2.2.0
httpx>=0.27.0
```

---

## Shared Environment Variables Template

```env
# Groq LLM (all agents)
GROQ_API_KEY=gsk_xxxxxxxxxxxxxxxxxxxxxxxx
GROQ_MODEL_PRIMARY=llama-3.3-70b-versatile
GROQ_MODEL_FAST=llama-3.1-8b-instant
GROQ_MODEL_QUALITY=openai/gpt-oss-120b

# Notion (agents 2, 4, 5, 7, 8, 10)
NOTION_API_KEY=secret_xxxxxxxxxxxxxxxx
NOTION_TASKS_DB=
NOTION_LEADS_DB=
NOTION_GRANTS_DB=
NOTION_EP_JOBS_DB=
NOTION_REMOTE_JOBS_DB=
NOTION_PRODUCTS_DB=
NOTION_TIMESHEETS_DB=

# Google (agents 1, 9, 10)
GOOGLE_SERVICE_ACCOUNT_JSON=/path/to/service-account.json
GOOGLE_CALENDAR_ID=primary
GMAIL_USER_EMAIL=

# Twilio (agent 4)
TWILIO_ACCOUNT_SID=
TWILIO_AUTH_TOKEN=
TWILIO_PHONE_NUMBER=+1XXXXXXXXXX

# SendGrid (agents 4, 6, 8)
SENDGRID_API_KEY=

# Slack (agents 2, 7, 8, 9, 10)
SLACK_WEBHOOK_URL=https://hooks.slack.com/services/xxx/yyy/zzz
SLACK_BOT_TOKEN=xoxb-xxxxxxxxxxxx

# Airtable (agent 3)
AIRTABLE_API_KEY=
AIRTABLE_BASE_ID=

# Application (all agents)
APP_ENV=development
LOG_LEVEL=INFO
```

---

## Shared pyproject.toml Template (Groq-based)

```toml
[project]
name = "<agent-name>"
version = "0.1.0"
description = "<description>"
readme = "README.md"
requires-python = ">=3.11"

dependencies = [
    "langchain-groq>=0.1.0",
    "langchain-core>=0.2.0",
    "langgraph>=0.0.40",
    "fastapi>=0.111.0",
    "uvicorn[standard]>=0.29.0",
    "pydantic>=2.7.0",
    "pydantic-settings>=2.2.0",
    "python-dotenv>=1.0.0",
    "httpx>=0.27.0",
    # Agent-specific deps here
]

[project.optional-dependencies]
dev = [
    "pytest>=8.2.0",
    "pytest-asyncio>=0.23.0",
    "ruff>=0.4.0",
]

[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[tool.hatch.build.targets.wheel]
packages = ["src/<module>"]

[tool.hatch.build.targets.sdist]
include = ["/src"]
```

---

## Implementation Order

| Phase | Weeks | Agents | Rationale |
|-------|-------|--------|-----------|
| **1: Foundation** | 1-2 | #10 Notion Sync, #9 Inbox Cleaner | Central hub + email infra |
| **2: Core Business** | 3-5 | #1 Schedule Parser, #4 Real Estate CRM, #8 VA Supervisor | Revenue-generating workflows |
| **3: Job & Research** | 6-8 | #2 EP Jobs, #3 Remote Jobs, #7 Grants | Scraping-heavy, parallel dev |
| **4: Supporting** | 9-10 | #5 Affiliate Funnel, #6 Timesheet | Content/reporting agents |

---

## Per-Agent Deliverables Checklist

Each agent project must include:

- [ ] `README.md` -- Architecture diagram, flow, key functionality, sample I/O, setup steps
- [ ] `INTERVIEW.md` -- 5-10 technical Q&A about the agent
- [ ] `pyproject.toml` -- UV project config with all dependencies
- [ ] `.env.example` -- All required env vars with descriptions
- [ ] `.gitignore` -- Python, .env, .venv, __pycache__
- [ ] `src/<module>/main.py` -- FastAPI app with health check
- [ ] `src/<module>/config.py` -- pydantic-settings config (Groq)
- [ ] `src/<module>/agents/` -- Agent logic modules
- [ ] `src/<module>/tools/` -- External service wrappers
- [ ] `infra/main.bicep` -- Azure Bicep IaC
- [ ] `tests/` -- Unit tests with mocks
- [ ] Runnable via `uv run uvicorn src.<module>.main:app --reload --port <port>`
