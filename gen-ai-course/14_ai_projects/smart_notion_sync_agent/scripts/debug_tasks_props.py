import requests
import os
from dotenv import load_dotenv

load_dotenv()
NOTION_API_KEY = os.getenv("NOTION_API_KEY")

headers = {
    "Authorization": f"Bearer {NOTION_API_KEY}",
    "Notion-Version": "2022-06-28"
}

db_id = os.getenv("NOTION_TASKS_DB")
r = requests.get(f"https://api.notion.com/v1/databases/{db_id}", headers=headers)
props = r.json().get("properties", {})
for k, v in props.items():
    print(f"Property: {k}, Type: {v['type']}")
    if v['type'] == 'status':
        print(f"  Status options: {[o['name'] for o in v['status']['options']]}")
    if v['type'] == 'select':
        print(f"  Select options: {[o['name'] for o in v['select']['options']]}")
