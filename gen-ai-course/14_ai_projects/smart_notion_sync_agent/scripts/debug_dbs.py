import os
from notion_client import Client
from dotenv import load_dotenv

load_dotenv()
client = Client(auth=os.getenv("NOTION_API_KEY"))
dbs = ["NOTION_TASKS_DB", "NOTION_LEADS_DB", "NOTION_JOBS_DB", "NOTION_GRANTS_DB", "NOTION_CALENDAR_DB", "NOTION_FILES_DB"]

for db_env in dbs:
    id = os.getenv(db_env)
    if id:
        try:
            db = client.databases.retrieve(database_id=id)
            print(f"{db_env} ({id}): {db.keys()}")
        except Exception as e:
            print(f"{db_env} ({id}): Error - {e}")
