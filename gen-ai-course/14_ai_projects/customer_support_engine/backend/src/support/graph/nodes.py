"""LangGraph node functions for the customer support engine."""

from __future__ import annotations

import json
import logging

from langchain_core.messages import AIMessage, HumanMessage, SystemMessage
from langchain_groq import ChatGroq

from support.config import settings
from support.graph.state import SupportState
from support.tools.escalation import EscalationHandler
from support.tools.kb_search import KnowledgeBaseSearch

logger = logging.getLogger(__name__)


def _get_llm() -> ChatGroq:
    return ChatGroq(
        api_key=settings.GROQ_API_KEY,
        model="llama-3.3-70b-versatile",
        temperature=0,
    )


# ---------------------------------------------------------------------------
# Classifier Node
# ---------------------------------------------------------------------------

def classifier_node(state: SupportState) -> dict:
    """Identify issue type and severity from the latest user message."""
    llm = _get_llm()

    last_human = next(
        (m for m in reversed(state["messages"]) if isinstance(m, HumanMessage)),
        None,
    )
    user_text = last_human.content if last_human else ""
    user_text_lower = user_text.lower().strip().strip("!?,.")

    # Fast-path for very common single-word greetings
    if user_text_lower in ["hello", "hi", "hey", "greetings", "hi there", "hello there"]:
        return {
            "issue_type": "greeting",
            "severity": None,
            "kb_chunks": [],
            "resolution_steps": [],
            "retry_count": 0,
            "feedback_signal": None,
        }

    system_prompt = (
        "You are a customer support classifier. "
        "Analyze the user message for intent and categorize it into exactly one of these types:\n"
        "- 'greeting': For simple greetings like 'hello', 'hi', 'hey', 'good morning', etc.\n"
        "- 'billing': For questions about payments, invoices, or subscriptions.\n"
        "- 'technical': For reporting bugs or technical system issues.\n"
        "- 'general': For other support questions or when the category is unclear.\n\n"
        "Respond ONLY with a JSON object like this:\n"
        '{"issue_type": "greeting", "severity": null}  '
        '(Note: for greetings, severity must be null. For others, choose one of ["low", "medium", "high", "critical"].)\n'
        "Do not include any other text."
    )

    response = llm.invoke(
        [SystemMessage(content=system_prompt), HumanMessage(content=user_text)]
    )

    content = response.content.strip()
    if content.startswith("```json"):
        content = content[7:-3].strip()
    elif content.startswith("```"):
        content = content[3:-3].strip()

    try:
        data = json.loads(content)
        issue_type = data.get("issue_type", "general")
        severity = data.get("severity")
    except (json.JSONDecodeError, AttributeError):
        logger.warning("Classifier returned non-JSON response; defaulting to general/low.")
        issue_type = "general"
        severity = "low"

    logger.info("Classified issue: type=%s severity=%s", issue_type, severity)

    return {
        "issue_type": issue_type,
        "severity": severity,
        "kb_chunks": [],
        "resolution_steps": [],
        "retry_count": 0,
        "feedback_signal": None,
    }


# ---------------------------------------------------------------------------
# Router Node
# ---------------------------------------------------------------------------

def router_node(state: SupportState) -> dict:
    """Log the routing decision; actual branching is handled by conditional edges."""
    issue_type = state.get("issue_type", "general")
    logger.info("Router: directing to %s handler", issue_type)
    return {}


# ---------------------------------------------------------------------------
# Knowledge Retrieval Node
# ---------------------------------------------------------------------------

def retrieval_node(state: SupportState) -> dict:
    """Fetch relevant knowledge base chunks using Azure AI Search."""
    last_human = next(
        (m for m in reversed(state["messages"]) if isinstance(m, HumanMessage)),
        None,
    )
    query = last_human.content if last_human else ""

    kb = KnowledgeBaseSearch(
        endpoint=settings.AZURE_SEARCH_ENDPOINT,
        api_key=settings.AZURE_SEARCH_KEY,
        index_name=settings.AZURE_SEARCH_INDEX,
    )

    chunks = kb.search(query, top_k=5)
    logger.info("Retrieved %d KB chunks for query: %s", len(chunks), query[:60])

    return {"kb_chunks": chunks}


# ---------------------------------------------------------------------------
# Resolution Reasoner Node
# ---------------------------------------------------------------------------

