from fastapi import FastAPI, HTTPException, Request, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware
import time

from .models import ParseScheduleResponse
from .pipelines.schedule_pipeline import SchedulePipeline
from .utils.logger import setup_logger
from .config import settings

logger = setup_logger(__name__)

app = FastAPI(
    title="Schedule Parser & Calendar Sync",
    description="Parse schedule screenshots via OCR and sync to Google Calendar",
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


pipeline = SchedulePipeline()


@app.get("/health")
async def health():
    return {
        "status": "ok",
        "service": "schedule-parser-calendar-sync",
        "ocr_configured": bool(settings.google_application_credentials),
    }


@app.post("/parse-schedule", response_model=ParseScheduleResponse)
async def parse_schedule(
    file: UploadFile = File(...),
    reminder_minutes: int = Form(default=30),
    calendar_id: str = Form(default="primary"),
):
    try:
        image_bytes = await file.read()
        result = await pipeline.process(image_bytes, reminder_minutes, calendar_id)
        return ParseScheduleResponse(**result)
    except Exception as exc:
        logger.exception(f"Parse failed: {exc}")
        raise HTTPException(status_code=500, detail=str(exc))


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8010)
