# GenAI Project Case Studies for Interview Prep — Design

**Date:** 2026-06-16
**Status:** Approved (design); pending implementation plan

## Summary

Produce 11 deep, interview-ready case studies — one per project under
`gen-ai-course/14_ai_projects/` — that let the user walk an interviewer through any
project end-to-end using a single, consistent 10-part structure. The case studies are
documentation only; no application code changes.

Target use: the "walk me through a project you built" round of a Senior AI Engineer
interview (see `course-content/SENIOR-AI-ENGINEER-INTERVIEW-GUIDE.md`).

## Decisions (locked during brainstorming)

| Decision | Choice |
|----------|--------|
| Subject | The GenAI projects already in this repo |
| Coverage | All 11 projects, deep |
| Location | One central interview-prep folder (not per-project folders) |
| Heading mapping | Keep all 10 of the user's headings, reframed for GenAI |
| Metrics sourcing | Realistic illustrative numbers, **explicitly labeled** illustrative |

## Scope

### In scope
- A new folder `course-content/project-case-studies/`.
- `README.md` index for that folder.
- 11 case-study markdown files, one per project.
- A link from `SENIOR-AI-ENGINEER-INTERVIEW-GUIDE.md` to the new folder.

### Out of scope
- Any change to project source code, READMEs, quizzes, or existing course content.
- Running the projects to produce real benchmark numbers.
- Classic-ML or generic-template case studies (explicitly de-scoped during brainstorming).

## The 11 projects

Grouped by archetype (used for the index grouping):

- **RAG / retrieval**
  - `book_recommender`
  - `customer_support_engine`
- **Multi-agent**
  - `multi_agent_researcher`
  - `market_intelligence_agent`
- **Single-agent automation**
  - `ai_inbox_cleaner`
  - `smart_notion_sync_agent`
  - `schedule_parser_calendar_sync`
  - `real_estate_crm_agent`
  - `va_task_supervisor_agent`
  - `ep_job_application_agent`
  - `grant_funding_research_agent`

> Note: the final archetype assignment per project is confirmed at write time by reading
> each project's source; the grouping above is the working assumption.

## File layout

```
course-content/
  project-case-studies/
    README.md                 # index + how-to-use + archetype grouping
    01-ai-inbox-cleaner.md
    02-book-recommender.md
    03-customer-support-engine.md
    04-multi-agent-researcher.md
    05-market-intelligence-agent.md
    06-smart-notion-sync-agent.md
    07-schedule-parser-calendar-sync.md
    08-real-estate-crm-agent.md
    09-va-task-supervisor-agent.md
    10-ep-job-application-agent.md
    11-grant-funding-research-agent.md
```

> File numbering is for stable ordering only; the exact number→project mapping is
> finalized at write time. Names are kebab-case of the project folder name.

## Per-file template

Every case-study file follows the same structure so they are easy to rehearse:

1. **30-second pitch** (top of file) — the elevator version of the whole story.
2. **Problem statement** — the real-world pain and who has it.
3. **Why AI/ML was needed** — why rules/manual didn't suffice; why an LLM/agent specifically.
4. **Dataset → Knowledge corpus & eval set** — what data flows in (emails, docs, leads),
   corpus size, and how a golden/eval set was (or would be) built.
5. **Feature engineering → Prompt & context engineering** — chunking, retrieval, prompt
   design, structured-output schemas, tool definitions.
6. **Model selection rationale** — which LLM(s), embedding/reranker choices, and the
   cost/latency/quality trade-offs behind them.
7. **Training process → Prompt iteration / fine-tuning-or-why-not** — how prompts were
   refined; honest "no training, and here's why RAG/prompting was the right call."
8. **Evaluation metrics** — task-appropriate metrics (classification accuracy/F1,
   retrieval hit-rate/MRR, faithfulness/groundedness, human-approval rate).
9. **Deployment architecture** — components, data flow, triggers (poller/webhook),
   external integrations, and where it would run in production (e.g. Azure).
10. **Business impact** — time saved, throughput, cost (illustrative, labeled).
11. **Lessons learned** — what broke, what to do differently, the senior-level trade-off
    reflection.
12. **Likely follow-up questions** (bottom of file) — 5–8 probing questions an interviewer
    would ask, each with a one-line answer pointer.

This preserves all 10 of the original headings (items 2–11 map to them) and adds the
30-second pitch and follow-up questions as interview-usability extras.

## Content sourcing rules

- **Grounded in code.** Architecture, models, tools, pipelines, and flow come from each
  project's actual source (`README.md`, `models.py`, `agents/`, `pipelines/`, `tools/`,
  `config.py`, `main.py`).
- **Illustrative numbers are labeled.** Any figure not directly derivable from the code
  (corpus size, latency, cost, accuracy, business impact) is written as a defensible
  representative value and explicitly marked, e.g.
  `*Illustrative:* ~5k support docs, p95 ~1.8s, ~$0.004/query`.
- **No invented measured results.** Nothing is presented as a benchmarked/measured result
  unless the repo actually contains it.
- **Depth scales with code.** Heavier projects (e.g. `book_recommender` RAG,
  `market_intelligence_agent` multi-agent) get proportionally richer technical detail.

## Index (`README.md`) contents

- Short "how to use this in an interview" intro.
- Projects grouped by archetype.
- Per project: one-paragraph summary + a "best for showing …" tag (e.g. "best for showing
  retrieval + reranking depth").
- Link back to `SENIOR-AI-ENGINEER-INTERVIEW-GUIDE.md`, and a link added from that guide
  to this folder.

## Build process

1. For each project, read README + key source files to extract the real architecture and
   model choices.
2. Write the case study from the template, filling grounded sections from code and
   labeling all illustrative numbers.
3. Write the index `README.md` once all 11 exist.
4. Add the cross-link from `SENIOR-AI-ENGINEER-INTERVIEW-GUIDE.md`.

## Success criteria

- 11 case-study files + 1 index exist under `course-content/project-case-studies/`.
- Each file covers all 12 template sections, with the 10 original headings represented.
- Every non-derivable number is explicitly labeled illustrative.
- Architecture/model claims match the actual project source.
- The senior interview guide links to the new folder.
