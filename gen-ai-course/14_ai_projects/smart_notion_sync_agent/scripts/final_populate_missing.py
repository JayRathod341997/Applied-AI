import requests
import os
import json
import time
from dotenv import load_dotenv
from datetime import datetime, timedelta

load_dotenv()
NOTION_API_KEY = os.getenv("NOTION_API_KEY")

headers = {
    "Authorization": f"Bearer {NOTION_API_KEY}",
    "Notion-Version": "2022-06-28",
    "Content-Type": "application/json"
}

def update_db(db_id, props):
    print(f"Updating {db_id} props...")
    r = requests.patch(f"https://api.notion.com/v1/databases/{db_id}", headers=headers, json={"properties": props})
    if r.status_code != 200:
        print(f"  Fail: {r.text}")
    else:
        print(f"  Success updating {db_id}")

def add_page(name, db_id, props):
    r = requests.post("https://api.notion.com/v1/pages", headers=headers, json={
        "parent": {"database_id": db_id},
        "properties": props
    })
    if r.status_code == 200:
        print(f"  Added: {name}")
        return json.loads(r.text)["id"]
    else:
        print(f"  Error adding {name}: {r.text}")
        return None

def get_recent_pages(db_id):
    r = requests.post(f"https://api.notion.com/v1/databases/{db_id}/query", headers=headers)
    if r.status_code == 200:
        return [p["id"] for p in r.json().get("results", [])]
    return []

# DATABASE IDs
jobs_db = os.getenv("NOTION_JOBS_DB")
tasks_db = os.getenv("NOTION_TASKS_DB")
cal_db = os.getenv("NOTION_CALENDAR_DB")
files_db = os.getenv("NOTION_FILES_DB")
leads_db = os.getenv("NOTION_LEADS_DB")

# 1. Update Properties
print("\n--- UPDATING SCHEMAS ---")
update_db(jobs_db, {
    "Company": {"rich_text": {}},
    "Status": {"select": {"options": [{"name": "Applied"}, {"name": "Interviewing"}, {"name": "Offer"}]}},
    "Application Date": {"date": {}}
})
update_db(tasks_db, {
    "Status": {"select": {"options": [{"name": "To Do"}, {"name": "In Progress"}, {"name": "Done"}]}},
    "Priority": {"select": {"options": [{"name": "High"}, {"name": "Medium"}, {"name": "Low"}]}},
    "Due Date": {"date": {}},
    "Related Lead": {"relation": {"database_id": leads_db}},
    "Related Job": {"relation": {"database_id": jobs_db}}
})
update_db(cal_db, {
    "Location": {"rich_text": {}},
    "Type": {"select": {"options": [{"name": "Meeting"}, {"name": "Call"}, {"name": "Deep Work"}]}},
    "Date": {"date": {}}
})
update_db(files_db, {
    "Type": {"select": {"options": [{"name": "PDF"}, {"name": "Doc"}, {"name": "Other"}]}},
    "Drive Link": {"url": {}}
})

print("\n--- WAITING 2 SECONDS FOR PROP SYNC ---")
time.sleep(2)

# FETCH LEADS FOR RELATIONS
lead_ids = get_recent_pages(leads_db)

# 2. Populate JOBS
print("\n--- POPULATING JOBS ---")
job_data = [
    {"Name": "Staff Engineer", "Company": "Anthropic", "Status": "Applied", "Date": "2026-04-01"},
    {"Name": "Founding Dev", "Company": "ElevenLabs", "Status": "Interviewing", "Date": "2026-03-25"},
    {"Name": "Senior Researcher", "Company": "Mistral", "Status": "Interviewing", "Date": "2026-04-02"}
]
job_ids = []
for j in job_data:
    jid = add_page(j["Name"], jobs_db, {
        "Name": {"title": [{"text": {"content": j["Name"]}}]},
        "Company": {"rich_text": [{"text": {"content": j["Company"]}}]},
        "Status": {"select": {"name": j["Status"]}},
        "Application Date": {"date": {"start": j["Date"]}}
    })
    if jid: job_ids.append(jid)

# 3. Populate TASKS
print("\n--- POPULATING TASKS ---")
task_data = [
    {"Name": "Prep Anthropic Deck", "Status": "In Progress", "Priority": "High", "Date": "2026-04-04"},
    {"Name": "Record Mistral Demo", "Status": "To Do", "Priority": "Medium", "Date": "2026-04-05"}
]
for i, t in enumerate(task_data):
    p = {
        "Name": {"title": [{"text": {"content": t["Name"]}}]},
        "Status": {"select": {"name": t["Status"]}},
        "Priority": {"select": {"name": t["Priority"]}},
        "Due Date": {"date": {"start": t["Date"]}}
    }
    if i < len(lead_ids): p["Related Lead"] = {"relation": [{"id": lead_ids[i]}]}
    if i < len(job_ids): p["Related Job"] = {"relation": [{"id": job_ids[i]}]}
    add_page(t["Name"], tasks_db, p)

# 4. Populate CALENDAR
print("\n--- POPULATING CALENDAR ---")
cal_data = [
    {"Name": "Anthropic Screen", "Date": "2026-04-06T18:00:00Z", "Loc": "Google Meet", "Type": "Meeting"},
    {"Name": "ElevenLabs Deep Dive", "Date": "2026-04-07T14:30:00Z", "Loc": "Zoom", "Type": "Call"}
]
for c in cal_data:
    add_page(c["Name"], cal_db, {
        "Name": {"title": [{"text": {"content": c["Name"]}}]},
        "Date": {"date": {"start": c["Date"]}},
        "Location": {"rich_text": [{"text": {"content": c["Loc"]}}]},
        "Type": {"select": {"name": c["Type"]}}
    })

# 5. Populate FILES
print("\n--- POPULATING FILES ---")
file_data = [
    {"Name": "Master_Resume.pdf", "Type": "PDF", "Link": "https://drive.com/resume"},
    {"Name": "Mistral_Case_Study.doc", "Type": "Doc", "Link": "https://drive.com/mistral"}
]
for f in file_data:
    add_page(f["Name"], files_db, {
        "Name": {"title": [{"text": {"content": f["Name"]}}]},
        "Type": {"select": {"name": f["Type"]}},
        "Drive Link": {"url": f["Link"]}
    })

print("\n--- FINISHED ---")
