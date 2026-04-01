from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
import time

from .models import AssignmentRequest, AssignmentResponse
from .pipelines.supervisor_pipeline import SupervisorPipeline
from .utils.logger import setup_logger
from .config import settings

logger = setup_logger(__name__)

app = FastAPI(
    title="VA Task Supervisor",
    description="VA task assignment, monitoring, and performance reporting",
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


pipeline = SupervisorPipeline()


@app.get("/health")
async def health():
    return {"status": "ok", "service": "va-task-supervisor"}


@app.post("/tasks/assign", response_model=AssignmentResponse)
async def assign_task(request: AssignmentRequest):
    try:
        result = await pipeline.assign_task(request.task.model_dump())
        return AssignmentResponse(**result)
    except Exception as exc:
        logger.exception(f"Assignment failed: {exc}")
        raise HTTPException(status_code=500, detail=str(exc))


@app.get("/tasks/overdue")
async def get_overdue_tasks():
    return {"overdue_tasks": [], "count": 0}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8017)
