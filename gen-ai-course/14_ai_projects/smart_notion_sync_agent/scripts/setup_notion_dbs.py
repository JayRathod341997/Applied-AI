import os
from notion_client import Client
from dotenv import load_dotenv
import time
from datetime import datetime, timedelta

# Load environment variables
load_dotenv()

NOTION_API_KEY = os.getenv("NOTION_API_KEY")
PAGE_ID = "33738521f62580d8baf3cee6e1277e2d" # From user's URL

if not NOTION_API_KEY:
    print("Error: NOTION_API_KEY not found in .env")
    exit(1)

client = Client(auth=NOTION_API_KEY)

def create_database(parent_page_id, title, properties):
    print(f"Creating database: {title}...")
    try:
        db = client.databases.create(
            parent={"type": "page_id", "page_id": parent_page_id},
            title=[{"text": {"content": title}}],
            properties=properties
        )
        print(f"Success! Database ID: {db['id']}")
        return db['id']
    except Exception as e:
        print(f"Failed to create {title}: {e}")
        return None

# --- DATABASE DEFINITIONS ---

# 1. Leads
leads_props = {
    "Name": {"title": {}},
    "Company": {"rich_text": {}},
    "Status": {"select": {"options": [
        {"name": "New", "color": "blue"},
        {"name": "Contacted", "color": "yellow"},
        {"name": "Converted", "color": "green"},
        {"name": "Lost", "color": "gray"}
    ]}},
    "Email": {"email": {}}
}

