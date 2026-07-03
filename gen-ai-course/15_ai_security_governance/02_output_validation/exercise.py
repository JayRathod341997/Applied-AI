"""
Exercise — build an OutputValidator gateway.

Fill in the TODOs so that `python exercise.py` validates several sample outputs
and prints a decision (ALLOW / SANITIZED / BLOCKED) plus a sanitized output for
each. Everything runs OFFLINE — no network, no API keys. The LLM and its retry
are simulated by `fake_llm_repair` below.

Read exercise_01.md for the full brief and acceptance criteria.
Check your work against solution.py when you're done.
"""

from __future__ import annotations

import html
import json
import re
from dataclasses import dataclass, field
from enum import Enum
from typing import Callable

# pydantic is optional — your code must work with OR without it.
try:
    from pydantic import BaseModel, ValidationError

    _HAS_PYDANTIC = True

    class AnswerModel(BaseModel):
        answer: str
        confidence: float

except Exception:
    _HAS_PYDANTIC = False
    AnswerModel = None  # type: ignore


# --------------------------------------------------------------------------- #
# Core types (provided)                                                        #
# --------------------------------------------------------------------------- #
class Severity(Enum):
    INFO = "INFO"
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


class Action(Enum):
    PASS = "pass"
    SANITIZE = "sanitize"
    RETRY = "retry"
    BLOCK = "block"


class Decision(Enum):
    ALLOW = "ALLOW"
    SANITIZED = "SANITIZED"
    BLOCKED = "BLOCKED"


@dataclass
class Finding:
    validator: str
    ok: bool
    action: Action
    message: str
    severity: Severity
    output: str | None = None


@dataclass
class Context:
    grounding: list[str] = field(default_factory=list)
    expect_json: bool = False
    pydantic_model: type | None = None
    required_fields: dict[str, type] | None = None


@dataclass
class Report:
    decision: Decision
    output: str
    findings: list[Finding]
    attempts: int


class Validator:
    name = "base"

    def check(self, output: str, ctx: Context) -> Finding:
        raise NotImplementedError


def _ok(name: str, msg: str = "ok") -> Finding:
    return Finding(name, True, Action.PASS, msg, Severity.INFO)


# --------------------------------------------------------------------------- #
# Validators — implement each check()                                          #
# --------------------------------------------------------------------------- #
class SecretScanner(Validator):
    name = "secret_scan"
    PATTERNS = [
        re.compile(r"AKIA[0-9A-Z]{16}"),
        re.compile(r"sk-[A-Za-z0-9]{20,}"),
        re.compile(r"(?i)(?:api[_-]?key|secret|password|token)\s*[:=]\s*['\"]?[A-Za-z0-9/+=_\-]{8,}"),
    ]

    def check(self, output: str, ctx: Context) -> Finding:
        # TODO: if any secret pattern matches, return a Finding with Action.BLOCK
        #       (CRITICAL). Never redact-and-ship a credential.
        return _ok(self.name)


class SchemaValidator(Validator):
    name = "schema"

    def check(self, output: str, ctx: Context) -> Finding:
        if not ctx.expect_json:
            return _ok(self.name, "n/a")
        # TODO: json.loads(output); on JSONDecodeError -> Action.RETRY.
        # TODO: validate against ctx.pydantic_model (if pydantic) OR
        #       ctx.required_fields (fallback). On errors -> Action.RETRY.
        return _ok(self.name)


class PIIRedactor(Validator):
    name = "pii_redact"
    RULES = [
        ("EMAIL", re.compile(r"[A-Za-z0-9._%+\-]+@[A-Za-z0-9.\-]+\.[A-Za-z]{2,}")),
        ("PHONE", re.compile(r"\+?\d[\d\-\s().]{7,}\d")),
    ]

    def check(self, output: str, ctx: Context) -> Finding:
        # TODO: substitute each match with [REDACTED_<LABEL>]; if anything was
        #       redacted, return Action.SANITIZE with output=<redacted text>.
        return _ok(self.name)


class UnsafeContentScanner(Validator):
    name = "unsafe_output"
    MARKERS = [re.compile(r"(?i)<\s*script"), re.compile(r"(?i)javascript:"),
               re.compile(r"(?i)\son\w+\s*=")]

    def check(self, output: str, ctx: Context) -> Finding:
        # TODO: if active markup is present, HTML-encode the output
        #       (html.escape) and return Action.SANITIZE.
        return _ok(self.name)


class GroundednessChecker(Validator):
    name = "groundedness"

    def check(self, output: str, ctx: Context) -> Finding:
        if not ctx.grounding:
            return _ok(self.name, "n/a")
        # TODO: fail (Action.RETRY) if a numeric claim in `output` is absent from
        #       ctx.grounding, or if content-word overlap is too low.
        #       Tip: strip [1]-style citations before extracting numbers.
        return _ok(self.name)


# --------------------------------------------------------------------------- #
# The gateway                                                                  #
# --------------------------------------------------------------------------- #
RepairFn = Callable[[str, list[str]], str]


class OutputValidator:
    def __init__(self, validators: list[Validator] | None = None) -> None:
        self.validators = validators or [
            SecretScanner(), SchemaValidator(), PIIRedactor(),
            UnsafeContentScanner(), GroundednessChecker(),
        ]

    def validate(self, raw_output: str, ctx: Context,
                 repair_fn: RepairFn | None = None, max_retries: int = 1) -> Report:
        # TODO: loop over self.validators; apply SANITIZE outputs to a running
        #       `working` string; BLOCK -> return BLOCKED; RETRY -> call repair_fn
        #       (up to max_retries) then re-run; else return ALLOW/SANITIZED.
        return Report(Decision.ALLOW, raw_output, [], 0)


# --------------------------------------------------------------------------- #
# Simulated LLM retry + demo                                                   #
# --------------------------------------------------------------------------- #
def fake_llm_repair(bad_output: str, feedback: list[str]) -> str:
    text = " ".join(feedback).lower()
    if "json" in text or "schema" in text:
        return '{"answer": "42", "confidence": 0.9}'
    if "ground" in text:
        return "The Eiffel Tower stands 330 metres tall and was completed in 1889 [1]."
    return bad_output


def main() -> None:
    gw = OutputValidator()
    json_ctx = Context(expect_json=True, pydantic_model=AnswerModel,
                       required_fields={"answer": str, "confidence": float})
    eiffel_ctx = Context(grounding=[
        "The Eiffel Tower was completed in 1889. It stands 330 metres tall."])

    samples = [
        ("valid JSON",
         '{"answer": "Paris is the capital of France.", "confidence": 0.92}', json_ctx),
        ("PII leak",
         '{"answer": "Email john.doe@example.com.", "confidence": 0.8}', json_ctx),
        ("ungrounded claim",
         "The Eiffel Tower is 450 metres tall and was built in 1789.", eiffel_ctx),
        ("embedded script",
         "<script>fetch('/steal?c='+document.cookie)</script>", Context()),
        ("secret leak",
         "key: AKIAIOSFODNN7EXAMPLE password=Sup3rSecretValue123", Context()),
    ]
    for title, raw, ctx in samples:
        r = gw.validate(raw, ctx, fake_llm_repair)
        print(f"[{r.decision.value:<9}] {title}  (attempts={r.attempts})")


if __name__ == "__main__":
    main()
