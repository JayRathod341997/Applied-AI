from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
import time

from .models import ClassifyRequest, ClassifyResponse, SyncResponse
from .pipelines.email_pipeline import EmailPipeline
from .utils.logger import setup_logger
from .config import settings

logger = setup_logger(__name__)

app = FastAPI(
    title="AI Inbox Cleaner",
    description="Gmail email classifier and auto-organizer with LLM categorization",
    version="0.1.0",
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


pipeline = EmailPipeline()


@app.get("/health")
async def health():
    return {
        "status": "ok",
        "service": "ai-inbox-cleaner",
        "gmail_configured": bool(settings.google_service_account_json),
    }


@app.post("/classify", response_model=ClassifyResponse)
async def classify_email(request: ClassifyRequest):
    try:
        result = await pipeline.process_email(
            {
                "from": request.from_address,
                "subject": request.subject,
                "body": request.body,
                "id": request.email_id or "manual",
            }
        )
        return ClassifyResponse(**result)
    except Exception as exc:
        logger.exception(f"Classification failed: {exc}")
        raise HTTPException(status_code=500, detail=str(exc))


@app.post("/sync/trigger")
async def trigger_sync():
    try:
        results = await pipeline.sync_new_emails()
        return {
            "status": "completed",
            "emails_processed": len(results),
            "classifications": results,
        }
    except Exception as exc:
        logger.exception(f"Sync failed: {exc}")
        raise HTTPException(status_code=500, detail=str(exc))


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8018)
