from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
import time

from .models import ResearchRequest, ResearchResponse
from .pipelines.research_pipeline import ResearchPipeline
from .utils.logger import setup_logger

logger = setup_logger(__name__)

app = FastAPI(
    title="Grant & Funding Research Agent",
    description="Automated grant and funding opportunity research and tracking",
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


pipeline = ResearchPipeline()


@app.get("/health")
async def health():
    return {"status": "ok", "service": "grant-funding-research-agent"}


@app.post("/research/run", response_model=ResearchResponse)
async def run_research(request: ResearchRequest):
    try:
        result = await pipeline.run(request.criteria.model_dump())
        return ResearchResponse(**result)
    except Exception as exc:
        logger.exception(f"Research failed: {exc}")
        raise HTTPException(status_code=500, detail=str(exc))


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8016)
