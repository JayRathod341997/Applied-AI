import os
from notion_client import Client
from dotenv import load_dotenv

load_dotenv()
client = Client(auth=os.getenv("NOTION_API_KEY"))
db_id = os.getenv("NOTION_LEADS_DB")

print(f"Using DB ID: {db_id}")

try:
    db = client.databases.retrieve(database_id=db_id)
    print(f"Retrieved DB: {db['title'][0]['text']['content']}")
except Exception as e:
    print(f"FAILED TO RETRIEVE DB: {e}")
    exit(1)

sample_leads = [
    {"Name": "John Doe", "Company": "TechInnovate", "Status": "New", "Email": "john@tech.com"},
    {"Name": "Jane Smith", "Company": "Global AI Hub", "Status": "Contacted", "Email": "jane@global.ai"},
    {"Name": "Bob Johnson", "Company": "Spark Digital", "Status": "Converted", "Email": "bob@spark.io"},
    {"Name": "Alice Green", "Company": "Green Energy Solutions", "Status": "New", "Email": "alice@green.co"},
    {"Name": "Chris Red", "Company": "Red Team Cyber", "Status": "Lost", "Email": "chris@redteam.com"},
    {"Name": "Samantha Blue", "Company": "Cloud Scale", "Status": "New", "Email": "samantha@cloud.com"}
]

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
        print(f"Success adding Lead: {lead['Name']}")
    except Exception as e:
        print(f"ERROR adding Lead {lead['Name']}: {e}")
