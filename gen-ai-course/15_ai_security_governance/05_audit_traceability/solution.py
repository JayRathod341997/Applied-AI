"""
solution.py - Tamper-evident AuditLogger for AI interactions.

Reference solution for the Module 15.05 exercise: Audit, Traceability & Control.

What this demonstrates (all stdlib, no network, no API keys):
  1. Append-only, hash-chained JSON audit log (blockchain-style linking).
  2. PII redaction BEFORE anything is written to the log.
  3. Chain-integrity verification that DETECTS tampering (altered/inserted/
     deleted records).
  4. Trace reconstruction: pull every span for one correlation_id and print
     an ordered, human-readable trace of a multi-step agent run.

Design notes
------------
* Each record stores the SHA-256 hash of the previous record ("prev_hash").
  The record's own "hash" is computed over its canonical content INCLUDING
  prev_hash. Change any earlier record and every subsequent hash breaks -> the
  log is tamper-EVIDENT (you cannot silently rewrite history).
* We log the REDACTED payload. In a real system the raw payload would be
  encrypted and stored separately under stricter access control; here we only
  keep a hash of the raw text so you can prove what was said without exposing
  PII in the audit trail.
* The genesis record chains from a fixed sentinel hash ("0" * 64).

Run:  python solution.py
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
# 1. PII redaction (runs BEFORE logging)
# --------------------------------------------------------------------------- #

# Ordered so more specific patterns win. Each maps to a placeholder token.
_PII_PATTERNS: list[tuple[str, re.Pattern[str]]] = [
    ("EMAIL", re.compile(r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}")),
    ("SSN", re.compile(r"\b\d{3}-\d{2}-\d{4}\b")),
    ("CREDIT_CARD", re.compile(r"\b(?:\d[ -]?){13,16}\b")),
    ("PHONE", re.compile(r"\b(?:\+?\d{1,2}[ -]?)?\(?\d{3}\)?[ -]?\d{3}[ -]?\d{4}\b")),
    ("IPV4", re.compile(r"\b(?:\d{1,3}\.){3}\d{1,3}\b")),
]


def redact_pii(text: str) -> tuple[str, dict[str, int]]:
    """Return (redacted_text, counts). Never mutates the original string.

    Counts let you prove HOW MUCH PII was present without storing the values.
    """
    counts: dict[str, int] = {}
    redacted = text
    for label, pattern in _PII_PATTERNS:
        redacted, n = pattern.subn(f"[REDACTED_{label}]", redacted)
        if n:
            counts[label] = counts.get(label, 0) + n
    return redacted, counts


# --------------------------------------------------------------------------- #
# 2. Hashing helpers
# --------------------------------------------------------------------------- #

def sha256_hex(data: str) -> str:
    return hashlib.sha256(data.encode("utf-8")).hexdigest()


def canonical_json(obj: Any) -> str:
    """Deterministic JSON so hashes are reproducible across processes."""
    return json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


# --------------------------------------------------------------------------- #
# 3. The audit record
# --------------------------------------------------------------------------- #

class Decision(str, Enum):
    ALLOW = "allow"
    BLOCK = "block"
    REVIEW = "review"  # routed to human-in-the-loop


@dataclass
class AuditRecord:
    """One immutable span in the audit chain.

    `hash` and `prev_hash` are the tamper-evidence machinery. Everything else
    is the "what to log for every AI interaction" evidence set.
    """

    # --- identity / traceability ---
    seq: int                         # position in the append-only log
    record_id: str                   # unique id for this span
    correlation_id: str              # groups all spans of one logical request
    parent_span_id: str | None       # for multi-step agent trees
    timestamp: float                 # epoch seconds (UTC)

    # --- who / what ---
    user_id: str
    app_id: str
    step: str                        # e.g. "retrieval", "generation", "guardrail"

    # --- model + prompt lineage ---
    model: str
    model_version: str               # PINNED, never "latest"
    system_prompt_version: str

    # --- request / response (REDACTED before it reaches here) ---
    request_redacted: str
    response_redacted: str
    raw_request_hash: str            # proof-of-content without storing raw PII
    raw_response_hash: str
    pii_found: dict[str, int]

    # --- retrieval / policy / guardrail evidence ---
    retrieval_sources: list[str]
    policy_decision: Decision
    guardrail_verdicts: dict[str, str]

    # --- ops metrics ---
    prompt_tokens: int
    completion_tokens: int
    cost_usd: float
    latency_ms: int

    # --- integrity (filled by the logger) ---
    prev_hash: str = GENESIS_PREV_HASH
    hash: str = ""

    def content_for_hash(self) -> dict[str, Any]:
        """Everything EXCEPT the record's own `hash` (which is derived)."""
        d = asdict(self)
        d.pop("hash", None)
        # Enum -> value for stable serialization
        d["policy_decision"] = self.policy_decision.value
        return d

    def compute_hash(self) -> str:
        return sha256_hex(canonical_json(self.content_for_hash()))


# --------------------------------------------------------------------------- #
# 4. The tamper-evident AuditLogger
# --------------------------------------------------------------------------- #

