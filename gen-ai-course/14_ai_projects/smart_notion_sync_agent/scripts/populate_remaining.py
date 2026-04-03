import requests
import os
import json
from dotenv import load_dotenv
from datetime import datetime, timedelta

load_dotenv()
NOTION_API_KEY = os.getenv("NOTION_API_KEY")

headers = {
    "Authorization": f"Bearer {NOTION_API_KEY}",
    "Notion-Version": "2022-06-28",
    "Content-Type": "application/json"
}

def update_db_props(db_id, props):
    r = requests.patch(f"https://api.notion.com/v1/databases/{db_id}", headers=headers, json={"properties": props})
    return r.status_code == 200, r.text

def add_page(db_id, props):
    r = requests.post("https://api.notion.com/v1/pages", headers=headers, json={
        "parent": {"database_id": db_id},
        "properties": props
    })
    return r.status_code == 200, r.text

def get_pages(db_id):
    r = requests.post(f"https://api.notion.com/v1/databases/{db_id}/query", headers=headers)
    if r.status_code == 200:
        return r.json().get("results", [])
    return []

# 1. JOBS
jobs_id = os.getenv("NOTION_JOBS_DB")
jobs_props_update = {
    "Company": {"rich_text": {}},
    "Status": {"select": {"options": [
        {"name": "Applied"}, {"name": "Interviewing"}, {"name": "Offer Received"}, {"name": "Rejected"}
    ]}},
    "Application Date": {"date": {}}
}
update_db_props(jobs_id, jobs_props_update)

# 2. CALENDAR
calendar_id = os.getenv("NOTION_CALENDAR_DB")
calendar_props_update = {
    "Location": {"rich_text": {}},
    "Type": {"select": {"options": [
        {"name": "Meeting"}, {"name": "Call"}, {"name": "Deep Work"}
    ]}},
    "Date": {"date": {}}
}
update_db_props(calendar_id, calendar_props_update)

# 3. FILES
files_id = os.getenv("NOTION_FILES_DB")
files_props_update = {
    "Type": {"select": {"options": [
        {"name": "PDF"}, {"name": "Doc"}, {"name": "Image"}
    ]}},
    "Drive Link": {"url": {}}
}
update_db_props(files_id, files_props_update)

# Fetch existing Leads and Jobs IDs for relation in Tasks
leads_pages = get_pages(os.getenv("NOTION_LEADS_DB"))
lead_ids = [p["id"] for p in leads_pages]

# Data for JOBS
sample_jobs = [
    {"Name": "AI Engineer", "Company": "NVIDIA", "Status": "Applied", "Date": "2026-04-01"},
    {"Name": "Product Manager", "Company": "OpenAI", "Status": "Interviewing", "Date": "2026-03-28"},
    {"Name": "Research Scientist", "Company": "DeepMind", "Status": "Offer Received", "Date": "2026-03-30"}
]
print("Populating Jobs...")
job_ids = []
for job in sample_jobs:
    success, resp = add_page(jobs_id, {
        "Name": {"title": [{"text": {"content": job["Name"]}}]},
        "Company": {"rich_text": [{"text": {"content": job["Company"]}}]},
        "Status": {"select": {"name": job["Status"]}},
        "Application Date": {"date": {"start": job["Date"]}}
    })
    if success:
        job_ids.append(json.loads(resp)["id"])
        print(f"  Added Job: {job['Name']}")

# Data for TASKS
tasks_id = os.getenv("NOTION_TASKS_DB")
sample_tasks = [
    {"Name": "Prep for NVIDIA Interview", "Status": "In Progress", "Priority": "High", "Date": (datetime.now() + timedelta(days=1)).isoformat()[:10]},
    {"Name": "Send Followup to Lead", "Status": "To Do", "Priority": "Medium", "Date": (datetime.now() + timedelta(days=2)).isoformat()[:10]}
]
print("Populating Tasks...")
for i, task in enumerate(sample_tasks):
    props = {
        "Name": {"title": [{"text": {"content": task["Name"]}}]},
        "Status": {"select": {"name": task["Status"]}},
        "Priority": {"select": {"name": task["Priority"]}},
        "Due Date": {"date": {"start": task["Date"]}}
    }
    if i < len(lead_ids):
        props["Related Lead"] = {"relation": [{"id": lead_ids[i]}]}
    if i < len(job_ids):
        props["Related Job"] = {"relation": [{"id": job_ids[i]}]}
    success, _ = add_page(tasks_id, props)
    if success: print(f"  Added Task: {task['Name']}")

# Data for CALENDAR
sample_events = [
    {"Name": "NVIDIA Interview", "Date": "2026-04-05T15:00:00Z", "Location": "Teams", "Type": "Meeting"},
    {"Name": "OpenAI Strategy Call", "Date": "2026-04-06T10:00:00Z", "Location": "Office", "Type": "Call"}
]
print("Populating Calendar...")
for event in sample_events:
    success, _ = add_page(calendar_id, {
        "Name": {"title": [{"text": {"content": event["Name"]}}]},
        "Date": {"date": {"start": event["Date"]}},
        "Location": {"rich_text": [{"text": {"content": event["Location"]}}]},
        "Type": {"select": {"name": event["Type"]}}
    })
    if success: print(f"  Added Event: {event['Name']}")

# Data for FILES
sample_files = [
    {"Name": "Resume_2026.pdf", "Type": "PDF", "Link": "https://drive.google.com/resume"},
    {"Name": "Design_Doc.docx", "Type": "Doc", "Link": "https://drive.google.com/design"}
]
print("Populating Files...")
for file in sample_files:
    success, _ = add_page(files_id, {
        "Name": {"title": [{"text": {"content": file["Name"]}}]},
        "Type": {"select": {"name": file["Type"]}},
        "Drive Link": {"url": file["Link"]}
    })
    if success: print(f"  Added File: {file['Name']}")

print("\n--- Remaining tables populated ---")
