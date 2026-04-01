from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
import time

from .models import PipelineRequest, PipelineResponse
from .pipelines.job_pipeline import JobPipeline
from .utils.logger import setup_logger

logger = setup_logger(__name__)

app = FastAPI(
    title="Remote Job Ops Engine",
    description="Remote job scraper, classifier, resume generator, and auto-apply engine",
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


pipeline = JobPipeline()


@app.get("/health")
async def health():
    return {"status": "ok", "service": "remote-job-ops-engine"}


@app.post("/pipeline/run", response_model=PipelineResponse)
async def run_pipeline(request: PipelineRequest):
    try:
        result = await pipeline.run(
            request.role_types, request.max_applications, request.generate_resume
        )
        return PipelineResponse(**result)
    except Exception as exc:
        logger.exception(f"Pipeline failed: {exc}")
        raise HTTPException(status_code=500, detail=str(exc))


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8012)