class AuditLogger:
    """Append-only, hash-chained audit log persisted as JSON Lines.

    Public API:
      * log(...)            -> append one redacted, chained record
      * verify_chain()      -> (ok, problems) integrity check / tamper detection
      * reconstruct_trace() -> ordered spans for a correlation_id
      * records()           -> read-only view of the in-memory chain
    """

    def __init__(self, path: str) -> None:
        self.path = path
        self._records: list[AuditRecord] = []
        self._last_hash = GENESIS_PREV_HASH

    # -- write path ---------------------------------------------------------- #
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
        # Redact BEFORE the data lands in the log.
        req_redacted, req_pii = redact_pii(request)
        resp_redacted, resp_pii = redact_pii(response)
        pii_found = {k: req_pii.get(k, 0) + resp_pii.get(k, 0)
                     for k in set(req_pii) | set(resp_pii)}

        record = AuditRecord(
            seq=len(self._records),
            record_id=uuid.uuid4().hex,
            correlation_id=correlation_id,
            parent_span_id=parent_span_id,
            timestamp=time.time(),
            user_id=user_id,
            app_id=app_id,
            step=step,
            model=model,
            model_version=model_version,
            system_prompt_version=system_prompt_version,
            request_redacted=req_redacted,
            response_redacted=resp_redacted,
            raw_request_hash=sha256_hex(request),
            raw_response_hash=sha256_hex(response),
            pii_found=pii_found,
            retrieval_sources=list(retrieval_sources),
            policy_decision=policy_decision,
            guardrail_verdicts=guardrail_verdicts or {},
            prompt_tokens=prompt_tokens,
            completion_tokens=completion_tokens,
            cost_usd=cost_usd,
            latency_ms=latency_ms,
            prev_hash=self._last_hash,
        )
        record.hash = record.compute_hash()

        self._records.append(record)
        self._last_hash = record.hash
        self._append_to_disk(record)
        return record

    def _append_to_disk(self, record: AuditRecord) -> None:
        # Append-only: never open in "w"/truncate mode. In prod this file lives
        # on WORM storage so even root cannot rewrite earlier lines.
        line = canonical_json(record.content_for_hash() | {"hash": record.hash})
        with open(self.path, "a", encoding="utf-8") as fh:
            fh.write(line + "\n")

    # -- verify path --------------------------------------------------------- #
    def verify_chain(self) -> tuple[bool, list[str]]:
        """Recompute every hash and confirm the chain links. Returns
        (ok, problems). Any mutation to a past record surfaces here."""
        problems: list[str] = []
        expected_prev = GENESIS_PREV_HASH
        for i, rec in enumerate(self._records):
            if rec.seq != i:
                problems.append(f"seq {i}: out-of-order seq={rec.seq}")
            if rec.prev_hash != expected_prev:
                problems.append(
                    f"seq {i}: broken link (prev_hash mismatch -> insert/delete?)")
            if rec.compute_hash() != rec.hash:
                problems.append(
                    f"seq {i}: content altered (stored hash != recomputed)")
            expected_prev = rec.hash
        return (len(problems) == 0, problems)

    @staticmethod
    def verify_file(path: str) -> tuple[bool, list[str]]:
        """Independent verifier: re-reads the JSONL from disk and checks it,
        so an auditor can validate without trusting the running process."""
        problems: list[str] = []
        expected_prev = GENESIS_PREV_HASH
        with open(path, "r", encoding="utf-8") as fh:
            for i, line in enumerate(fh):
                line = line.strip()
                if not line:
                    continue
                obj = json.loads(line)
                stored_hash = obj.pop("hash", "")
                recomputed = sha256_hex(canonical_json(obj))
                if obj.get("prev_hash") != expected_prev:
                    problems.append(f"line {i}: broken chain link")
                if recomputed != stored_hash:
                    problems.append(f"line {i}: content altered")
                expected_prev = stored_hash
        return (len(problems) == 0, problems)

    # -- read path ----------------------------------------------------------- #
    def reconstruct_trace(self, correlation_id: str) -> list[AuditRecord]:
        spans = [r for r in self._records if r.correlation_id == correlation_id]
        return sorted(spans, key=lambda r: (r.timestamp, r.seq))

    def records(self) -> list[AuditRecord]:
        return list(self._records)


# --------------------------------------------------------------------------- #
# 5. Local, deterministic "LLM" + a simulated multi-step agent
# --------------------------------------------------------------------------- #

def fake_llm(prompt: str) -> str:
    """Deterministic stand-in for a real model. No network."""
    if "refund" in prompt.lower():
        return ("Your refund of $49.00 will be processed to the card on file. "
                "A confirmation was sent to jane.doe@example.com.")
    if "summarize" in prompt.lower():
        return "Summary: customer wants a refund and status update."
    return "Acknowledged. How else can I help?"