def reasoner_node(state: SupportState) -> dict:
    """Core reasoning: produce step-by-step resolution using KB context."""
    llm = _get_llm()

    last_human = next(
        (m for m in reversed(state["messages"]) if isinstance(m, HumanMessage)),
        None,
    )
    user_text = last_human.content if last_human else ""
    kb_context = "\n\n".join(state.get("kb_chunks", []))

    system_prompt = (
        "You are an expert customer support agent. "
        "Using the knowledge base context provided, create a clear, numbered list of "
        "resolution steps to solve the customer's issue. "
        "If the context is insufficient, use your best judgment. "
        "Respond ONLY with a JSON array of strings, each string being one step. "
        "Example: [\"Step 1: ...\", \"Step 2: ...\"]"
    )

    user_prompt = (
        f"Customer issue: {user_text}\n\n"
        f"Knowledge base context:\n{kb_context or 'No context available.'}"
    )

    response = llm.invoke(
        [SystemMessage(content=system_prompt), HumanMessage(content=user_prompt)]
    )

    try:
        steps = json.loads(response.content.strip())
        if not isinstance(steps, list):
            steps = [response.content.strip()]
    except (json.JSONDecodeError, AttributeError):
        steps = [response.content.strip()]

    logger.info("Reasoner produced %d resolution steps", len(steps))

    return {"resolution_steps": steps}


# ---------------------------------------------------------------------------
# Response Generator Node
# ---------------------------------------------------------------------------

def response_generator_node(state: SupportState) -> dict:
    """Compose a polished, customer-facing message from the resolution steps."""
    llm = _get_llm()

    steps = state.get("resolution_steps", [])
    issue_type = state.get("issue_type", "general")
    severity = state.get("severity", "low")
    steps_text = "\n".join(steps) if steps else "No resolution steps available."

    if issue_type == "greeting":
        system_prompt = (
            "You are a friendly customer support assistant. "
            "Greet the customer warmly and briefly mention that you can help with "
            "billing inquiries, technical troubleshooting, and general product questions. "
            "Ask how you can assist them today."
        )
        user_prompt = f"The customer said: {state['messages'][-1].content}"
    else:
        system_prompt = (
            "You are a friendly and professional customer support agent. "
            "Given the resolution steps below, write a warm, concise response addressed "
            "directly to the customer. Do not use bullet points; write in natural prose. "
            "End with an offer to help further."
        )
        user_prompt = (
            f"Issue type: {issue_type} | Severity: {severity or 'N/A'}\n\n"
            f"Resolution steps:\n{steps_text}"
        )

    response = llm.invoke(
        [SystemMessage(content=system_prompt), HumanMessage(content=user_prompt)]
    )

    reply = response.content.strip()
    logger.info("Response generated (%d chars)", len(reply))

    return {
        "messages": [AIMessage(content=reply)],
        "status": "resolved" if issue_type != "greeting" else "open",
    }


# ---------------------------------------------------------------------------
# Feedback Evaluator Node
# ---------------------------------------------------------------------------

def feedback_evaluator_node(state: SupportState) -> dict:
    """
    Evaluate the last customer message as feedback.

    Uses the LLM to classify the latest user reply as 'helpful' or 'not_helpful'.
    The graph's conditional edge then decides whether to loop or finish.
    """
    llm = _get_llm()

    last_human = next(
        (m for m in reversed(state["messages"]) if isinstance(m, HumanMessage)),
        None,
    )
    feedback_text = last_human.content if last_human else ""

    system_prompt = (
        "You are evaluating customer feedback after a support interaction. "
        "Respond ONLY with a JSON object: "
        '{"signal": "helpful"} or {"signal": "not_helpful"}. '
        "Be generous – if the customer seems satisfied or their issue is resolved, "
        "choose helpful."
    )

    response = llm.invoke(
        [SystemMessage(content=system_prompt), HumanMessage(content=feedback_text)]
    )

    content = response.content.strip()
    if content.startswith("```json"):
        content = content[7:-3].strip()
    elif content.startswith("```"):
        content = content[3:-3].strip()

    try:
        data = json.loads(content)
        signal = data.get("signal", "helpful")
    except (json.JSONDecodeError, AttributeError):
        signal = "helpful"

    retry_count = state.get("retry_count", 0)
    if signal == "not_helpful":
        retry_count += 1

    logger.info("Feedback signal: %s (retry_count=%d)", signal, retry_count)

    return {
        "feedback_signal": signal,
        "retry_count": retry_count,
    }


# ---------------------------------------------------------------------------
# Escalation Node
# ---------------------------------------------------------------------------

def escalation_node(state: SupportState) -> dict:
    """Create a human-handoff ticket in Cosmos DB and notify the customer."""
    handler = EscalationHandler(
        endpoint=settings.COSMOS_ENDPOINT,
        key=settings.COSMOS_KEY,
        database_name=settings.COSMOS_DB,
        container_name=settings.COSMOS_CONTAINER,
    )

    ticket_id = handler.create_ticket(state)
    logger.info("Escalation ticket created: %s", ticket_id)

    message = (
        f"I apologize that we weren't able to fully resolve your issue automatically. "
        f"I have escalated your case to our specialist team. "
        f"Your ticket ID is **{ticket_id}**. "
        f"A team member will contact you shortly. "
        f"Thank you for your patience."
    )

    return {
        "messages": [AIMessage(content=message)],
        "status": "escalated",
    }
