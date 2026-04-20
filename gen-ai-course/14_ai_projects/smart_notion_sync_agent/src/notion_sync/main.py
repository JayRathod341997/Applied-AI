from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import time
import logging
import asyncio

from .models import SyncRequest, SyncResponse, HealthStatus, SlackEventRequest
from .pipelines.notion_sync import SyncEngine
from .pipelines.slack import invoke_slack_to_notion, invoke_notion_to_slack
from .utils.logger import setup_logger
from .config import settings

logger = setup_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    async def loop():
        while True:
            await asyncio.to_thread(invoke_notion_to_slack)
            await asyncio.sleep(10)

    task = asyncio.create_task(loop())
    yield
    task.cancel()


app = FastAPI(
    title="Smart Notion Sync Agent",
    description="Bi-directional sync between Google Workspace and Notion with LLM conflict resolution",
    version="0.1.0",
    use_enum_values=True,
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.middleware("http")
async def add_process_time_header(request: Request, call_next):
    start = time.perf_counter()
    response = await call_next(request)
    elapsed = time.perf_counter() - start
    response.headers["X-Process-Time"] = f"{elapsed:.4f}s"
    return response


sync_engine = SyncEngine()


@app.get("/health")
async def health():
    return {
        "status": "ok",
        "service": "smart-notion-sync-agent",
        "notion_configured": bool(settings.notion_api_key),
        "google_configured": bool(settings.google_service_account_json),
    }


@app.post("/sync/trigger")
async def trigger_sync(request: SyncRequest):
    try:
        sources = request.sources or ["google_calendar", "google_drive", "gmail"]
        results = await sync_engine.full_sync(sources, request.direction)
        return {
            "status": "completed",
            "sync_results": results,
            "health": {"all_systems_healthy": True},
        }
    except Exception as exc:
        logger.exception(f"Sync failed: {exc}")
        raise HTTPException(status_code=500, detail=str(exc))


@app.get("/sync/status")
async def sync_status():
    return {
        "integrations": {
            "notion": {"configured": bool(settings.notion_api_key)},
            "google_calendar": {
                "configured": bool(settings.google_service_account_json)
            },
            "slack": {"configured": bool(settings.slack_bot_token)},
        }
    }


@app.post("/slack/events")
async def slack_events(payload: SlackEventRequest, request: Request):
    # Slack retries on timeout — ignore retried deliveries
    if request.headers.get("X-Slack-Retry-Reason") == "http_timeout":
        return {"ok": True}

    if payload.type == "url_verification":
        return {"challenge": payload.challenge}

    event = payload.event or {}
    if (
        event.get("type") == "message"
        and not event.get("bot_id")
        and not event.get("subtype")
    ):
        asyncio.create_task(asyncio.to_thread(invoke_slack_to_notion, event))

    return {"ok": True}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8019)
