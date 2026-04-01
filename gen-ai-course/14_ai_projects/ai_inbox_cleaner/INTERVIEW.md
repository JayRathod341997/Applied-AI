# AI Inbox Cleaner - Interview Q&A

## Q1: Why use two different LLM models?
**A:** The fast model (llama-3.1-8b-instant) handles classification because it's latency-sensitive - we need quick categorization for potentially hundreds of emails. The primary model (llama-3.3-70b-versatile) handles reply drafting where quality matters more than speed.

## Q2: How does the categorization work?
**A:** Each email (from, subject, body) is sent to the classifier agent with a structured prompt listing the 6 categories. The LLM returns a JSON response with category, confidence score, priority level, and reasoning. We use temperature=0 for consistent classification.

## Q3: What happens with emails that don't fit any category?
**A:** The LLM assigns the closest match with a lower confidence score. If confidence is below 0.5, the email is labeled "Unsorted" for manual review. The system learns from user corrections over time.

## Q4: How do you handle Gmail API rate limits?
**A:** Gmail API allows 250 quota units per second. We batch requests (50 messages per poll), use partial responses to reduce payload size, and implement exponential backoff on 429 errors.

## Q5: How does the reply drafting work without sending?
**A:** Drafts are created in Gmail's draft folder using the drafts API, not sent directly. The user reviews and sends manually. This prevents accidental sends while still saving time on common responses.

## Q6: How would you add a new email category?
**A:** Add the category name to the CLASSIFICATION_PROMPT, add a label mapping in CATEGORY_LABEL_MAP, and optionally add special handling in the action router. No model retraining needed - it's all prompt-based.
