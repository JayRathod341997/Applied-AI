# GenAI Project Case Studies Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Produce 11 interview-ready GenAI project case studies plus an index, in a central folder, grounded in each project's source code.

**Architecture:** One markdown file per project under `course-content/project-case-studies/`, each following a fixed 12-section template (the user's 10 headings reframed for GenAI, plus a 30-second pitch and follow-up questions). An index `README.md` links them and groups by archetype; the senior interview guide links to the folder. Numbers not derivable from code are written as defensible values explicitly labeled illustrative.

**Tech Stack:** Markdown only. No application code changes. Source of truth = each project's `README.md` + `src/**` (`models.py`, `agents/`, `pipelines/`, `tools/`, `config.py`, `main.py`).

---

## Reference: the 12-section template

Every case-study file MUST contain these sections, in this order, as `##` headings (the 30-second pitch is the lead paragraph under the title; follow-ups close the file):

```markdown
# <Project Title> — Case Study

**30-second pitch:** <2-3 sentence elevator version of the whole story.>

## 1. Problem statement
## 2. Why AI/ML was needed
## 3. Dataset → Knowledge corpus & eval set
## 4. Feature engineering → Prompt & context engineering
## 5. Model selection rationale
## 6. Training process → Prompt iteration / fine-tuning (or why not)
## 7. Evaluation metrics
## 8. Deployment architecture
## 9. Business impact
## 10. Lessons learned

## Likely follow-up questions
```

**Content rules (apply to every file):**
- Architecture, models, tools, pipelines, and flow MUST come from the project's actual source. Name the real LLMs, embedding models, rerankers, and integrations the code uses.
- Any number not derivable from code (corpus size, latency, cost, accuracy, F1, business impact) MUST be written as a representative value and explicitly tagged, e.g. `*Illustrative:* ~5k docs, p95 ~1.8s, ~$0.004/query`.
- Never present an illustrative number as a measured/benchmarked result.
- "Likely follow-up questions" = 5–8 probing interviewer questions, each with a one-line answer pointer.
- Depth scales with code: RAG and multi-agent projects get richer sections 4–8 than thin automation agents.

**Project → output-file map (kebab-case of folder name, numbered for ordering):**

| # | Project folder | Output file | Archetype |
|---|----------------|-------------|-----------|
| 01 | `ai_inbox_cleaner` | `01-ai-inbox-cleaner.md` | Automation agent |
| 02 | `book_recommender` | `02-book-recommender.md` | RAG |
| 03 | `customer_support_engine` | `03-customer-support-engine.md` | RAG |
| 04 | `multi_agent_researcher` | `04-multi-agent-researcher.md` | Multi-agent |
| 05 | `market_intelligence_agent` | `05-market-intelligence-agent.md` | Multi-agent |
| 06 | `smart_notion_sync_agent` | `06-smart-notion-sync-agent.md` | Automation agent |
| 07 | `schedule_parser_calendar_sync` | `07-schedule-parser-calendar-sync.md` | Automation agent (OCR) |
| 08 | `real_estate_crm_agent` | `08-real-estate-crm-agent.md` | Automation agent |
| 09 | `va_task_supervisor_agent` | `09-va-task-supervisor-agent.md` | Automation agent |
| 10 | `ep_job_application_agent` | `10-ep-job-application-agent.md` | Automation agent |
| 11 | `grant_funding_research_agent` | `11-grant-funding-research-agent.md` | Research agent |

> Confirm the archetype against the source while writing; adjust the index grouping if the code disagrees.

---

## Task 0: Create folder and verify project paths

**Files:**
- Create: `course-content/project-case-studies/.gitkeep` (temporary; removed once real files exist)

- [ ] **Step 1: Confirm all 11 project folders exist**

Run:
```bash
ls -1 "gen-ai-course/14_ai_projects"
```
Expected: output includes all 11 folder names from the map above.

- [ ] **Step 2: Create the output folder**

Run:
```bash
mkdir -p "course-content/project-case-studies"
```
Expected: no error.

No commit yet (folder is empty; first case-study commit will include it).

---

## Tasks 1–11: Write one case study per project

Each task has the SAME shape. Do them one at a time. The per-project source files to read and the output file differ per task; everything else is identical.

> The four "Step" pattern per task: (1) read the project's source, (2) write the file from the template, (3) verify all sections are present and claims trace to source, (4) commit.

### Task 1: `ai_inbox_cleaner` → `01-ai-inbox-cleaner.md`

**Files:**
- Read: `gen-ai-course/14_ai_projects/ai_inbox_cleaner/README.md`, `gen-ai-course/14_ai_projects/ai_inbox_cleaner/src/inbox_cleaner/models.py`, `.../agents/`, `.../pipelines/email_pipeline.py`, `.../main.py`, `.../tools/`
- Create: `course-content/project-case-studies/01-ai-inbox-cleaner.md`

- [ ] **Step 1: Read the source.** Read the files above. Note the real LLMs (e.g. Groq llama-3.1-8b for classify, llama-3.3-70b for drafting), the 6 email categories, the action router, and the Slack/Notion integrations.

- [ ] **Step 2: Write the file** using the 12-section template. Ground sections 4/5/8 in the actual classification prompt, model split, and Gmail→classify→route→notify flow. Label all numbers illustrative.

- [ ] **Step 3: Verify structure.** Run:
```bash
grep -E "^(# |## )" "course-content/project-case-studies/01-ai-inbox-cleaner.md"
```
Expected: the title plus all 11 `##` headings from the template, in order. Also confirm at least one `*Illustrative:*` tag exists and the named models match the source.

- [ ] **Step 4: Commit.**
```bash
git add "course-content/project-case-studies/01-ai-inbox-cleaner.md"
git commit -m "docs(case-studies): add ai_inbox_cleaner case study"
```

### Task 2: `book_recommender` → `02-book-recommender.md`

**Files:**
- Read: `gen-ai-course/14_ai_projects/book_recommender/README.md`, `src/recommender/ingestion/chunker.py`, `.../ingestion/embedder.py`, `.../ingestion/indexer.py`, `.../retrieval/search.py`, `.../retrieval/reranker.py`, `.../recommendation/pipeline.py`, `.../config.py`, `.../models.py`
- Create: `course-content/project-case-studies/02-book-recommender.md`

- [ ] **Step 1: Read the source.** Note embedding model, vector store, chunking strategy, the reranker, and the recommendation pipeline. This is a RAG project — give sections 3/4/5/7 extra depth (corpus, chunking, embeddings+reranker, retrieval metrics like hit-rate/MRR/nDCG).

- [ ] **Step 2: Write the file** from the template, grounded in the ingestion→retrieval→rerank→recommend pipeline. Label numbers illustrative.

- [ ] **Step 3: Verify structure.** Run:
```bash
grep -E "^(# |## )" "course-content/project-case-studies/02-book-recommender.md"
```
Expected: title + all 11 `##` headings. Confirm reranker and embedding model named match source; confirm retrieval metrics appear in section 7.

- [ ] **Step 4: Commit.**
```bash
git add "course-content/project-case-studies/02-book-recommender.md"
git commit -m "docs(case-studies): add book_recommender case study"
```

### Task 3: `customer_support_engine` → `03-customer-support-engine.md`

**Files:**
- Read: `gen-ai-course/14_ai_projects/customer_support_engine/README.md`, and the backend source under `gen-ai-course/14_ai_projects/customer_support_engine/backend/` (retrieval, pipeline, models, config — read the actual `src`/app modules present, excluding `.venv`)
- Create: `course-content/project-case-studies/03-customer-support-engine.md`

- [ ] **Step 1: Read the source.** Identify the RAG retrieval stack, LLM, grounding/citation approach, and API surface. RAG project — depth on sections 4/7/8 (context assembly, faithfulness/groundedness metrics, serving architecture).

- [ ] **Step 2: Write the file** from the template, grounded in source. Label numbers illustrative.

- [ ] **Step 3: Verify structure.** Run:
```bash
grep -E "^(# |## )" "course-content/project-case-studies/03-customer-support-engine.md"
```
Expected: title + all 11 `##` headings. Confirm faithfulness/groundedness metric appears in section 7.

- [ ] **Step 4: Commit.**
```bash
git add "course-content/project-case-studies/03-customer-support-engine.md"
git commit -m "docs(case-studies): add customer_support_engine case study"
```

### Task 4: `multi_agent_researcher` → `04-multi-agent-researcher.md`

**Files:**
- Read: `gen-ai-course/14_ai_projects/multi_agent_researcher/README.md`, `src/researcher/crew/agents.py`, `.../crew/tasks.py`, `.../crew/crew_builder.py`, `.../tools/`, `.../config.py`, `.../main.py`
- Create: `course-content/project-case-studies/04-multi-agent-researcher.md`

- [ ] **Step 1: Read the source.** Note the framework (CrewAI), the agent roles, task graph, tools (web/search/memory), and LLM. Multi-agent — depth on sections 4/5/8 (agent decomposition, orchestration, why multi-agent vs single).

- [ ] **Step 2: Write the file** from the template, grounded in the crew/agents/tasks structure. Label numbers illustrative.

- [ ] **Step 3: Verify structure.** Run:
```bash
grep -E "^(# |## )" "course-content/project-case-studies/04-multi-agent-researcher.md"
```
Expected: title + all 11 `##` headings. Confirm the orchestration framework and agent roles named match source.

- [ ] **Step 4: Commit.**
```bash
git add "course-content/project-case-studies/04-multi-agent-researcher.md"
git commit -m "docs(case-studies): add multi_agent_researcher case study"
```

### Task 5: `market_intelligence_agent` → `05-market-intelligence-agent.md`

**Files:**
- Read: `gen-ai-course/14_ai_projects/market_intelligence_agent/README.md`, `src/market_intel/agents/orchestrator.py`, `.../agents/retrieval_agent.py`, `.../agents/reasoning_agent.py`, `.../agents/validation_agent.py`, `.../pipelines/rag_chain.py`, `.../tools/`, `.../config.py`, `.../main.py`
- Create: `course-content/project-case-studies/05-market-intelligence-agent.md`

- [ ] **Step 1: Read the source.** Note the orchestrator + retrieval/reasoning/validation agents and the RAG chain. Multi-agent + RAG — depth on sections 4/7/8 (retrieval+validation loop, how validation guards hallucination, orchestration).

- [ ] **Step 2: Write the file** from the template, grounded in source. Label numbers illustrative.

- [ ] **Step 3: Verify structure.** Run:
```bash
grep -E "^(# |## )" "course-content/project-case-studies/05-market-intelligence-agent.md"
```
Expected: title + all 11 `##` headings. Confirm the validation-agent role appears in sections 4/7.

- [ ] **Step 4: Commit.**
```bash
git add "course-content/project-case-studies/05-market-intelligence-agent.md"
git commit -m "docs(case-studies): add market_intelligence_agent case study"
```

### Task 6: `smart_notion_sync_agent` → `06-smart-notion-sync-agent.md`

**Files:**
- Read: `gen-ai-course/14_ai_projects/smart_notion_sync_agent/README.md`, `src/notion_sync/agents/conflict_resolver.py`, `.../utils/`, and other modules present under `src/notion_sync/`
- Create: `course-content/project-case-studies/06-smart-notion-sync-agent.md`

- [ ] **Step 1: Read the source.** Note the sync flow and the LLM-based conflict resolution. Automation agent — keep sections 3/6 honest about no training; depth on section 4 (how conflicts are framed as a prompt) and section 8 (sync triggers).

- [ ] **Step 2: Write the file** from the template, grounded in source. Label numbers illustrative.

- [ ] **Step 3: Verify structure.** Run:
```bash
grep -E "^(# |## )" "course-content/project-case-studies/06-smart-notion-sync-agent.md"
```
Expected: title + all 11 `##` headings.

- [ ] **Step 4: Commit.**
```bash
git add "course-content/project-case-studies/06-smart-notion-sync-agent.md"
git commit -m "docs(case-studies): add smart_notion_sync_agent case study"
```

### Task 7: `schedule_parser_calendar_sync` → `07-schedule-parser-calendar-sync.md`

**Files:**
- Read: `gen-ai-course/14_ai_projects/schedule_parser_calendar_sync/README.md`, `src/schedule_parser/tools/ocr_tool.py`, `.../tools/image_preprocessor.py`, `.../tools/calendar_tool.py`, `.../agents/parser.py`, `.../agents/validator.py`, `.../pipelines/schedule_pipeline.py`, `.../models.py`, `.../config.py`, `.../main.py`
- Create: `course-content/project-case-studies/07-schedule-parser-calendar-sync.md`

- [ ] **Step 1: Read the source.** Note the OCR → preprocess → LLM-parse → validate → calendar-sync pipeline. This has a real CV/OCR angle — section 3 (image inputs) and section 4 (OCR preprocessing + structured extraction) get extra depth; section 7 includes extraction accuracy / field-level F1.

- [ ] **Step 2: Write the file** from the template, grounded in source. Label numbers illustrative.

- [ ] **Step 3: Verify structure.** Run:
```bash
grep -E "^(# |## )" "course-content/project-case-studies/07-schedule-parser-calendar-sync.md"
```
Expected: title + all 11 `##` headings. Confirm OCR/extraction metric appears in section 7.

- [ ] **Step 4: Commit.**
```bash
git add "course-content/project-case-studies/07-schedule-parser-calendar-sync.md"
git commit -m "docs(case-studies): add schedule_parser_calendar_sync case study"
```

### Task 8: `real_estate_crm_agent` → `08-real-estate-crm-agent.md`

**Files:**
- Read: `gen-ai-course/14_ai_projects/real_estate_crm_agent/README.md`, `src/real_estate_crm/agents/qualifier.py`, `.../tools/sms_tool.py`, `.../tools/email_tool.py`, `.../pipelines/lead_pipeline.py`, `.../models.py`, `.../config.py`, `.../main.py`
- Create: `course-content/project-case-studies/08-real-estate-crm-agent.md`

- [ ] **Step 1: Read the source.** Note lead qualification logic, SMS/email tools, and the lead pipeline. Automation agent — depth on section 4 (qualification prompt + scoring) and section 9 (lead-conversion impact).

- [ ] **Step 2: Write the file** from the template, grounded in source. Label numbers illustrative.

- [ ] **Step 3: Verify structure.** Run:
```bash
grep -E "^(# |## )" "course-content/project-case-studies/08-real-estate-crm-agent.md"
```
Expected: title + all 11 `##` headings.

- [ ] **Step 4: Commit.**
```bash
git add "course-content/project-case-studies/08-real-estate-crm-agent.md"
git commit -m "docs(case-studies): add real_estate_crm_agent case study"
```

### Task 9: `va_task_supervisor_agent` → `09-va-task-supervisor-agent.md`

**Files:**
- Read: `gen-ai-course/14_ai_projects/va_task_supervisor_agent/README.md`, `src/va_supervisor/agents/assigner.py`, `.../tools/notion_tool.py`, `.../tools/slack_tool.py`, `.../pipelines/supervisor_pipeline.py`, `.../models.py`, `.../config.py`, `.../main.py`
- Create: `course-content/project-case-studies/09-va-task-supervisor-agent.md`

- [ ] **Step 1: Read the source.** Note task assignment/supervision logic and Notion/Slack tools. Automation agent — depth on section 4 (assignment reasoning) and section 8 (supervisor loop + integrations).

- [ ] **Step 2: Write the file** from the template, grounded in source. Label numbers illustrative.

- [ ] **Step 3: Verify structure.** Run:
```bash
grep -E "^(# |## )" "course-content/project-case-studies/09-va-task-supervisor-agent.md"
```
Expected: title + all 11 `##` headings.

- [ ] **Step 4: Commit.**
```bash
git add "course-content/project-case-studies/09-va-task-supervisor-agent.md"
git commit -m "docs(case-studies): add va_task_supervisor_agent case study"
```

### Task 10: `ep_job_application_agent` → `10-ep-job-application-agent.md`

**Files:**
- Read: `gen-ai-course/14_ai_projects/ep_job_application_agent/README.md`, `src/ep_job_app/tools/scraper.py`, plus other modules present under `src/ep_job_app/` (`agents/`, `pipelines/`, `models.py`, `config.py`, `main.py`)
- Create: `course-content/project-case-studies/10-ep-job-application-agent.md`

- [ ] **Step 1: Read the source.** Note the scraping + application-generation flow and the LLM used. Automation agent — depth on section 4 (tailoring prompt) and section 8 (scrape→generate→submit flow).

- [ ] **Step 2: Write the file** from the template, grounded in source. Label numbers illustrative.

- [ ] **Step 3: Verify structure.** Run:
```bash
grep -E "^(# |## )" "course-content/project-case-studies/10-ep-job-application-agent.md"
```
Expected: title + all 11 `##` headings.

- [ ] **Step 4: Commit.**
```bash
git add "course-content/project-case-studies/10-ep-job-application-agent.md"
git commit -m "docs(case-studies): add ep_job_application_agent case study"
```

### Task 11: `grant_funding_research_agent` → `11-grant-funding-research-agent.md`

**Files:**
- Read: `gen-ai-course/14_ai_projects/grant_funding_research_agent/README.md`, plus all modules present under its `src/` (`agents/`, `tools/`, `pipelines/`, `models.py`, `config.py`, `main.py`)
- Create: `course-content/project-case-studies/11-grant-funding-research-agent.md`

- [ ] **Step 1: Read the source.** Note the research/retrieval flow and LLM. Research agent — depth on sections 3/4 (sources + query/extraction prompts) and section 7 (precision/recall of relevant grants).

- [ ] **Step 2: Write the file** from the template, grounded in source. Label numbers illustrative.

- [ ] **Step 3: Verify structure.** Run:
```bash
grep -E "^(# |## )" "course-content/project-case-studies/11-grant-funding-research-agent.md"
```
Expected: title + all 11 `##` headings.

- [ ] **Step 4: Commit.**
```bash
git add "course-content/project-case-studies/11-grant-funding-research-agent.md"
git commit -m "docs(case-studies): add grant_funding_research_agent case study"
```

---

## Task 12: Write the index `README.md`

**Files:**
- Create: `course-content/project-case-studies/README.md`

- [ ] **Step 1: Write the index.** Include:
  - A short "How to use this in an interview" intro (walk-through structure, that numbers are illustrative).
  - Projects grouped by archetype: **RAG** (book_recommender, customer_support_engine), **Multi-agent** (multi_agent_researcher, market_intelligence_agent), **Automation agents** (ai_inbox_cleaner, smart_notion_sync_agent, schedule_parser_calendar_sync, real_estate_crm_agent, va_task_supervisor_agent, ep_job_application_agent), **Research agent** (grant_funding_research_agent).
  - For each project: a relative link to its file, a one-paragraph summary, and a "best for showing …" tag.
  - A link to `../SENIOR-AI-ENGINEER-INTERVIEW-GUIDE.md`.

  Adjust grouping if any Step-1 source read in Tasks 1–11 contradicted the assumed archetype.

- [ ] **Step 2: Verify links resolve.** Run:
```bash
ls course-content/project-case-studies/
```
Expected: `README.md` + all 11 numbered files. Confirm each filename referenced in the README exists in that listing.

- [ ] **Step 3: Commit.**
```bash
git add "course-content/project-case-studies/README.md"
git commit -m "docs(case-studies): add index for GenAI project case studies"
```

---

## Task 13: Link the senior interview guide to the new folder

**Files:**
- Modify: `course-content/SENIOR-AI-ENGINEER-INTERVIEW-GUIDE.md`

- [ ] **Step 1: Add a cross-link.** In the "How to Use This Guide" section (around the four-axes list), add a sentence/bullet pointing to the project case studies, e.g.:
  > **Project deep-dives:** For the "walk me through a project you built" round, see [Project Case Studies](project-case-studies/README.md) — 11 end-to-end writeups using a consistent 10-part structure.

- [ ] **Step 2: Verify.** Run:
```bash
grep -n "project-case-studies/README.md" "course-content/SENIOR-AI-ENGINEER-INTERVIEW-GUIDE.md"
```
Expected: one match.

- [ ] **Step 3: Commit.**
```bash
git add "course-content/SENIOR-AI-ENGINEER-INTERVIEW-GUIDE.md"
git commit -m "docs(interview-guide): link to project case studies"
```

---

## Final verification

- [ ] **All files present.** Run:
```bash
ls course-content/project-case-studies/ | wc -l
```
Expected: 12 (README + 11 case studies). The `.gitkeep` from Task 0, if created, should have been superseded — remove it if it still exists:
```bash
rm -f "course-content/project-case-studies/.gitkeep"
```

- [ ] **Every file has all sections.** Run:
```bash
for f in course-content/project-case-studies/[0-9]*.md; do echo "== $f =="; grep -c "^## " "$f"; done
```
Expected: each file reports at least 11 `##` headings.

- [ ] **No unlabeled gaps.** Spot-check 2–3 files: every figure that isn't from code carries an `*Illustrative:*` (or equivalent) tag, and named models match the project source.

## Self-review notes (author)

- **Spec coverage:** Tasks 1–11 cover all 11 projects; Task 12 the central index; Task 13 the guide cross-link — matches spec's in-scope list. Template's 12 sections enforced via the grep checks.
- **Placeholder scan:** Per-task code/commands are concrete; the only deferred items (exact illustrative figures, final archetype) are intentional and instructed, not placeholders.
- **Consistency:** Output filenames in tasks match the project→file map and the index in Task 12.
