"""
exercise.py - STARTER scaffold: build a tamper-evident AuditLogger.

Goal: implement an append-only, hash-chained audit log for AI interactions
that (a) redacts PII BEFORE logging, (b) can verify chain integrity and detect
tampering, and (c) can reconstruct a full trace by correlation_id.

Fill in every TODO. The stubs below let the file RUN as-is (it just won't do
anything useful yet). Use only the standard library: hashlib, json, re,
dataclasses, enum, time, uuid.  No network. No API keys.

Run:  python exercise.py
"""

from __future__ import annotations

import hashlib
import json
import re
import time
import uuid
from dataclasses import dataclass, field, asdict
from enum import Enum
from typing import Any, Iterable

GENESIS_PREV_HASH = "0" * 64


# --------------------------------------------------------------------------- #
# 1. PII redaction (must run BEFORE anything is written to the log)
# --------------------------------------------------------------------------- #

def redact_pii(text: str) -> tuple[str, dict[str, int]]:
    """Return (redacted_text, counts_by_type).

    TODO:
      * Detect at least EMAIL and SSN (bonus: PHONE, CREDIT_CARD, IPV4).
      * Replace each match with a token like "[REDACTED_EMAIL]".
      * Return how many of each type you replaced (so you can prove how much
        PII was present WITHOUT storing the values).
      * Never mutate the input string.
    """
    # TODO: implement real redaction with regex patterns.
    return text, {}


# --------------------------------------------------------------------------- #
# 2. Hashing helpers
# --------------------------------------------------------------------------- #

def sha256_hex(data: str) -> str:
    return hashlib.sha256(data.encode("utf-8")).hexdigest()


def canonical_json(obj: Any) -> str:
    """Deterministic JSON so the same content always hashes the same."""
    # TODO: use sort_keys=True and a fixed separator so hashes are reproducible.
    return json.dumps(obj)


# --------------------------------------------------------------------------- #
# 3. Audit record
# --------------------------------------------------------------------------- #

class Decision(str, Enum):
    ALLOW = "allow"
    BLOCK = "block"
    REVIEW = "review"


@dataclass
class AuditRecord:
    seq: int
    record_id: str
    correlation_id: str
    parent_span_id: str | None
    timestamp: float
    user_id: str
    app_id: str
    step: str
    model: str
    model_version: str
    system_prompt_version: str
    request_redacted: str
    response_redacted: str
    raw_request_hash: str
    raw_response_hash: str
    pii_found: dict[str, int]
    retrieval_sources: list[str]
    policy_decision: Decision
    guardrail_verdicts: dict[str, str]
    prompt_tokens: int
    completion_tokens: int
    cost_usd: float
    latency_ms: int
    prev_hash: str = GENESIS_PREV_HASH
    hash: str = ""

    def content_for_hash(self) -> dict[str, Any]:
        """Everything EXCEPT the record's own `hash`."""
        d = asdict(self)
        d.pop("hash", None)
        d["policy_decision"] = self.policy_decision.value
        return d

    def compute_hash(self) -> str:
        # TODO: hash the canonical JSON of content_for_hash().
        return ""


# --------------------------------------------------------------------------- #
# 4. Tamper-evident AuditLogger
# --------------------------------------------------------------------------- #

class AuditLogger:
    def __init__(self, path: str) -> None:
        self.path = path
        self._records: list[AuditRecord] = []
        self._last_hash = GENESIS_PREV_HASH

    def log(
        self,
        *,
        correlation_id: str,
        user_id: str,
        app_id: str,
        step: str,
        model: str,
        model_version: str,
        system_prompt_version: str,
        request: str,
        response: str,
        retrieval_sources: Iterable[str] = (),
        policy_decision: Decision = Decision.ALLOW,
        guardrail_verdicts: dict[str, str] | None = None,
        prompt_tokens: int = 0,
        completion_tokens: int = 0,
        cost_usd: float = 0.0,
        latency_ms: int = 0,
        parent_span_id: str | None = None,
    ) -> AuditRecord:
        """Append one redacted, hash-chained record.

        TODO:
          1. Redact request AND response before building the record.
          2. Store raw_request_hash / raw_response_hash (proof-of-content).
          3. Set prev_hash = self._last_hash, then compute record.hash.
          4. Append to self._records, update self._last_hash, persist to disk.
        """
        # TODO: implement. For now return a placeholder so the file runs.
        raise NotImplementedError("Implement AuditLogger.log")

    def _append_to_disk(self, record: AuditRecord) -> None:
        # TODO: append ONE JSON line (never truncate/overwrite the file).
        pass

    def verify_chain(self) -> tuple[bool, list[str]]:
        """Recompute every hash and confirm links. Return (ok, problems).

        TODO: walk records; flag (a) prev_hash != expected, (b) recomputed
        hash != stored hash, (c) out-of-order seq. Any past mutation -> fail.
        """
        # TODO: implement real verification.
        return True, []

    def reconstruct_trace(self, correlation_id: str) -> list[AuditRecord]:
        """Return all spans for one correlation_id, time-ordered.

        TODO: filter self._records and sort by (timestamp, seq).
        """
        # TODO: implement.
        return []

    def records(self) -> list[AuditRecord]:
        return list(self._records)


# --------------------------------------------------------------------------- #
# 5. Local fake LLM + simulated agent (provided)
# --------------------------------------------------------------------------- #

def fake_llm(prompt: str) -> str:
    if "refund" in prompt.lower():
        return ("Your refund will be processed. Confirmation sent to "
                "jane.doe@example.com.")
    return "Acknowledged. How else can I help?"


def run_agent(logger: AuditLogger, user_id: str, question: str) -> str:
    """Log a 2-step agent run under one correlation_id."""
    correlation_id = uuid.uuid4().hex
    logger.log(
        correlation_id=correlation_id, user_id=user_id, app_id="support-agent",
        step="retrieval", model="embed-3", model_version="2024-01-25",
        system_prompt_version="r-v2", request=question,
        response="retrieved 2 docs", retrieval_sources=["kb://policy#v4"],
    )
    answer = fake_llm(question)
    logger.log(
        correlation_id=correlation_id, user_id=user_id, app_id="support-agent",
        step="generation", model="model-x", model_version="2026-05-01",
        system_prompt_version="sys-v7", request=question, response=answer,
        prompt_tokens=800, completion_tokens=50, cost_usd=0.003, latency_ms=120,
    )
    return correlation_id


# --------------------------------------------------------------------------- #
# 6. Demo
# --------------------------------------------------------------------------- #

def main() -> None:
    import tempfile, os
    log_path = os.path.join(tempfile.gettempdir(), "ai_audit_exercise.jsonl")
    if os.path.exists(log_path):
        os.remove(log_path)

    logger = AuditLogger(log_path)
    try:
        cid = run_agent(logger, "user-1001",
                        "Please process my refund. Email: jane.doe@example.com")
    except NotImplementedError as e:
        print(f"[stub] {e} -- fill in the TODOs to make the demo work.")
        return

    print("Records:", len(logger.records()))
    ok, problems = logger.verify_chain()
    print("verify_chain ok:", ok, problems)
    print("trace:", [r.step for r in logger.reconstruct_trace(cid)])


if __name__ == "__main__":
    main()