def run_agent(logger: AuditLogger, user_id: str, question: str) -> str:
    """A 3-step agent: retrieve -> generate -> guardrail. Every step is
    logged under ONE correlation_id so the trace is fully reconstructable."""
    correlation_id = uuid.uuid4().hex

    # Step 1: retrieval
    t0 = time.perf_counter()
    sources = ["kb://refund-policy#v4", "kb://account-123"]
    retrieval_span = logger.log(
        correlation_id=correlation_id,
        user_id=user_id,
        app_id="support-agent",
        step="retrieval",
        model="text-embedding-3-small",
        model_version="2024-01-25",
        system_prompt_version="retrieval-v2",
        request=question,
        response=f"retrieved {len(sources)} docs",
        retrieval_sources=sources,
        latency_ms=int((time.perf_counter() - t0) * 1000),
    )

    # Step 2: generation
    t0 = time.perf_counter()
    answer = fake_llm(question)
    logger.log(
        correlation_id=correlation_id,
        user_id=user_id,
        app_id="support-agent",
        step="generation",
        model="claude-opus-4",
        model_version="2026-05-01",  # PINNED version, never "latest"
        system_prompt_version="support-sys-v7",
        request=question,
        response=answer,
        retrieval_sources=sources,
        prompt_tokens=812,
        completion_tokens=64,
        cost_usd=0.0031,
        latency_ms=int((time.perf_counter() - t0) * 1000),
        parent_span_id=retrieval_span.record_id,
    )

    # Step 3: output guardrail + policy decision
    t0 = time.perf_counter()
    verdicts = {"toxicity": "pass", "pii_leak": "pass", "policy": "pass"}
    logger.log(
        correlation_id=correlation_id,
        user_id=user_id,
        app_id="support-agent",
        step="guardrail",
        model="guardrail-classifier",
        model_version="1.4.2",
        system_prompt_version="guardrail-v3",
        request=answer,
        response="approved for delivery",
        policy_decision=Decision.ALLOW,
        guardrail_verdicts=verdicts,
        latency_ms=int((time.perf_counter() - t0) * 1000),
        parent_span_id=retrieval_span.record_id,
    )
    return correlation_id


# --------------------------------------------------------------------------- #
# 6. Demo
# --------------------------------------------------------------------------- #

def _print_trace(logger: AuditLogger, correlation_id: str) -> None:
    print(f"\n=== Reconstructed trace for correlation_id={correlation_id[:12]}... ===")
    for span in logger.reconstruct_trace(correlation_id):
        print(f"  [{span.seq}] {span.step:<11} "
              f"model={span.model}@{span.model_version} "
              f"policy={span.policy_decision.value} "
              f"pii={span.pii_found or '{}'} "
              f"lat={span.latency_ms}ms")
        print(f"        req : {span.request_redacted[:60]}")
        print(f"        resp: {span.response_redacted[:60]}")


def main() -> None:
    import tempfile
    import os

    log_path = os.path.join(tempfile.gettempdir(), "ai_audit_demo.jsonl")
    # Fresh file for a clean demo (real logs are append-only forever).
    if os.path.exists(log_path):
        os.remove(log_path)

    logger = AuditLogger(log_path)

    print("### 1. Logging several AI interactions (multi-step agent) ###")
    cid1 = run_agent(logger, user_id="user-1001",
                     question="Please process my refund. My email is jane.doe@example.com "
                              "and my SSN is 123-45-6789.")
    cid2 = run_agent(logger, user_id="user-2002",
                     question="Can you summarize my account status? Call me at (415) 555-0199.")
    print(f"Logged {len(logger.records())} records across 2 correlation ids.")
    print("Note: PII was redacted BEFORE writing. Sample stored request:")
    print("   ", logger.records()[0].request_redacted)

    print("\n### 2. Verify chain integrity (in-memory AND from disk) ###")
    ok, problems = logger.verify_chain()
    print(f"in-memory verify_chain() -> ok={ok} problems={problems}")
    ok_file, problems_file = AuditLogger.verify_file(log_path)
    print(f"on-disk  verify_file()   -> ok={ok_file} problems={problems_file}")

    print("\n### 3. Demonstrate tamper detection ###")
    # Attacker silently rewrites a past response to hide what happened.
    victim = logger.records()[1]
    original_value = victim.response_redacted
    print(f"Tampering with record seq={victim.seq}: altering response_redacted...")
    victim.response_redacted = "APPROVED (falsified) - no refund actually issued"
    ok_after, problems_after = logger.verify_chain()
    print(f"verify_chain() after tamper -> ok={ok_after}")
    for p in problems_after:
        print(f"   ! {p}")
    assert not ok_after, "Tampering MUST be detected"
    # Restore the exact original so the trace print below stays coherent.
    victim.response_redacted = original_value
    ok_restored, _ = logger.verify_chain()
    print(f"verify_chain() after restoring original -> ok={ok_restored}")

    print("\n### 4. Reconstruct full traces by correlation_id ###")
    _print_trace(logger, cid1)
    _print_trace(logger, cid2)

    print(f"\nAudit log written to: {log_path}")
    print("Done.")


if __name__ == "__main__":
    main()
