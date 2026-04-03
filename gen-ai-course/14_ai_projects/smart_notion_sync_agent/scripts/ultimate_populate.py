import requests
import os
import json
import time
from dotenv import load_dotenv
from datetime import datetime, timedelta

load_dotenv()
NOTION_API_KEY = os.getenv("NOTION_API_KEY")
PAGE_ID = "33738521f62580d8baf3cee6e1277e2d"

headers = {
    "Authorization": f"Bearer {NOTION_API_KEY}",
    "Notion-Version": "2022-06-28",
    "Content-Type": "application/json"
}

def update_db_props(db_id, props):
    print(f"Updating properties for {db_id}...")
    r = requests.patch(f"https://api.notion.com/v1/databases/{db_id}", headers=headers, json={"properties": props})
    if r.status_code == 200:
        print(f"  Update successful for {db_id}")
        return True
    else:
        print(f"  Update failed for {db_id}: {r.text}")
        return False

def add_page(db_id, props):
    r = requests.post("https://api.notion.com/v1/pages", headers=headers, json={
        "parent": {"database_id": db_id},
        "properties": props
    })
    return r.status_code == 200, r.text

# 1. LEADS
leads_id = os.getenv("NOTION_LEADS_DB")
leads_props = {
    "Company": {"rich_text": {}},
    "Status": {"select": {"options": [
        {"name": "New", "color": "blue"},
        {"name": "Contacted", "color": "yellow"},
        {"name": "Converted", "color": "green"},
        {"name": "Lost", "color": "gray"}
    ]}},
    "Email": {"email": {}}
}
update_db_props(leads_id, leads_props)

sample_leads = [
    {"Name": "John Doe", "Company": "TechInnovate", "Status": "New", "Email": "john@tech.com"},
    {"Name": "Jane Smith", "Company": "Global AI Hub", "Status": "Contacted", "Email": "jane@global.ai"},
    {"Name": "Bob Johnson", "Company": "Spark Digital", "Status": "Converted", "Email": "bob@spark.io"},
    {"Name": "Alice Green", "Company": "Green Energy Solutions", "Status": "New", "Email": "alice@green.co"},
    {"Name": "Chris Red", "Company": "Red Team Cyber", "Status": "Lost", "Email": "chris@redteam.com"},
    {"Name": "Samantha Blue", "Company": "Cloud Scale", "Status": "New", "Email": "samantha@cloud.com"}
]
lead_page_ids = []
print("Populating Leads...")
for lead in sample_leads:
    success, resp = add_page(leads_id, {
        "Name": {"title": [{"text": {"content": lead["Name"]}}]},
        "Company": {"rich_text": [{"text": {"content": lead["Company"]}}]},
        "Status": {"select": {"name": lead["Status"]}},
        "Email": {"email": lead["Email"]}
    })
    if success:
        lead_page_ids.append(json.loads(resp)['id'])
        print(f"  Added {lead['Name']}")

# 2. JOBS
jobs_id = os.getenv("NOTION_JOBS_DB")
jobs_props = {
    "Company": {"rich_text": {}},
    "Status": {"select": {"options": [
        {"name": "Interested", "color": "blue"},
        {"name": "Applied", "color": "yellow"},
        {"name": "Interviewing", "color": "purple"},
        {"name": "Offer Received", "color": "green"},
        {"name": "Rejected", "color": "red"}
    ]}},
    "Application Date": {"date": {}}
}
update_db_props(jobs_id, jobs_props)

sample_jobs = [
    {"Title": "Senior AI Agent Dev", "Company": "Groq", "Status": "Interviewing", "Date": "2026-04-01"},
    {"Title": "Prompt Engineer", "Company": "Anthropic", "Status": "Applied", "Date": "2026-03-25"},
    {"Title": "Full Stack Dev", "Company": "Vercel", "Status": "Offer Received", "Date": "2026-03-30"},
    {"Title": "Machine Learning Engineer", "Company": "Google", "Status": "Interested", "Date": "2026-04-02"},
    {"Title": "Data Scientist", "Company": "Meta", "Status": "Rejected", "Date": "2026-03-15"}
]
job_page_ids = []
print("Populating Jobs...")
for job in sample_jobs:
    success, resp = add_page(jobs_id, {
        "Title": {"title": [{"text": {"content": job["Title"]}}]},
        "Company": {"rich_text": [{"text": {"content": job["Company"]}}]},
        "Status": {"select": {"name": job["Status"]}},
        "Application Date": {"date": {"start": job["Date"]}}
    })
    if success:
        job_page_ids.append(json.loads(resp)['id'])
        print(f"  Added {job['Title']}")

