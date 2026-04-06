"""
Medical Q&A - FastAPI + Uvicorn Inference Server

Endpoints:
  POST /answer          - answer a single medical question
  POST /answer/batch    - answer multiple questions in one call
  GET  /health          - liveness / readiness probe
  GET  /model/info      - display loaded model metadata

Run locally:
  uvicorn deploy.app:app --host 0.0.0.0 --port 8000 --reload

Production (multiple workers — NOT recommended for GPU model; use 1):
  uvicorn deploy.app:app --host 0.0.0.0 --port 8000 --workers 1

Environment variables:
  MODEL_PATH      Path to fine-tuned model (default: models/medical_qa_lora/final)
  BASE_MODEL      Base model name (required only if MODEL_PATH is LoRA-adapter-only)
  MAX_NEW_TOKENS  Generation token budget (default: 512)
  TEMPERATURE     Sampling temperature (default: 0.7)
"""

from __future__ import annotations

import logging
import os
import time
from contextlib import asynccontextmanager
from typing import List, Optional

import torch
import uvicorn
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

# Resolve package path when run as `uvicorn deploy.app:app` from project root
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.inference import MedicalQAInference

logging.basicConfig(level=logging.INFO,
                    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)


# ── Global state ──────────────────────────────────────────────────────────────

_engine: Optional[MedicalQAInference] = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Load the model once on startup; release on shutdown."""
    global _engine
    model_path = os.getenv("MODEL_PATH", "models/medical_qa_lora/final")
    base_model = os.getenv("BASE_MODEL", None)
    max_new_tokens = int(os.getenv("MAX_NEW_TOKENS", "512"))
    temperature = float(os.getenv("TEMPERATURE", "0.7"))

    logger.info(f"Loading Medical Q&A engine from: {model_path}")
    _engine = MedicalQAInference(
        model_path=model_path,
        base_model=base_model,
        max_new_tokens=max_new_tokens,
        temperature=temperature,
    )
    logger.info("Engine ready.")
    yield
    logger.info("Shutting down.")
    _engine = None


# ── App ───────────────────────────────────────────────────────────────────────

app = FastAPI(
    title="Medical Q&A API",
    description="Fine-tuned BioGPT/LLM for medical question answering",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


# ── Schemas ───────────────────────────────────────────────────────────────────

class QuestionRequest(BaseModel):
    question: str = Field(..., min_length=5, max_length=1024,
                          example="What are the early symptoms of Type 2 diabetes?")
    context: Optional[str] = Field(default="", max_length=1024,
                                   example="Patient is 45 years old, BMI 30.")

class AnswerResponse(BaseModel):
    question: str
    answer: str
    latency_ms: float

class BatchQuestionRequest(BaseModel):
    questions: List[str] = Field(..., min_items=1, max_items=16)
    contexts: Optional[List[str]] = Field(default=None)

class BatchAnswerResponse(BaseModel):
    answers: List[str]
    latency_ms: float

class HealthResponse(BaseModel):
    status: str
    device: str
    model_loaded: bool

class ModelInfoResponse(BaseModel):
    model_path: str
    device: str
    max_new_tokens: int
    parameter_count: Optional[int]


# ── Endpoints ─────────────────────────────────────────────────────────────────

@app.get("/health", response_model=HealthResponse, tags=["Utility"])
async def health_check():
    return HealthResponse(
        status="ok",
        device=str(_engine.device) if _engine else "N/A",
        model_loaded=_engine is not None,
    )


@app.get("/model/info", response_model=ModelInfoResponse, tags=["Utility"])
async def model_info():
    if _engine is None:
        raise HTTPException(status_code=503, detail="Model not loaded")
    try:
        param_count = sum(p.numel() for p in _engine.model.parameters())
    except Exception:
        param_count = None
    return ModelInfoResponse(
        model_path=_engine.model_path,
        device=str(_engine.device),
        max_new_tokens=_engine.max_new_tokens,
        parameter_count=param_count,
    )


@app.post("/answer", response_model=AnswerResponse, tags=["Inference"])
async def answer_question(req: QuestionRequest):
    if _engine is None:
        raise HTTPException(status_code=503, detail="Model not loaded")

    t0 = time.perf_counter()
    try:
        answer = _engine.answer(req.question, req.context or "")
    except Exception as exc:
        logger.error(f"Inference error: {exc}")
        raise HTTPException(status_code=500, detail=f"Inference error: {str(exc)}")

    latency_ms = round((time.perf_counter() - t0) * 1000, 1)
    return AnswerResponse(question=req.question, answer=answer, latency_ms=latency_ms)


@app.post("/answer/batch", response_model=BatchAnswerResponse, tags=["Inference"])
async def answer_batch(req: BatchQuestionRequest):
    if _engine is None:
        raise HTTPException(status_code=503, detail="Model not loaded")

    t0 = time.perf_counter()
    try:
        answers = _engine.answer_batch(req.questions, req.contexts)
    except Exception as exc:
        logger.error(f"Batch inference error: {exc}")
        raise HTTPException(status_code=500, detail=f"Inference error: {str(exc)}")

    latency_ms = round((time.perf_counter() - t0) * 1000, 1)
    return BatchAnswerResponse(answers=answers, latency_ms=latency_ms)


# ── Standalone entry-point ────────────────────────────────────────────────────

if __name__ == "__main__":
    uvicorn.run(
        "deploy.app:app",
        host="0.0.0.0",
        port=int(os.getenv("PORT", "8000")),
        workers=1,
        reload=False,
        log_level="info",
    )
