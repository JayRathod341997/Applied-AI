from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
import time

from .models import LeadInput, LeadResponse
from .pipelines.lead_pipeline import LeadPipeline
from .utils.logger import setup_logger
from .config import settings

logger = setup_logger(__name__)

app = FastAPI(
    title="Real Estate CRM Assistant",
    description="Real estate lead qualification and automated follow-up sequences",
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


pipeline = LeadPipeline()


@app.get("/health")
async def health():
    return {
        "status": "ok",
        "service": "real-estate-crm-agent",
        "twilio_configured": bool(settings.twilio_account_sid),
        "sendgrid_configured": bool(settings.sendgrid_api_key),
    }


@app.post("/webhook/lead", response_model=LeadResponse)
async def receive_lead(lead: LeadInput):
    try:
        result = await pipeline.process_lead(lead.model_dump())
        return LeadResponse(**result)
    except Exception as exc:
        logger.exception(f"Lead processing failed: {exc}")
        raise HTTPException(status_code=500, detail=str(exc))


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8013)
