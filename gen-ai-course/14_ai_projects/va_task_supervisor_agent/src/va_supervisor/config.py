from pydantic_settings import BaseSettings
from functools import lru_cache
from pathlib import Path


class Settings(BaseSettings):
    groq_api_key: str = ""
    groq_model_primary: str = "llama-3.3-70b-versatile"
    groq_model_fast: str = "llama-3.1-8b-instant"
    notion_api_key: str = ""
    notion_tasks_db: str = ""
    notion_va_profiles_db: str = ""
    slack_webhook_url: str = ""
    slack_bot_token: str = ""
    sendgrid_api_key: str = ""
    app_env: str = "development"
    log_level: str = "INFO"

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
