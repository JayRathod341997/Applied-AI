# Smart Notion Sync Agent - Interview Q&A

## Q1: How does the bi-directional sync handle conflicts?
**A:** When the same record is modified in both Notion and Google, the ConflictResolverAgent uses ChatGroq (llama-3.3-70b) to analyze both versions and produce a merged result. It compares timestamps, field-level changes, and content hashes to determine the best resolution strategy (use_a, use_b, or merge).

## Q2: What happens if a sync fails midway?
**A:** The sync engine uses exponential backoff retry logic. Failed records are placed in a dead letter queue for manual review. Each source sync is transactional - either all records in a batch succeed or the batch is retried.

## Q3: How do you detect changes efficiently?
**A:** We use a two-layer approach: timestamp comparison for quick filtering (only check records modified since last sync) and content hashing (SHA-256 of sorted key-value pairs) for detecting actual content changes.

## Q4: Why use an LLM for conflict resolution instead of rules?
**A:** Data conflicts in real-world scenarios are nuanced. A rule-based system would need extensive case handling. The LLM understands context - for example, it can distinguish between a typo correction and a meaningful data change, and it can merge partial updates intelligently.

## Q5: How does this agent integrate with the other 9 agents?
**A:** Other agents push their activity logs (job applications, lead updates, task completions) to Notion databases. This agent ensures those records are also reflected in Google Calendar/Drive where needed, and vice versa.

## Q6: What rate limiting strategy do you use for Notion API?
**A:** Notion's API allows 3 requests per second. We use a token bucket rate limiter with batch processing of 50 records per batch, with 200ms delays between batches.

## Q7: How would you add a new sync source?
**A:** Create a new tool class in `tools/` (e.g., `slack_tool.py`), add a `sync_<source>` method to `SyncEngine`, register it in the `full_sync` dispatcher, and add the corresponding Notion database ID to config.
