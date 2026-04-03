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

db_id = os.getenv("NOTION_TASKS_DB")
r = requests.get(f"https://api.notion.com/v1/databases/{db_id}", headers=headers)
data = r.json()
print(json.dumps(data.get("properties", {}), indent=2))
