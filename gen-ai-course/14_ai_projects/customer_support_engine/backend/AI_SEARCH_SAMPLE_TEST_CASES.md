# AI Search Sample Test Cases (Updated)

These test cases are aligned with the new KB dataset in:
- `backend/.data/knowledge_base.jsonl`
- `backend/data/knowledge_base.jsonl`

Each case includes expected retrieval output (`kb_chunks`) and expected graph-level behavior.

## Preconditions

1. Knowledge base ingested:
```bash
uv run python -m support.tools.kb_search --ingest ./data/knowledge_base.jsonl
```
2. App is configured with valid Azure Search/OpenAI settings.
3. Graph is invoked with `conversation_id` and `retry_count`.

---

## Test Case 1 - Duplicate Charge (Billing Resolved)

**User input**
```json
{
  "messages": [{"role": "user", "content": "I was charged twice this month for my subscription."}],
  "conversation_id": "tc-ai-001",
  "retry_count": 0
}
```

**Expected retrieved KB signals**
- Matches `billing-duplicate-charge`
- May also match `billing-refund-policy`

**Expected output (truncated)**
```json
{
  "issue_type": "billing",
  "severity": "medium",
  "kb_chunks": [
    "Issue type: billing. Symptom: customer reports duplicate subscription charge...",
    "Issue type: billing policy. Standard policy..."
  ],
  "resolution_status": "resolved",
  "feedback_signal": "no_feedback"
}
```

---

## Test Case 2 - Password Reset Email Missing (Technical Auth)

**User input**
```json
{
  "messages": [{"role": "user", "content": "I never received the password reset email."}],
  "conversation_id": "tc-ai-002",
  "retry_count": 0
}
```

**Expected retrieved KB signals**
- Matches `auth-password-reset-missing-email`

**Expected output (truncated)**
```json
{
  "issue_type": "technical",
  "severity": "low",
  "kb_chunks": [
    "Issue type: technical-auth. Symptom: password reset email not received..."
  ],
  "resolution_steps": [
    "Validate account email and spam folder.",
    "Check suppression/bounce state.",
    "Resend reset token or provide fallback link."
  ],
  "resolution_status": "resolved"
}
```

---

## Test Case 3 - API 429 Throttling (Reliability Guidance)

**User input**
```json
{
  "messages": [{"role": "user", "content": "We're getting too many 429 rate limit errors from the API."}],
  "conversation_id": "tc-ai-003",
  "retry_count": 0
}
```

**Expected retrieved KB signals**
- Matches `api-429-rate-limit`
- May also match `performance-token-control`

**Expected output (truncated)**
```json
{
  "issue_type": "technical",
  "severity": "medium",
  "kb_chunks": [
    "Issue type: reliability. Symptom: intermittent 429 throttling...",
    "Performance concern: high token usage increases latency and cost..."
  ],
  "resolution_steps": [
    "Implement exponential backoff with jitter.",
    "Reduce concurrency and repeated requests.",
    "Evaluate quota/region scaling if persistent."
  ],
  "resolution_status": "resolved"
}
```

---

## Test Case 4 - Production Outage (High Severity Escalation)

**User input**
```json
{
  "messages": [{"role": "user", "content": "Our production API is down and customers are blocked."}],
  "conversation_id": "tc-ai-004",
  "retry_count": 0
}
```

**Expected retrieved KB signals**
- Matches `graph-severity-escalation`
- May match `api-500-upstream-failure`

**Expected output (truncated)**
```json
{
  "issue_type": "technical",
  "severity": "high",
  "resolution_status": "escalated",
  "feedback_signal": "no_feedback"
}
```

---

## Test Case 5 - KB Ingestion Failure Troubleshooting

**User input**
```json
{
  "messages": [{"role": "user", "content": "Knowledge base ingestion failed with a file or credential error."}],
  "conversation_id": "tc-ai-005",
  "retry_count": 0
}
```

**Expected retrieved KB signals**
- Matches `kb-ingestion-file-format`
- Matches `debug-playbook-kb-ingest-failure`
- May match `kb-ingestion-command-paths`

**Expected output (truncated)**
```json
{
  "issue_type": "technical",
  "kb_chunks": [
    "Feature area: knowledge base ingestion. Expected format is JSONL...",
    "Debugging playbook for ingestion errors: confirm JSONL path exists..."
  ],
  "resolution_steps": [
    "Validate JSONL lines and required fields.",
    "Verify endpoint/key/index and permissions.",
    "Re-run ingestion with corrected path."
  ],
  "resolution_status": "resolved"
}
```

---

## Test Case 6 - Configuration Missing Environment Variables

**User input**
```json
{
  "messages": [{"role": "user", "content": "Service fails at startup with missing environment variable errors."}],
  "conversation_id": "tc-ai-006",
  "retry_count": 0
}
```

**Expected retrieved KB signals**
- Matches `config-missing-env-vars`
- May match `debug-playbook-startup`

**Expected output (truncated)**
```json
{
  "issue_type": "technical",
  "severity": "medium",
  "kb_chunks": [
    "Configuration issue: application fails at startup due to missing environment variables...",
    "Debugging playbook for startup errors..."
  ],
  "resolution_steps": [
    "Compare .env against .env.example.",
    "Set required Azure and app variables.",
    "Restart and confirm successful startup."
  ],
  "resolution_status": "resolved"
}
```

---

## Test Case 7 - Retry Loop Then Escalation

**User input**
```json
{
  "messages": [
    {"role": "user", "content": "Login issue still not fixed after your steps."}
  ],
  "conversation_id": "tc-ai-007",
  "retry_count": 2,
  "feedback_signal": "not_helpful"
}
```

**Expected retrieved KB signals**
- Matches `graph-feedback-loop-behavior`
- May match `auth-login-loop`

**Expected output (truncated)**
```json
{
  "retry_count": 2,
  "feedback_signal": "not_helpful",
  "resolution_status": "escalated"
}
```

---

## Test Case 8 - Feature Request Intake

**User input**
```json
{
  "messages": [{"role": "user", "content": "Can you add SSO support for our enterprise tenant?"}],
  "conversation_id": "tc-ai-008",
  "retry_count": 0
}
```

**Expected retrieved KB signals**
- Matches `user-interaction-feature-request`

**Expected output (truncated)**
```json
{
  "issue_type": "general",
  "severity": "low",
  "kb_chunks": [
    "Common user interaction: feature request submission..."
  ],
  "resolution_steps": [
    "Capture use case and business impact.",
    "Classify as enhancement and route to backlog.",
    "Set expectation: reviewed, not guaranteed."
  ],
  "resolution_status": "resolved"
}
```
