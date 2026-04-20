from ...config import settings
from ...tools.notion_client import NotionTool
from ...tools.slack_client import SlackTool
from ...utils.logger import logger
from .state import SlackSyncState, _last_property_snapshot
from datetime import date

notion = NotionTool()
slack = SlackTool()


def get_llm():
    from langchain_groq import ChatGroq

    return ChatGroq(
        model=settings.groq_model_primary,
        groq_api_key=settings.groq_api_key,
        temperature=0,
    )


def ingest_node(state: SlackSyncState) -> SlackSyncState:
    event = state.slack_event
    state.message_text = event.get("text", "")
    state.channel_id = event.get("channel", "")
    # Use thread_ts if in a thread, otherwise fall back to the message's own ts
    state.thread_ts = event.get("thread_ts") or event.get("ts")
    state.user_id = event.get("user", "")
    return state


def classify_node(state: SlackSyncState) -> SlackSyncState:
    llm = get_llm()
    prompt = f"""Classify this Slack message:
"{state.message_text}"

Reply with exactly one word: task, note, or skip.
- task: action item, TODO, "can you...", assigned work
- note: FYI, decision log, reference info
- skip: casual chat, emoji-only, greetings"""

    result = llm.invoke(prompt)
    classification = result.content.strip().lower()
    state.classification = (
        classification if classification in ("task", "note") else "skip"
    )
    return state


def extract_node(state: SlackSyncState) -> SlackSyncState:
    import json
    import re

    llm = get_llm()
    prompt = f"""Extract structured fields from this Slack message and return ONLY a JSON object.

Message: "{state.message_text}"

Return this exact JSON (use null for missing fields):
{{
  "name": "<task name>",
  "due_date": "<YYYY-MM-DD or null>",
  "priority": "<High | Medium | Low or null>",
  "related_job": "<job name/id or null>",
  "related_lead": "<lead name/id or null>"
}}"""

    try:
        result = llm.invoke(prompt)
        raw = result.content.strip()
        raw = re.sub(r"```(?:json)?|```", "", raw).strip()
        data = json.loads(raw)
        state.task_name = data.get("name") or state.message_text[:200]
        state.task_due_date = data.get("due_date")
        state.task_priority = data.get("priority")
        state.task_related_job = data.get("related_job")
        state.task_related_lead = data.get("related_lead")
        logger.info(
            "extract_node: Parsed â†’ name=%s due=%s priority=%s job=%s lead=%s",
            state.task_name,
            state.task_due_date,
            state.task_priority,
            state.task_related_job,
            state.task_related_lead,
        )
    except Exception as e:
        logger.warning("extract_node: Extraction failed (%s), using raw text", e)
        state.task_name = state.message_text[:200]
    return state


def task_node(state: SlackSyncState) -> SlackSyncState:
    db_id = settings.notion_tasks_db
    if not db_id:
        logger.warning("task_node: NOTION_TASKS_DB not configured")
        return state

    properties = {
        "Name": {
            "title": [
                {"text": {"content": state.task_name or state.message_text[:200]}}
            ]
        },
        "Status": {"select": {"name": "To Do"}},
        "Source": {
            "rich_text": [
                {
                    "text": {
                        "content": f"slack://{state.channel_id}/{state.thread_ts or ''}"
                    }
                }
            ]
        },
        "Slack User": {"rich_text": [{"text": {"content": state.user_id}}]},
    }

    if state.task_due_date:
        properties["Due Date"] = {"date": {"start": state.task_due_date}}

    if state.task_priority:
        properties["Priority"] = {"select": {"name": state.task_priority}}

    if state.task_related_job:
        properties["Related Job"] = {
            "rich_text": [{"text": {"content": state.task_related_job}}]
        }

    if state.task_related_lead:
        properties["Related Lead"] = {
            "rich_text": [{"text": {"content": state.task_related_lead}}]
        }

    logger.info("task_node: Creating Notion page in Tasks DB %s", db_id)
    page = notion.create_page(db_id, properties=properties)
    state.notion_page_id = page["id"] if page else None
    logger.info("task_node: Page created â†’ %s", state.notion_page_id)
    return state


def note_node(state: SlackSyncState) -> SlackSyncState:
    db_id = settings.notion_notes_db
    if not db_id:
        logger.warning("Notes DB not configured")
        return state

    page = notion.create_page(
        db_id,
        properties={
            "Name": {"title": [{"text": {"content": state.message_text[:200]}}]},
            "Tags": {"multi_select": [{"name": "slack"}]},
            "Source": {
                "rich_text": [{"text": {"content": f"slack://{state.channel_id}"}}]
            },
        },
    )
    state.notion_page_id = page["id"] if page else None
    return state


def slack_ack_node(state: SlackSyncState) -> SlackSyncState:
    if state.notion_page_id and state.thread_ts:
        slack.add_reaction(
            channel=state.channel_id,
            name="white_check_mark",
            timestamp=state.thread_ts,
        )
    return state


