import requests
import os
from dotenv import load_dotenv

load_dotenv()
token = os.getenv("NOTION_API_KEY")
h = {"Authorization": f"Bearer {token}", "Notion-Version": "2022-06-28"}

dbs = {
    "Leads": os.getenv("NOTION_LEADS_DB"),
    "Grants": os.getenv("NOTION_GRANTS_DB"),
    "Jobs": os.getenv("NOTION_JOBS_DB"),
    "Tasks": os.getenv("NOTION_TASKS_DB"),
    "Calendar": os.getenv("NOTION_CALENDAR_DB"),
    "Files": os.getenv("NOTION_FILES_DB")
}

print("Final Count Check:")
for name, db_id in dbs.items():
    if not db_id: continue
    r = requests.post(f"https://api.notion.com/v1/databases/{db_id}/query", headers=h)
    count = len(r.json().get("results", []))
    print(f"  {name}: {count} items")
