"""
Customer Support Engine – FastAPI application entry point.

Endpoints
---------
GET  /health                   – Liveness check.
POST /support/start            – Start or continue a support conversation.
WS   /ws/{conversation_id}    – Real-time WebSocket interface.
"""

from __future__ import annotations

import logging
from contextlib import asynccontextmanager
from typing import AsyncGenerator

import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from api.routes.health import router as health_router
from api.routes.support import router as support_router
from core.graph_runner import set_graph
from support.config import settings
from support.graph.builder import build_graph
from support.memory.checkpointer import CosmosDBCheckpointer

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    logger.info("Initialising LangGraph with CosmosDB checkpointer ...")
    try:
        checkpointer = CosmosDBCheckpointer(
            endpoint=settings.COSMOS_ENDPOINT,
            key=settings.COSMOS_KEY,
            database_name=settings.COSMOS_DB,
            container_name=settings.COSMOS_CONTAINER,
        )
        set_graph(build_graph(checkpointer=checkpointer))
        logger.info("Graph ready.")
    except Exception as exc:
        logger.warning(
            "Could not initialise CosmosDB checkpointer (%s); falling back to MemorySaver.",
            exc,
        )
        set_graph(build_graph())

    yield

    logger.info("Shutting down Customer Support Engine.")


app = FastAPI(
    title="Customer Support Engine",
    description="Stateful multi-agent customer support system powered by LangGraph + Azure AI.",
    version="0.1.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health_router)
app.include_router(support_router)


if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8003, reload=False)