def _property_value_as_text(prop: dict) -> str | None:
    if not isinstance(prop, dict):
        return None

    prop_type = prop.get("type")
    if prop_type == "title":
        text = "".join(part.get("plain_text", "") for part in prop.get("title", []))
        return text or None
    if prop_type == "rich_text":
        text = "".join(part.get("plain_text", "") for part in prop.get("rich_text", []))
        return text or None
    if prop_type in ("select", "status"):
        return (prop.get(prop_type) or {}).get("name")
    if prop_type == "multi_select":
        values = [
            item.get("name") for item in prop.get("multi_select", []) if item.get("name")
        ]
        return ", ".join(values) or None
    if prop_type == "date":
        date_value = prop.get("date") or {}
        start = date_value.get("start")
        end = date_value.get("end")
        if start and end:
            return f"{start} -> {end}"
        return start
    if prop_type == "number":
        value = prop.get("number")
        return str(value) if value is not None else None
    if prop_type == "checkbox":
        value = prop.get("checkbox")
        return str(bool(value)) if value is not None else None
    if prop_type in (
        "url",
        "email",
        "phone_number",
        "created_time",
        "last_edited_time",
    ):
        return prop.get(prop_type)
    if prop_type == "people":
        values = [
            person.get("name") or person.get("id")
            for person in prop.get("people", [])
            if person.get("name") or person.get("id")
        ]
        return ", ".join(values) or None
    if prop_type == "relation":
        values = [item.get("id") for item in prop.get("relation", []) if item.get("id")]
        return ", ".join(values) or None
    if prop_type == "formula":
        formula = prop.get("formula") or {}
        formula_type = formula.get("type")
        if formula_type:
            value = formula.get(formula_type)
            return str(value) if value is not None else None
        return None

    return None


def _extract_trackable_properties(page: dict) -> dict[str, str | None]:
    props = page.get("properties", {})
    result: dict[str, str | None] = {}
    for prop_name, prop in props.items():
        result[prop_name] = _property_value_as_text(prop)
    return result


def _compute_field_changes(
    previous_props: dict[str, str | None], current_props: dict[str, str | None]
) -> list[dict[str, str | None]]:
    changes: list[dict[str, str | None]] = []
    for prop_name in sorted(set(previous_props) | set(current_props)):
        old_value = previous_props.get(prop_name)
        new_value = current_props.get(prop_name)
        if old_value != new_value:
            changes.append({"field": prop_name, "old": old_value, "new": new_value})
    return changes


def poll_node(state: SlackSyncState) -> SlackSyncState:
    db_id = settings.notion_tasks_db
    if not db_id:
        logger.warning("poll_node: NOTION_TASKS_DB not configured, skipping fetch")
        state.notion_changes = []
        return state

    today = date.today().isoformat()
    filter_dict = {"property": "Due Date", "date": {"equals": today}}

    logger.info(
        "poll_node: Fetching tasks from Notion DB %s with filter %s",
        db_id,
        filter_dict,
    )
    results = notion.query_database(db_id, filter_dict=filter_dict)
    logger.info("poll_node: Fetched %d pages from Notion", len(results))

    state.notion_changes = []
    for page in results:
        pid = page["id"]
        current_props = _extract_trackable_properties(page)
        previous_props = _last_property_snapshot.get(pid)
        field_changes = _compute_field_changes(previous_props or {}, current_props)

        if previous_props is None or field_changes:
            page_with_changes = dict(page)
            page_with_changes["_field_changes"] = field_changes
            state.notion_changes.append(page_with_changes)

        _last_property_snapshot[pid] = current_props

    logger.info("poll_node: %d changed page(s) detected", len(state.notion_changes))
    return state


def format_node(state: SlackSyncState) -> SlackSyncState:
    event_blocks: list[str] = []
    for idx, page in enumerate(state.notion_changes[:5], start=1):
        props = page.get("properties", {})
        name = _property_value_as_text(props.get("Name", {})) or "Untitled"
        status = _property_value_as_text(props.get("Status", {})) or "Unknown"
        field_changes = page.get("_field_changes", [])

        updated_fields = [
            change.get("field")
            for change in field_changes
            if isinstance(change, dict) and change.get("field")
        ]
        updated_fields_text = ", ".join(updated_fields) if updated_fields else "None"

        lines = [
            f"{idx}. *{name}*",
            f"Status: {status}",
            f"Updated properties: {updated_fields_text}",
        ]

        for change in field_changes:
            field_name = change.get("field", "Unknown field")
            old_value = change.get("old") if change.get("old") is not None else "(empty)"
            new_value = change.get("new") if change.get("new") is not None else "(empty)"
            lines.append(f"- {field_name}: {old_value} -> {new_value}")

        event_blocks.append("\n".join(lines))

    state.slack_message = "Notion updates:\n\n" + "\n\n".join(event_blocks)
    state.target_channel = settings.slack_sync_channel
    logger.info("format_node: Message prepared for channel %s", state.target_channel)
    return state


def notify_node(state: SlackSyncState) -> SlackSyncState:
    if state.slack_message and state.target_channel:
        logger.info(
            "notify_node: Posting message to Slack channel %s", state.target_channel
        )
        slack.post_message(channel=state.target_channel, text=state.slack_message)
        logger.info("notify_node: Message posted successfully")
    else:
        logger.debug("notify_node: Nothing to post (no message or channel configured)")
    return state


# â”€â”€ Routing â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€


def route_classification(state: SlackSyncState) -> str:
    return state.classification


def route_changes(state: SlackSyncState) -> str:
    return "changed" if state.notion_changes else "no_changes"
