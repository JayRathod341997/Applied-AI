import os
from notion_client import Client
from dotenv import load_dotenv
from datetime import datetime, timedelta

load_dotenv()

client = Client(auth=os.getenv("NOTION_API_KEY"))

# Database IDs from .env
DB_IDS = {
    "tasks": os.getenv("NOTION_TASKS_DB"),
    "leads": os.getenv("NOTION_LEADS_DB"),
    "jobs": os.getenv("NOTION_JOBS_DB"),
    "grants": os.getenv("NOTION_GRANTS_DB"),
    "calendar": os.getenv("NOTION_CALENDAR_DB"),
    "files": os.getenv("NOTION_FILES_DB")
}

def get_db_props(db_id):
    try:
        db = client.databases.retrieve(database_id=db_id)
        return db.get("properties", {})
    except Exception as e:
        print(f"Error retrieving DB {db_id}: {e}")
        return {}

def populate_leads():
    db_id = DB_IDS['leads']
    if not db_id: return
    print("Populating Leads...")
    sample_leads = [
        {"Name": "John Doe", "Company": "TechInnovate", "Status": "New", "Email": "john@tech.com"},
        {"Name": "Jane Smith", "Company": "Global AI Hub", "Status": "Contacted", "Email": "jane@global.ai"},
        {"Name": "Bob Johnson", "Company": "Spark Digital", "Status": "Converted", "Email": "bob@spark.io"},
        {"Name": "Alice Green", "Company": "Green Energy Solutions", "Status": "New", "Email": "alice@green.co"},
        {"Name": "Chris Red", "Company": "Red Team Cyber", "Status": "Lost", "Email": "chris@redteam.com"},
        {"Name": "Samantha Blue", "Company": "Cloud Scale", "Status": "New", "Email": "samantha@cloud.com"}
    ]
    ids = []
    for lead in sample_leads:
        try:
            page = client.pages.create(
                parent={"database_id": db_id},
                properties={
                    "Name": {"title": [{"text": {"content": lead["Name"]}}]},
                    "Company": {"rich_text": [{"text": {"content": lead["Company"]}}]},
                    "Status": {"select": {"name": lead["Status"]}},
                    "Email": {"email": lead["Email"]}
                }
            )
            ids.append(page['id'])
        except Exception as e: print(f"  Error adding lead {lead['Name']}: {e}")
    return ids

def populate_jobs():
    db_id = DB_IDS['jobs']
    if not db_id: return
    print("Populating Jobs...")
    sample_jobs = [
        {"Title": "Senior AI Agent Dev", "Company": "Groq", "Status": "Interviewing", "Date": "2026-04-01"},
        {"Title": "Prompt Engineer", "Company": "Anthropic", "Status": "Applied", "Date": "2026-03-25"},
        {"Title": "Full Stack Dev", "Company": "Vercel", "Status": "Offer Received", "Date": "2026-03-30"},
        {"Title": "Machine Learning Engineer", "Company": "Google", "Status": "Interested", "Date": "2026-04-02"},
        {"Title": "Data Scientist", "Company": "Meta", "Status": "Rejected", "Date": "2026-03-15"}
    ]
    ids = []
    for job in sample_jobs:
        try:
            page = client.pages.create(
                parent={"database_id": db_id},
                properties={
                    "Title": {"title": [{"text": {"content": job["Title"]}}]},
                    "Company": {"rich_text": [{"text": {"content": job["Company"]}}]},
                    "Status": {"select": {"name": job["Status"]}},
                    "Application Date": {"date": {"start": job["Date"]}}
                }
            )
            ids.append(page['id'])
        except Exception as e: print(f"  Error adding job {job['Title']}: {e}")
    return ids

def populate_tasks(lead_ids, job_ids):
    db_id = DB_IDS['tasks']
    if not db_id: return
    print("Populating Tasks...")
    sample_tasks = [
        {"Name": "Follow up with John", "Status": "To Do", "Priority": "High", "Date": (datetime.now() + timedelta(days=1)).isoformat()[:10], "LeadIdx": 0},
        {"Name": "Submit Groq Assignment", "Status": "In Progress", "Priority": "High", "Date": (datetime.now() + timedelta(days=2)).isoformat()[:10], "JobIdx": 0},
        {"Name": "Onboarding Call spark", "Status": "Review", "Priority": "Medium", "Date": (datetime.now() + timedelta(days=3)).isoformat()[:10], "LeadIdx": 2},
        {"Name": "Draft Meta Response", "Status": "Done", "Priority": "Low", "Date": "2026-03-20", "JobIdx": 4},
        {"Name": "Setup Cloud Sync", "Status": "To Do", "Priority": "Medium", "Date": (datetime.now() + timedelta(days=5)).isoformat()[:10], "LeadIdx": 5},
        {"Name": "Vercel Offer Negotiation", "Status": "In Progress", "Priority": "High", "Date": (datetime.now() + timedelta(days=1)).isoformat()[:10], "JobIdx": 2}
    ]
    for task in sample_tasks:
        try:
            props = {
                "Name": {"title": [{"text": {"content": task["Name"]}}]},
                "Status": {"select": {"name": task["Status"]}},
                "Priority": {"select": {"name": task["Priority"]}},
                "Due Date": {"date": {"start": task["Date"]}}
            }
            if "LeadIdx" in task and task["LeadIdx"] < len(lead_ids):
                props["Related Lead"] = {"relation": [{"id": lead_ids[task["LeadIdx"]]}]}
            if "JobIdx" in task and task["JobIdx"] < len(job_ids):
                props["Related Job"] = {"relation": [{"id": job_ids[task["JobIdx"]]}]}
            
            client.pages.create(parent={"database_id": db_id}, properties=props)
        except Exception as e: print(f"  Error adding task {task['Name']}: {e}")

