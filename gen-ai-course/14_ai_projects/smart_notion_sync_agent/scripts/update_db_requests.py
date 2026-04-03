import requests
import os
import json
from dotenv import load_dotenv

load_dotenv()
NOTION_API_KEY = os.getenv("NOTION_API_KEY")
DB_ID = os.getenv("NOTION_LEADS_DB")

headers = {
    "Authorization": f"Bearer {NOTION_API_KEY}",
    "Notion-Version": "2022-06-28",
    "Content-Type": "application/json"
}

props = {
    "Company": {"rich_text": {}},
    "Status": {"select": {"options": [
        {"name": "New", "color": "blue"},
        {"name": "Contacted", "color": "yellow"},
        {"name": "Converted", "color": "green"},
        {"name": "Lost", "color": "gray"}
    ]}},
    "Email": {"email": {}}
}

# The endpoint for updating a database is PATCH /v1/databases/{id}
r = requests.patch(f"https://api.notion.com/v1/databases/{DB_ID}", headers=headers, json={"properties": props})
print(f"Update Status: {r.status_code}")
if r.status_code != 200:
    print(r.text)
else:
    print("Update successful!")
