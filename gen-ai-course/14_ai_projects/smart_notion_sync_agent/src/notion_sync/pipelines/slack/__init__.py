from .state import SlackSyncState
from .graphs import slack_to_notion, notion_to_slack


def invoke_slack_to_notion(event: dict):
    return slack_to_notion.invoke(SlackSyncState(slack_event=event))


def invoke_notion_to_slack():
    return notion_to_slack.invoke(SlackSyncState())
