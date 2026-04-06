# Implementation Plan: First-Time Initialization & Real-Time Sync

## Goal
Populate an empty Google Calendar with existing milestones from the Notion "Master Sync Calendar" database and establish a bi‑directional sync so future edits stay in sync.

## Proposed Changes

### 1. Configuration (`config.py`)
- Add `google_calendar_id` (already present) and ensure it is set to the target calendar ID.
- Add a constant for the Notion hidden property name that will store the Google `event_id` (e.g., `sync_id`).

### 2. Mapping Helpers (`utils/calendar_mapping.py` – new file)
- Define a function `notion_to_gcal(event: Dict) -> Dict` that maps Notion fields to Google Calendar fields (title, start/end, location, description, etc.).
- Define a reverse mapper `gcal_to_notion(event: Dict) -> Dict` for future updates.

### 3. Initial Push Script (`scripts/initial_sync.py` – new script)
- Query Notion database `settings.notion_calendar_db` for records where the hidden `sync_id` property is empty.
- For each record:
  1. Convert to Google event using the mapper.
  2. Call `GoogleCalendarTool.create_event`.
  3. Store the returned `event_id` back into the Notion record via `NotionTool.update_page`.
- Log successes and failures.

### 4. Extend `SyncEngine`
- Add method `async def initial_sync_calendar(self) -> Dict` that performs the same logic as the script but can be triggered via the `/sync/trigger` endpoint with a new action `initial_sync`.
- Update `full_sync` to optionally call `initial_sync_calendar` when `direction` is `initial`.

### 5. Conflict Resolution Enhancements
- When a Notion record changes, compare its hash with the stored hash (use `_hash_content`).
- If the Google event differs, invoke `ConflictResolverAgent.resolve` with both payloads.
- Apply the chosen resolution (use A, use B, or merge) and update both sides.

### 6. Logging & Monitoring
- Use existing `logger` to emit `X-Process-Time` and detailed info for each synced record.
- Add health endpoint fields for `last_initial_sync` timestamp.

## Open Questions (User Review Required)
- **Hidden Sync ID Property Name**: What is the exact Notion property key for the hidden sync identifier? (e.g., `Sync ID` vs `sync_id`).
- **Timezone Handling**: Should we assume UTC for all dates, or read a timezone from Notion and convert to the Google calendar's timezone?
- **Conflict Preference**: In case of simultaneous edits, should the default resolution favor Notion (`use_a`) unless the AI explicitly chooses otherwise?

## Verification Plan
### Automated Tests
- Run `scripts/initial_sync.py` and assert that the number of created Google events matches the number of Notion rows without a `sync_id`.
- Verify that each Notion page now contains the `sync_id` property.
- Trigger an incremental update (modify a Notion location) and ensure the Google event updates accordingly.

### Manual Verification
- Open the target Google Calendar in a browser and visually confirm that all milestones appear with correct titles, dates, locations, and descriptions.
- Check a few Notion entries to see the stored `event_id`.
- Simulate a conflict by editing the same event in Google Calendar and Notion, then run the sync and verify the AI‑driven resolution is applied.

---
*Please confirm the hidden property name and any timezone preferences so we can finalize the implementation.*