# 3. TASKS
tasks_id = os.getenv("NOTION_TASKS_DB")
tasks_props = {
    "Status": {"select": {"options": [
        {"name": "To Do", "color": "gray"},
        {"name": "In Progress", "color": "blue"},
        {"name": "Review", "color": "yellow"},
        {"name": "Done", "color": "green"}
    ]}},
    "Priority": {"select": {"options": [
        {"name": "High", "color": "red"},
        {"name": "Medium", "color": "orange"},
        {"name": "Low", "color": "blue"}
    ]}},
    "Due Date": {"date": {}},
    "Related Lead": {"relation": {"database_id": leads_id}},
    "Related Job": {"relation": {"database_id": jobs_id}}
}
update_db_props(tasks_id, tasks_props)

sample_tasks = [
    {"Name": "Follow up with John", "Status": "To Do", "Priority": "High", "Date": (datetime.now() + timedelta(days=1)).isoformat()[:10], "LeadIdx": 0},
    {"Name": "Submit Groq Assignment", "Status": "In Progress", "Priority": "High", "Date": (datetime.now() + timedelta(days=2)).isoformat()[:10], "JobIdx": 0},
    {"Name": "Onboarding Call spark", "Status": "Review", "Priority": "Medium", "Date": (datetime.now() + timedelta(days=3)).isoformat()[:10], "LeadIdx": 2},
    {"Name": "Draft Meta Response", "Status": "Done", "Priority": "Low", "Date": "2026-03-20", "JobIdx": 4},
    {"Name": "Setup Cloud Sync", "Status": "To Do", "Priority": "Medium", "Date": (datetime.now() + timedelta(days=5)).isoformat()[:10], "LeadIdx": 5},
    {"Name": "Vercel Offer Negotiation", "Status": "In Progress", "Priority": "High", "Date": (datetime.now() + timedelta(days=1)).isoformat()[:10], "JobIdx": 2}
]
print("Populating Tasks...")
for task in sample_tasks:
    props = {
        "Name": {"title": [{"text": {"content": task["Name"]}}]},
        "Status": {"select": {"name": task["Status"]}},
        "Priority": {"select": {"name": task["Priority"]}},
        "Due Date": {"date": {"start": task["Date"]}}
    }
    if "LeadIdx" in task and task["LeadIdx"] < len(lead_page_ids):
        props["Related Lead"] = {"relation": [{"id": lead_page_ids[task["LeadIdx"]]}]}
    if "JobIdx" in task and task["JobIdx"] < len(job_page_ids):
        props["Related Job"] = {"relation": [{"id": job_page_ids[task["JobIdx"]]}]}
    
    success, resp = add_page(tasks_id, props)
    if success: print(f"  Added Task: {task['Name']}")

# 4. GRANTS
grants_id = os.getenv("NOTION_GRANTS_DB")
grants_props = {
    "Amount": {"number": {"format": "dollar"}},
    "Status": {"select": {"options": [
        {"name": "Opportunity", "color": "blue"},
        {"name": "Drafting", "color": "yellow"},
        {"name": "Submitted", "color": "purple"},
        {"name": "Awarded", "color": "green"},
        {"name": "Declined", "color": "red"}
    ]}},
    "Deadline": {"date": {}}
}
update_db_props(grants_id, grants_props)

