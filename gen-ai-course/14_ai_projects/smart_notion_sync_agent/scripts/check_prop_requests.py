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

r = requests.get(f"https://api.notion.com/v1/databases/{DB_ID}", headers=headers)
print(f"Status: {r.status_code}")
data = r.json()
if "properties" in data:
    print(f"Properties found: {list(data['properties'].keys())}")
else:
    print(f"Properties NOT found in response. Keys: {list(data.keys())}")
    print(json.dumps(data, indent=2))
