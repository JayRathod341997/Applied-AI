"""POST /support/start and WS /ws/{conversation_id} endpoints."""

from __future__ import annotations

import json
import logging
import uuid

from fastapi import APIRouter, HTTPException, WebSocket, WebSocketDisconnect
from langchain_core.messages import AIMessage, HumanMessage
from api.schemas.support import StartRequest, StartResponse, HistoryItem
from core.graph_runner import get_graph, run_graph

logger = logging.getLogger(__name__)

router = APIRouter(tags=["support"])


def _extract_reply(result: dict) -> str:
    """Extract the last AI message content from a graph result."""
    ai_messages = [m for m in result.get("messages", []) if isinstance(m, AIMessage)]
    return ai_messages[-1].content if ai_messages else "I'm sorry, I could not process your request."


@router.post("/support/start", response_model=StartResponse)
async def start_support(body: StartRequest) -> StartResponse:
    """
    Start or continue a support conversation.

    If ``conversation_id`` is omitted a new one is generated automatically.
    """
    if get_graph() is None:
        raise HTTPException(status_code=503, detail="Graph not initialised yet.")

    conversation_id = body.conversation_id or str(uuid.uuid4())

    try:
        result = run_graph(conversation_id, body.message)
    except Exception as exc:
        logger.error("Graph invocation failed: %s", exc, exc_info=True)
        raise HTTPException(status_code=500, detail=str(exc)) from exc

    return StartResponse(
        conversation_id=conversation_id,
        reply=_extract_reply(result),
        issue_type=result.get("issue_type"),
        severity=result.get("severity"),
        status=result.get("status"),
    )


@router.get("/support/history/{conversation_id}", response_model=list[HistoryItem])
async def get_history(conversation_id: str) -> list[HistoryItem]:
    """Retrieve the full message history for a conversation."""
    graph = get_graph()
    if graph is None:
        raise HTTPException(status_code=503, detail="Graph not initialised yet.")

    config = {"configurable": {"thread_id": conversation_id}}
    state = graph.get_state(config)
    
    if not state.values or "messages" not in state.values:
        return []

    history = []
    for m in state.values["messages"]:
        role = "user" if isinstance(m, HumanMessage) else "assistant"
        
        # Extract metadata if present
        issue_type = getattr(m, "response_metadata", {}).get("issue_type")
        severity = getattr(m, "response_metadata", {}).get("severity")
        status = getattr(m, "response_metadata", {}).get("status")
        
        history.append(
            HistoryItem(
                id=getattr(m, "id", str(uuid.uuid4())),
                role=role,
                content=m.content,
                timestamp=getattr(m, "timestamp", None), # We'll start saving this
                issue_type=issue_type,
                severity=severity,
                status=status,
            )
        )
    return history


@router.delete("/support/history/{conversation_id}")
async def delete_history(conversation_id: str) -> dict:
    """Delete a conversation history from the checkpointer."""
    graph = get_graph()
    if graph is None:
        raise HTTPException(status_code=503, detail="Graph not initialised yet.")

    checkpointer = getattr(graph, "checkpointer", None)
    if hasattr(checkpointer, "delete_conversation"):
        checkpointer.delete_conversation(conversation_id)
    
    return {"status": "success", "message": "Conversation deleted"}


@router.websocket("/ws/{conversation_id}")
async def websocket_endpoint(websocket: WebSocket, conversation_id: str) -> None:
    """
    WebSocket endpoint for real-time support interactions.

    Message protocol (JSON):
    - Client -> Server: {"message": "<user text>"}
    - Server -> Client: {"reply": "...", "issue_type": "...", "severity": "...", "status": "..."}
    - Server -> Client (error): {"error": "<message>"}
    - Client -> Server: {"message": "exit"} to close the connection gracefully.
    """
    await websocket.accept()
    logger.info("WebSocket connected: conversation_id=%s", conversation_id)

    if get_graph() is None:
        await websocket.send_json({"error": "Graph not initialised yet."})
        await websocket.close()
        return

    try:
        while True:
            raw = await websocket.receive_text()

            try:
                payload = json.loads(raw)
            except json.JSONDecodeError:
                await websocket.send_json({"error": "Invalid JSON payload."})
                continue

            user_message: str = payload.get("message", "").strip()
            if not user_message:
                await websocket.send_json({"error": "Empty message."})
                continue

            if user_message.lower() == "exit":
                await websocket.send_json({"reply": "Goodbye! Have a great day."})
                break

            try:
                result = run_graph(conversation_id, user_message)
            except Exception as exc:
                logger.error("Graph error on WS: %s", exc, exc_info=True)
                await websocket.send_json({"error": str(exc)})
                continue

            await websocket.send_json(
                {
                    "reply": _extract_reply(result),
                    "issue_type": result.get("issue_type"),
                    "severity": result.get("severity"),
                    "status": result.get("status"),
                }
            )

    except WebSocketDisconnect:
        logger.info("WebSocket disconnected: conversation_id=%s", conversation_id)
