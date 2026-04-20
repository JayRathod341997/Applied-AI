from pydantic_settings import BaseSettings
from functools import lru_cache
from pathlib import Path


class Settings(BaseSettings):
    # Groq
    groq_api_key: str = ""
    groq_model_primary: str = "llama-3.3-70b-versatile"

    # Notion
    notion_api_key: str = ""
    notion_tasks_db: str = ""
    notion_leads_db: str = ""
    notion_jobs_db: str = ""
    notion_grants_db: str = ""
    notion_calendar_db: str = ""
    notion_files_db: str = ""
    notion_notes_db: str = ""

    # Notion Property Names
    notion_title_key: str = "Name"
    notion_start_date_key: str = "Start Date"
    notion_end_date_key: str = "End Date"
    notion_location_key: str = "Location"
    notion_type_key: str = "Type"

    # Google
    google_service_account_json: str = ""
    google_calendar_id: str = "primary"

    # Slack
    slack_webhook_url: str = ""
    slack_bot_token: str = ""
    slack_signing_secret: str = ""
    slack_sync_channel: str = ""

    # Application
    app_env: str = "development"
    log_level: str = "INFO"

    # Hidden property name used to store Google Calendar event ID in Notion
    SYNC_ID_PROPERTY: str = "Sync ID"
    model_config = {
        "env_file": str(Path(__file__).parents[2] / ".env"),
        "env_file_encoding": "utf-8",
        "case_sensitive": False,
        "extra": "ignore",
    }


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
