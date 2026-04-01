# Real Estate CRM Assistant - Interview Q&A

## Q1: How does the LLM qualify leads?
**A:** The qualifier agent receives all lead fields and analyzes budget clarity, timeline urgency, pre-approval status, and specificity of criteria. It returns a 0-100 score with hot/warm/cold categorization and reasoning.

## Q2: Why use LLM instead of rule-based scoring?
**A:** Lead messages are unstructured natural language. An LLM can understand "we're pre-approved and need to move in 3 months" implies higher intent than "just browsing." Rules would need extensive regex patterns.

## Q3: How does the follow-up sequence work?
**A:** Day 0: Welcome SMS + email sent immediately. Day 1: Property match email. Day 3: Follow-up SMS. Day 7: Nurture email. APScheduler manages the timing.

## Q4: What happens if SMS/email fails?
**A:** The pipeline logs failures but continues processing. Failed deliveries are retried with exponential backoff. The lead record in Notion is updated with delivery status.

## Q5: How do hot leads get special treatment?
**A:** Hot leads trigger an immediate Slack notification to the sales team. They also get prioritized in the follow-up sequence with shorter intervals between touches.
