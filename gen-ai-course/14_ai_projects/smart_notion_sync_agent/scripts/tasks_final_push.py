import requests
import os
import time
from dotenv import load_dotenv

load_dotenv()
NOTION_API_KEY = os.getenv("NOTION_API_KEY")
tasks_db = os.getenv("NOTION_TASKS_DB")
headers = {
    "Authorization": f"Bearer {NOTION_API_KEY}",
    "Notion-Version": "2022-06-28",
    "Content-Type": "application/json"
}

# 1. Basic Props
print("Updating TASKS basic props...")
basic_props = {
    "Status": {"select": {"options": [{"name": "To Do"}, {"name": "In Progress"}, {"name": "Done"}]}},
    "Priority": {"select": {"options": [{"name": "High"}, {"name": "Medium"}, {"name": "Low"}]}},
    "Due Date": {"date": {}}
}
r1 = requests.patch(f"https://api.notion.com/v1/databases/{tasks_db}", headers=headers, json={"properties": basic_props})
print(f"Basic props update: {r1.status_code}")
if r1.status_code != 200: print(r1.text)

# 2. Relations (Optional attempt)
leads_db = os.getenv("NOTION_LEADS_DB")
jobs_db = os.getenv("NOTION_JOBS_DB")
print("Updating TASKS relations...")
# For multi-property update, sometimes they fail collectively. Let's do them individually.
r2 = requests.patch(f"https://api.notion.com/v1/databases/{tasks_db}", headers=headers, json={
    "properties": {"Related Lead": {"relation": {"database_id": leads_db}}}
})
print(f"Relation Lead: {r2.status_code}")
r3 = requests.patch(f"https://api.notion.com/v1/databases/{tasks_db}", headers=headers, json={
    "properties": {"Related Job": {"relation": {"database_id": jobs_db}}}
})
print(f"Relation Job: {r3.status_code}")

# 3. Populate
print("Populating TASKS...")
task_data = [
    {"Name": "Master Notion API", "Status": "In Progress", "Priority": "High", "Date": "2026-04-05"},
    {"Name": "Sync System Test", "Status": "To Do", "Priority": "Medium", "Date": "2026-04-06"},
    {"Name": "Project Review", "Status": "To Do", "Priority": "Low", "Date": "2026-04-10"}
]
for t in task_data:
    p = {
        "Name": {"title": [{"text": {"content": t["Name"]}}]},
        "Status": {"select": {"name": t["Status"]}},
        "Priority": {"select": {"name": t["Priority"]}},
        "Due Date": {"date": {"start": t["Date"]}}
    }
    r = requests.post("https://api.notion.com/v1/pages", headers=headers, json={"parent": {"database_id": tasks_db}, "properties": p})
    if r.status_code == 200:
        print(f"  Added task: {t['Name']}")
    else:
        print(f"  Failed task {t['Name']}: {r.text}")

print("\n--- Done with TASKS attempt ---")
