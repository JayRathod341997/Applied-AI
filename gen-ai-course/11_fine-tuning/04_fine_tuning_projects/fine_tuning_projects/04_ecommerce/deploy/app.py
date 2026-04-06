"""FastAPI application for serving the fine-tuned e-commerce assistant."""

from __future__ import annotations

import os
import sys
import time
from pathlib import Path
from threading import Lock
from typing import Any

import torch
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC_ROOT = PROJECT_ROOT / "src"
if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))

from ecommerce_ft.config import load_config, resolve_project_paths
from ecommerce_ft.data import build_prompt
from ecommerce_ft.modeling import load_model_for_inference, load_tokenizer

app = FastAPI(title="E-commerce Customer Support API", version="0.1.0")


class GenerateRequest(BaseModel):
    message: str = Field(..., min_length=1, description="Customer query/instruction.")
    context: str = Field(default="", description="Optional order/product context.")
    max_new_tokens: int | None = Field(default=None, ge=8, le=1024)
    temperature: float | None = Field(default=None, ge=0.0, le=2.0)
    top_p: float | None = Field(default=None, ge=0.05, le=1.0)


class GenerateResponse(BaseModel):
    response: str
    latency_ms: float


class InferenceState:
    def __init__(self) -> None:
        self.model: Any | None = None
        self.tokenizer: Any | None = None
        self.config = None
        self.lock = Lock()

    def load(self) -> None:
        if self.model is not None and self.tokenizer is not None:
            return

        config_path = os.getenv("ECOM_CONFIG_PATH", str(PROJECT_ROOT / "configs/train_config.yaml"))
        cfg = load_config(config_path)
        cfg = resolve_project_paths(cfg, project_root=PROJECT_ROOT)

        adapter_dir = os.getenv("ECOM_ADAPTER_DIR", str(Path(cfg.training.output_dir) / "adapter"))
        if not Path(adapter_dir).exists():
            raise FileNotFoundError(
                f"Adapter directory not found: {adapter_dir}. "
                "Train the model first or pass ECOM_ADAPTER_DIR."
            )

        tokenizer = load_tokenizer(cfg)
        model = load_model_for_inference(cfg, adapter_dir=adapter_dir)
        self.config = cfg
        self.model = model
        self.tokenizer = tokenizer


STATE = InferenceState()


@app.on_event("startup")
def startup_event() -> None:
    STATE.load()


@app.get("/health")
def health() -> dict[str, Any]:
    return {"status": "ok", "model_loaded": STATE.model is not None}


@app.post("/generate", response_model=GenerateResponse)
def generate(request: GenerateRequest) -> GenerateResponse:
    try:
        STATE.load()
    except Exception as exc:  # pragma: no cover - runtime deployment path
        raise HTTPException(status_code=500, detail=str(exc)) from exc

    if STATE.model is None or STATE.tokenizer is None or STATE.config is None:
        raise HTTPException(status_code=500, detail="Model state not initialized.")

    prompt = build_prompt(request.message, request.context)
    max_new_tokens = (
        request.max_new_tokens
        if request.max_new_tokens is not None
        else STATE.config.generation.max_new_tokens
    )
    temperature = (
        request.temperature if request.temperature is not None else STATE.config.generation.temperature
    )
    top_p = request.top_p if request.top_p is not None else STATE.config.generation.top_p

    start = time.perf_counter()
    with STATE.lock:
        model_inputs = STATE.tokenizer(prompt, return_tensors="pt")
        if torch.cuda.is_available():
            model_inputs = {k: v.cuda() for k, v in model_inputs.items()}

        generated = STATE.model.generate(
            **model_inputs,
            max_new_tokens=max_new_tokens,
            temperature=temperature,
            top_p=top_p,
            repetition_penalty=STATE.config.generation.repetition_penalty,
            do_sample=True,
            eos_token_id=STATE.tokenizer.eos_token_id,
            pad_token_id=STATE.tokenizer.pad_token_id,
        )
        full_text = STATE.tokenizer.decode(generated[0], skip_special_tokens=True)
    latency_ms = (time.perf_counter() - start) * 1000.0

    response_text = full_text[len(prompt) :].strip() if full_text.startswith(prompt) else full_text
    return GenerateResponse(response=response_text, latency_ms=latency_ms)