sample_grants = [
    {"Name": "OpenSource Innovation", "Amount": 50000, "Status": "Awarded", "Date": "2026-01-01"},
    {"Name": "AI for Earth", "Amount": 100000, "Status": "Submitted", "Date": "2026-05-15"},
    {"Name": "Privacy First Grant", "Amount": 25000, "Status": "Opportunity", "Date": "2026-04-30"},
    {"Name": "Decentralized Web Fund", "Amount": 75000, "Status": "Drafting", "Date": "2026-04-10"},
    {"Name": "Ethical AI Research", "Amount": 200000, "Status": "Rejected", "Date": "2025-12-15"}
]
print("Populating Grants...")
for grant in sample_grants:
    success, resp = add_page(grants_id, {
        "Name": {"title": [{"text": {"content": grant["Name"]}}]},
        "Amount": {"number": grant["Amount"]},
        "Status": {"select": {"name": grant["Status"]}},
        "Deadline": {"date": {"start": grant["Date"]}}
    })
    if success: print(f"  Added Grant: {grant['Name']}")

# 5. CALENDAR
calendar_id = os.getenv("NOTION_CALENDAR_DB")
calendar_props = {
    "Location": {"rich_text": {}},
    "Type": {"select": {"options": [
        {"name": "Meeting", "color": "blue"},
        {"name": "Call", "color": "yellow"},
        {"name": "Personal", "color": "green"},
        {"name": "Deep Work", "color": "purple"}
    ]}},
    "Date": {"date": {}}
}
update_db_props(calendar_id, calendar_props)

sample_events = [
    {"Event": "Groq Interview Phase 1", "Date": "2026-04-05T10:00:00Z", "Location": "Zoom", "Type": "Meeting"},
    {"Event": "Sync Strategy Session", "Date": "2026-04-06T14:00:00Z", "Location": "Office", "Type": "Deep Work"},
    {"Event": "Catchup with Jane", "Date": "2026-04-07T09:00:00Z", "Location": "Coffee Shop", "Type": "Call"},
    {"Event": "Weekend Hike", "Date": "2026-04-11T08:00:00Z", "Location": "Mountains", "Type": "Personal"},
    {"Event": "Code Review - Sync Engine", "Date": "2026-04-03T16:00:00Z", "Location": "Virtual", "Type": "Deep Work"}
]
print("Populating Calendar...")
for event in sample_events:
    success, resp = add_page(calendar_id, {
        "Event": {"title": [{"text": {"content": event["Event"]}}]},
        "Date": {"date": {"start": event["Date"]}},
        "Location": {"rich_text": [{"text": {"content": event["Location"]}}]},
        "Type": {"select": {"name": event["Type"]}}
    })
    if success: print(f"  Added Meeting: {event['Event']}")

# 6. FILES
files_id = os.getenv("NOTION_FILES_DB")
files_props = {
    "Filename": {"title": {}},
    "Type": {"select": {"options": [
        {"name": "PDF", "color": "red"},
        {"name": "Doc", "color": "blue"},
        {"name": "Image", "color": "green"},
        {"name": "Archive", "color": "orange"}
    ]}},
    "Drive Link": {"url": {}}
}
update_db_props(files_id, files_props)

sample_files = [
    {"Name": "Proposal_V1.pdf", "Type": "PDF", "Link": "https://drive.google.com/doc/1"},
    {"Name": "Architecture_Diagram.png", "Type": "Image", "Link": "https://drive.google.com/doc/2"},
    {"Name": "OAuth_Credentials.json", "Type": "Archive", "Link": "https://drive.google.com/doc/3"},
    {"Name": "Sync_Engine_Spec.docx", "Type": "Doc", "Link": "https://drive.google.com/doc/4"},
    {"Name": "User_Feedback_Results.pdf", "Type": "PDF", "Link": "https://drive.google.com/doc/5"}
]
print("Populating Files...")
for file in sample_files:
    success, resp = add_page(files_id, {
        "Filename": {"title": [{"text": {"content": file["Name"]}}]},
        "Type": {"select": {"name": file["Type"]}},
        "Drive Link": {"url": file["Link"]}
    })
    if success: print(f"  Added File: {file['Name']}")

print("\n--- ALL DONE ---")
