import requests
import os
import json
from dotenv import load_dotenv

load_dotenv()
NOTION_API_KEY = os.getenv("NOTION_API_KEY")

headers = {
    "Authorization": f"Bearer {NOTION_API_KEY}",
    "Notion-Version": "2022-06-28"
}

db_map = {
    "JOBS": os.getenv("NOTION_JOBS_DB"),
    "TASKS": os.getenv("NOTION_TASKS_DB"),
    "CALENDAR": os.getenv("NOTION_CALENDAR_DB"),
    "FILES": os.getenv("NOTION_FILES_DB")
}

print("Verifying schemas for remaining tables...")
for name, db_id in db_map.items():
    if not db_id:
        print(f"{name}: Database ID not found in .env")
        continue
    r = requests.get(f"https://api.notion.com/v1/databases/{db_id}", headers=headers)
    if r.status_code == 200:
        data = r.json()
        props = data.get("properties", {})
        title_prop = next((k for k, v in props.items() if v["type"] == "title"), "??")
        print(f"{name} ({db_id}): TitleProp='{title_prop}', AllProps={list(props.keys())}")
    else:
        print(f"{name} ({db_id}): Error {r.status_code} - {r.text}")
