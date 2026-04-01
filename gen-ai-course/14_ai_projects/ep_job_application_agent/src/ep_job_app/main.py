from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
import time

from .models import ScrapeRequest, ScrapeResponse
from .pipelines.application_pipeline import ApplicationPipeline
from .utils.logger import setup_logger

logger = setup_logger(__name__)

app = FastAPI(
    title="EP Job Application Agent",
    description="Executive Protection job scraper, filter, and auto-apply agent",
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
    response.headers["X-Process-Time"] = f"{time.perf_counter() - start:.4f}s"
    return response


pipeline = ApplicationPipeline()


@app.get("/health")
async def health():
    return {"status": "ok", "service": "ep-job-application-agent"}


@app.post("/scrape-trigger", response_model=ScrapeResponse)
async def scrape_trigger(request: ScrapeRequest):
    try:
        result = await pipeline.run(
            request.min_rate_per_day, request.location, request.max_results
        )
        return ScrapeResponse(**result)
    except Exception as exc:
        logger.exception(f"Scrape failed: {exc}")
        raise HTTPException(status_code=500, detail=str(exc))


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8011)
