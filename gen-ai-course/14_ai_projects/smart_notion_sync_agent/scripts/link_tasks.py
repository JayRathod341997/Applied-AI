import requests
import os
from dotenv import load_dotenv

load_dotenv()
NOTION_API_KEY = os.getenv("NOTION_API_KEY")
tasks_db = os.getenv("NOTION_TASKS_DB")
leads_db = os.getenv("NOTION_LEADS_DB")
jobs_db = os.getenv("NOTION_JOBS_DB")

headers = {
    "Authorization": f"Bearer {NOTION_API_KEY}",
    "Notion-Version": "2022-06-28",
    "Content-Type": "application/json"
}

def get_pages(db_id):
    r = requests.post(f"https://api.notion.com/v1/databases/{db_id}/query", headers=headers)
    return r.json().get("results", [])

leads = get_pages(leads_db)
jobs = get_pages(jobs_db)
tasks = get_pages(tasks_db)

print(f"Linking {len(tasks)} tasks...")
for i, task in enumerate(tasks):
    tid = task["id"]
    props = {}
    if i < len(leads):
        props["Related Lead"] = {"relation": [{"id": leads[i]["id"]}]}
    if i < len(jobs):
        props["Related Job"] = {"relation": [{"id": jobs[i]["id"]}]}
    
    # PATCH /v1/pages/{page_id}
    r = requests.patch(f"https://api.notion.com/v1/pages/{tid}", headers=headers, json={"properties": props})
    if r.status_code == 200:
        print(f"  Linked Task {i+1}")
    else:
        print(f"  Failed Linked Task {i+1}: {r.text}")

print("--- Data Population Complete ---")