# 2. Jobs
jobs_props = {
    "Title": {"title": {}},
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

# 3. Tasks (Relations will be added later if needed, but easier to create some first)
tasks_props = {
    "Name": {"title": {}},
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
    "Due Date": {"date": {}}
}

# 4. Grants
grants_props = {
    "Name": {"title": {}},
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

# 5. Calendar
calendar_props = {
    "Event": {"title": {}},
    "Date": {"date": {}},
    "Location": {"rich_text": {}},
    "Type": {"select": {"options": [
        {"name": "Meeting", "color": "blue"},
        {"name": "Call", "color": "yellow"},
        {"name": "Personal", "color": "green"},
        {"name": "Deep Work", "color": "purple"}
    ]}}
}

# 6. Files
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

def main():
    db_ids = {}

    # Create base databases
    db_ids['leads'] = create_database(PAGE_ID, "Leads Command Center", leads_props)
    db_ids['jobs'] = create_database(PAGE_ID, "Job Application Tracker", jobs_props)
    db_ids['grants'] = create_database(PAGE_ID, "Grants & Funding", grants_props)
    db_ids['calendar'] = create_database(PAGE_ID, "Master Sync Calendar", calendar_props)
    db_ids['files'] = create_database(PAGE_ID, "Sync File Archive", files_props)

    # Create Tasks with relations
    if db_ids['leads'] and db_ids['jobs']:
        tasks_props["Related Lead"] = {
            "relation": {
                "database_id": db_ids['leads'],
                "type": "dual_property",
                "dual_property": {"synced_property_name": "Related Tasks"}
            }
        }
        tasks_props["Related Job"] = {
            "relation": {
                "database_id": db_ids['jobs'],
                "type": "dual_property",
                "dual_property": {"synced_property_name": "Related Tasks"}
            }
        }
    
    db_ids['tasks'] = create_database(PAGE_ID, "Notion Tasks Agent", tasks_props)

    print("\n--- Summary of Created Databases ---")
    for key, id in db_ids.items():
        print(f"{key}: {id}")

    # POPULATE DATA
    print("\nPopulating sample data...")

    # LEADS
    sample_leads = [
        {"Name": "John Doe", "Company": "TechInnovate", "Status": "New", "Email": "john@tech.com"},
        {"Name": "Jane Smith", "Company": "Global AI Hub", "Status": "Contacted", "Email": "jane@global.ai"},
        {"Name": "Bob Johnson", "Company": "Spark Digital", "Status": "Converted", "Email": "bob@spark.io"},
        {"Name": "Alice Green", "Company": "Green Energy Solutions", "Status": "New", "Email": "alice@green.co"},
        {"Name": "Chris Red", "Company": "Red Team Cyber", "Status": "Lost", "Email": "chris@redteam.com"},
        {"Name": "Samantha Blue", "Company": "Cloud Scale", "Status": "New", "Email": "samantha@cloud.com"}
    ]
    lead_ids = []
    for lead in sample_leads:
        try:
            page = client.pages.create(
                parent={"database_id": db_ids['leads']},
                properties={
                    "Name": {"title": [{"text": {"content": lead["Name"]}}]},
                    "Company": {"rich_text": [{"text": {"content": lead["Company"]}}]},
                    "Status": {"select": {"name": lead["Status"]}},
                    "Email": {"email": lead["Email"]}
                }
            )
            lead_ids.append(page['id'])
        except Exception as e: print(f"Error adding lead: {e}")

    # JOBS
    sample_jobs = [
        {"Title": "Senior AI Agent Dev", "Company": "Groq", "Status": "Interviewing", "Date": "2026-04-01"},
        {"Title": "Prompt Engineer", "Company": "Anthropic", "Status": "Applied", "Date": "2026-03-25"},
        {"Title": "Full Stack Dev", "Company": "Vercel", "Status": "Offer Received", "Date": "2026-03-30"},
        {"Title": "Machine Learning Engineer", "Company": "Google", "Status": "Interested", "Date": "2026-04-02"},
        {"Title": "Data Scientist", "Company": "Meta", "Status": "Rejected", "Date": "2026-03-15"}
    ]
    job_ids = []
    for job in sample_jobs:
        try:
            page = client.pages.create(
                parent={"database_id": db_ids['jobs']},
                properties={
                    "Title": {"title": [{"text": {"content": job["Title"]}}]},
                    "Company": {"rich_text": [{"text": {"content": job["Company"]}}]},
                    "Status": {"select": {"name": job["Status"]}},
                    "Application Date": {"date": {"start": job["Date"]}}
                }
            )
            job_ids.append(page['id'])
        except Exception as e: print(f"Error adding job: {e}")

    # TASKS (with relations)
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
            
            client.pages.create(parent={"database_id": db_ids['tasks']}, properties=props)
        except Exception as e: print(f"Error adding task: {e}")

    # GRANTS
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
                parent={"database_id": db_ids['grants']},
                properties={
                    "Name": {"title": [{"text": {"content": grant["Name"]}}]},
                    "Amount": {"number": grant["Amount"]},
                    "Status": {"select": {"name": grant["Status"]}},
                    "Deadline": {"date": {"start": grant["Date"]}}
                }
            )
        except Exception as e: print(f"Error adding grant: {e}")

    # CALENDAR
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
                parent={"database_id": db_ids['calendar']},
                properties={
                    "Event": {"title": [{"text": {"content": event["Event"]}}]},
                    "Date": {"date": {"start": event["Date"]}},
                    "Location": {"rich_text": [{"text": {"content": event["Location"]}}]},
                    "Type": {"select": {"name": event["Type"]}}
                }
            )
        except Exception as e: print(f"Error adding event: {e}")

    # FILES
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
                parent={"database_id": db_ids['files']},
                properties={
                    "Filename": {"title": [{"text": {"content": file["Name"]}}]},
                    "Type": {"select": {"name": file["Type"]}},
                    "Drive Link": {"url": file["Link"]}
                }
            )
        except Exception as e: print(f"Error adding file: {e}")

    # UPDATE .env
    print("\nUpdating .env file with new database IDs...")
    update_env(db_ids)

def update_env(db_ids):
    env_path = ".env"
    try:
        with open(env_path, 'r') as f:
            lines = f.readlines()
        
        new_lines = []
        mapping = {
            "NOTION_TASKS_DB": db_ids.get('tasks'),
            "NOTION_LEADS_DB": db_ids.get('leads'),
            "NOTION_JOBS_DB": db_ids.get('jobs'),
            "NOTION_GRANTS_DB": db_ids.get('grants'),
            "NOTION_CALENDAR_DB": db_ids.get('calendar'),
            "NOTION_FILES_DB": db_ids.get('files')
        }
        
        updated_keys = set()
        for line in lines:
            found = False
            for key, val in mapping.items():
                if line.startswith(f"{key}=") and val:
                    new_lines.append(f"{key}={val.replace('-', '')}\n")
                    updated_keys.add(key)
                    found = True
                    break
            if not found:
                new_lines.append(line)
        
        # Add keys that weren't in the file
        for key, val in mapping.items():
            if key not in updated_keys and val:
                new_lines.append(f"{key}={val.replace('-', '')}\n")

        with open(env_path, 'w') as f:
            f.writelines(new_lines)
        print("Success! .env file updated.")
    except Exception as e:
        print(f"Failed to update .env: {e}")

if __name__ == "__main__":
    main()