def populate_grants():
    db_id = DB_IDS['grants']
    if not db_id: return
    print("Populating Grants...")
    sample_grants = [
        {"Name": "OpenSource Innovation", "Amount": 50000, "Status": "Awarded", "Date": "2026-01-01"},
        {"Name": "AI for Earth", "Amount": 100000, "Status": "Submitted", "Date": "2026-05-15"},
        {"Name": "Privacy First Grant", "Amount": 25000, "Status": "Opportunity", "Date": "2026-04-30"},
        {"Name": "Decentralized Web Fund", "Amount": 75000, "Status": "Drafting", "Date": "2026-04-10"},
        {"Name": "Ethical AI Research", "Amount": 200000, "Status": "Rejected", "Date": "2025-12-15"}
    ]
    for grant in sample_grants:
        try:
            client.pages.create(
                parent={"database_id": db_id},
                properties={
                    "Name": {"title": [{"text": {"content": grant["Name"]}}]},
                    "Amount": {"number": grant["Amount"]},
                    "Status": {"select": {"name": grant["Status"]}},
                    "Deadline": {"date": {"start": grant["Date"]}}
                }
            )
        except Exception as e: print(f"  Error adding grant {grant['Name']}: {e}")

def populate_calendar():
    db_id = DB_IDS['calendar']
    if not db_id: return
    print("Populating Calendar...")
    sample_events = [
        {"Event": "Groq Interview Phase 1", "Date": "2026-04-05T10:00:00Z", "Location": "Zoom", "Type": "Meeting"},
        {"Event": "Sync Strategy Session", "Date": "2026-04-06T14:00:00Z", "Location": "Office", "Type": "Deep Work"},
        {"Event": "Catchup with Jane", "Date": "2026-04-07T09:00:00Z", "Location": "Coffee Shop", "Type": "Call"},
        {"Event": "Weekend Hike", "Date": "2026-04-11T08:00:00Z", "Location": "Mountains", "Type": "Personal"},
        {"Event": "Code Review - Sync Engine", "Date": "2026-04-03T16:00:00Z", "Location": "Virtual", "Type": "Deep Work"}
    ]
    for event in sample_events:
        try:
            client.pages.create(
                parent={"database_id": db_id},
                properties={
                    "Event": {"title": [{"text": {"content": event["Event"]}}]},
                    "Date": {"date": {"start": event["Date"]}},
                    "Location": {"rich_text": [{"text": {"content": event["Location"]}}]},
                    "Type": {"select": {"name": event["Type"]}}
                }
            )
        except Exception as e: print(f"  Error adding event {event['Event']}: {e}")

def populate_files():
    db_id = DB_IDS['files']
    if not db_id: return
    print("Populating Files...")
    
    # Check actual property names
    props = get_db_props(db_id)
    title_key = next((k for k, v in props.items() if v["type"] == "title"), "Filename")
    type_key = next((k for k, v in props.items() if v["type"] == "select"), "Type")
    url_key = next((k for k, v in props.items() if v["type"] == "url"), "Drive Link")
    
    print(f"  Using properties: {title_key}, {type_key}, {url_key}")

    sample_files = [
        {"Name": "Proposal_V1.pdf", "Type": "PDF", "Link": "https://drive.google.com/doc/1"},
        {"Name": "Architecture_Diagram.png", "Type": "Image", "Link": "https://drive.google.com/doc/2"},
        {"Name": "OAuth_Credentials.json", "Type": "Archive", "Link": "https://drive.google.com/doc/3"},
        {"Name": "Sync_Engine_Spec.docx", "Type": "Doc", "Link": "https://drive.google.com/doc/4"},
        {"Name": "User_Feedback_Results.pdf", "Type": "PDF", "Link": "https://drive.google.com/doc/5"}
    ]
    for file in sample_files:
        try:
            client.pages.create(
                parent={"database_id": db_id},
                properties={
                    title_key: {"title": [{"text": {"content": file["Name"]}}]},
                    type_key: {"select": {"name": file["Type"]}},
                    url_key: {"url": file["Link"]}
                }
            )
        except Exception as e: print(f"  Error adding file {file['Name']}: {e}")

if __name__ == "__main__":
    l_ids = populate_leads()
    j_ids = populate_jobs()
    populate_tasks(l_ids or [], j_ids or [])
    populate_grants()
    populate_calendar()
    populate_files()
