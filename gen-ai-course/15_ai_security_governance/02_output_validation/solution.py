"""
Output Validation & Guardrails — reference solution.

Builds an `OutputValidator` that runs a CHAIN of validators over an LLM's raw
output and returns a `Report` with:
  - a decision  (ALLOW / SANITIZED / BLOCKED)
  - a sanitized output (redacted / encoded as needed)
  - the individual findings
  - a retry/repair hook that re-asks a (simulated) model on repairable failures.

Core principle: *LLM output is untrusted input to the next system.* Validate it
independently of the input, sanitize before downstream use, and never trust it as
code/markup.

Runs offline on the standard library. `pydantic` is used if installed; otherwise a
lightweight fallback schema check kicks in. No network, no API keys.

    python solution.py
"""

from __future__ import annotations

import html
import json
import re
from dataclasses import dataclass, field
from enum import Enum
from typing import Callable

# --------------------------------------------------------------------------- #
# Optional pydantic (graceful fallback)                                        #
# --------------------------------------------------------------------------- #
try:
    from pydantic import BaseModel, ValidationError

    _HAS_PYDANTIC = True

    class AnswerModel(BaseModel):
        answer: str
        confidence: float

except Exception:  # pydantic not installed -> fallback path
    _HAS_PYDANTIC = False
    AnswerModel = None  # type: ignore


# --------------------------------------------------------------------------- #
# Core types                                                                   #
# --------------------------------------------------------------------------- #
class Severity(Enum):
    INFO = "INFO"
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


class Action(Enum):
    """What a single validator wants the gateway to do."""
    PASS = "pass"        # nothing to do
    SANITIZE = "sanitize"  # continue, but with a modified output
    RETRY = "retry"      # repairable -> re-ask the model
    BLOCK = "block"      # unrecoverable -> reject outright


class Decision(Enum):
    """Final gateway verdict for the whole chain."""
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
    output: str | None = None  # replacement output when action == SANITIZE


@dataclass
class Context:
    """Everything a validator might need beyond the raw output itself."""
    grounding: list[str] = field(default_factory=list)  # RAG source passages
    expect_json: bool = False
    pydantic_model: type | None = None
    required_fields: dict[str, type] | None = None       # fallback schema


@dataclass
class Report:
    decision: Decision
    output: str
    findings: list[Finding]
    attempts: int


# --------------------------------------------------------------------------- #
# Validators                                                                   #
# --------------------------------------------------------------------------- #
class Validator:
    name = "base"

    def check(self, output: str, ctx: Context) -> Finding:  # pragma: no cover
        raise NotImplementedError


def _ok(name: str, msg: str = "ok") -> Finding:
    return Finding(name, True, Action.PASS, msg, Severity.INFO)


class SecretScanner(Validator):
    """Credentials must NEVER appear in an output. Block, don't redact-and-ship."""
    name = "secret_scan"
    PATTERNS = [
        re.compile(r"AKIA[0-9A-Z]{16}"),                       # AWS access key id
        re.compile(r"sk-[A-Za-z0-9]{20,}"),                    # OpenAI-style key
        re.compile(r"-----BEGIN (?:RSA )?PRIVATE KEY-----"),   # private key block
        re.compile(
            r"(?i)(?:api[_-]?key|secret|password|passwd|token)\s*[:=]\s*['\"]?[A-Za-z0-9/+=_\-]{8,}"
        ),
    ]

    def check(self, output: str, ctx: Context) -> Finding:
        for pat in self.PATTERNS:
            if pat.search(output):
                return Finding(
                    self.name, False, Action.BLOCK,
                    "credential/secret detected in output — response withheld",
                    Severity.CRITICAL,
                )
        return _ok(self.name, "no secrets")


class SchemaValidator(Validator):
    """Structured-output contract. Failures are repairable -> re-ask (RETRY)."""
    name = "schema"

    def check(self, output: str, ctx: Context) -> Finding:
        if not ctx.expect_json:
            return _ok(self.name, "n/a (free text)")
        try:
            obj = json.loads(output)
        except json.JSONDecodeError as e:
            return Finding(self.name, False, Action.RETRY,
                           f"invalid JSON: {e}", Severity.HIGH)

        errs: list[str] = []
        if ctx.pydantic_model is not None and _HAS_PYDANTIC:
            try:
                ctx.pydantic_model(**obj)
            except ValidationError as e:
                errs = [f"{'.'.join(map(str, er['loc']))}: {er['msg']}"
                        for er in e.errors()]
        elif ctx.required_fields:
            for fld, typ in ctx.required_fields.items():
                if fld not in obj:
                    errs.append(f"missing field '{fld}'")
                elif typ in (int, float) and not isinstance(obj[fld], (int, float)):
                    errs.append(f"'{fld}' must be numeric")
                elif typ is str and not isinstance(obj[fld], str):
                    errs.append(f"'{fld}' must be a string")

        if errs:
            return Finding(self.name, False, Action.RETRY,
                           "schema errors -> " + "; ".join(errs), Severity.HIGH)
        return _ok(self.name, "valid schema")


class PIIRedactor(Validator):
    """DLP on the way out. Redact-and-continue (Presidio-style, regex fallback)."""
    name = "pii_redact"
    RULES = [
        ("EMAIL", re.compile(r"[A-Za-z0-9._%+\-]+@[A-Za-z0-9.\-]+\.[A-Za-z]{2,}")),
        ("PHONE", re.compile(r"\+?\d[\d\-\s().]{7,}\d")),
        ("SSN", re.compile(r"\b\d{3}-\d{2}-\d{4}\b")),
        ("CREDIT_CARD", re.compile(r"\b(?:\d[ \-]?){13,16}\b")),
    ]

    def check(self, output: str, ctx: Context) -> Finding:
        redacted = output
        hits: list[str] = []
        for label, pat in self.RULES:
            if pat.search(redacted):
                hits.append(label)
                redacted = pat.sub(f"[REDACTED_{label}]", redacted)
        if hits:
            return Finding(self.name, False, Action.SANITIZE,
                           f"PII redacted: {', '.join(sorted(set(hits)))}",
                           Severity.MEDIUM, output=redacted)
        return _ok(self.name, "no PII")


class ToxicityFilter(Validator):
    """Denylist mask. A real system swaps this for a classifier (e.g. Detoxify)."""
    name = "toxicity"
    DENYLIST = {"idiot", "moron", "kill yourself", "slur_example"}

    def check(self, output: str, ctx: Context) -> Finding:
        lowered = output.lower()
        found = [w for w in self.DENYLIST if w in lowered]
        if found:
            masked = output
            for w in found:
                masked = re.sub(re.escape(w), "*" * len(w), masked, flags=re.I)
            return Finding(self.name, False, Action.SANITIZE,
                           f"toxic terms masked: {len(found)}",
                           Severity.MEDIUM, output=masked)
        return _ok(self.name, "clean")


class UnsafeContentScanner(Validator):
    """Insecure output handling (LLM05). HTML-encode active markup before render."""
    name = "unsafe_output"
    MARKERS = [
        re.compile(r"(?i)<\s*script"),
        re.compile(r"(?i)<\s*iframe"),
        re.compile(r"(?i)javascript:"),
        re.compile(r"(?i)\son\w+\s*="),  # onerror=, onclick=, ...
    ]

    def check(self, output: str, ctx: Context) -> Finding:
        if any(p.search(output) for p in self.MARKERS):
            # Encode the whole payload so it renders as inert text downstream.
            return Finding(self.name, False, Action.SANITIZE,
                           "active markup detected — output HTML-encoded",
                           Severity.HIGH, output=html.escape(output))
        return _ok(self.name, "no active markup")


class GroundednessChecker(Validator):
    """
    RAG factuality guard. An answer must be supported by the provided context.
    Cheap, deterministic proxy for an NLI model:
      * every numeric claim must appear in the sources, and
      * enough content words must overlap the sources.
    Unsupported -> RETRY with 'answer only from context' feedback.
    """
    name = "groundedness"
    STOP = {"this", "that", "with", "from", "have", "here", "there", "your",
            "about", "which", "were", "was", "and", "the", "for", "are"}
    THRESHOLD = 0.5

    def _words(self, text: str) -> list[str]:
        return [w for w in re.findall(r"[a-zA-Z]+", text.lower())
                if len(w) > 3 and w not in self.STOP]

    def check(self, output: str, ctx: Context) -> Finding:
        if not ctx.grounding:
            return _ok(self.name, "n/a (no context)")
        source = " ".join(ctx.grounding)
        src_words = set(self._words(source))
        src_nums = set(re.findall(r"\d+", source))

        # Ignore [1]-style citation markers when checking numeric claims.
        answer = re.sub(r"\[\d+\]", "", output)
        claim_nums = set(re.findall(r"\d+", answer))
        bad_nums = claim_nums - src_nums

        claim_words = self._words(output)
        overlap = (sum(w in src_words for w in claim_words) / len(claim_words)
                   if claim_words else 1.0)

        if bad_nums or overlap < self.THRESHOLD:
            why = []
            if bad_nums:
                why.append(f"unsupported figures {sorted(bad_nums)}")
            if overlap < self.THRESHOLD:
                why.append(f"low context overlap ({overlap:.0%})")
            return Finding(self.name, False, Action.RETRY,
                           "ungrounded claim — " + "; ".join(why),
                           Severity.HIGH)
        return _ok(self.name, f"grounded ({overlap:.0%} overlap)")


# --------------------------------------------------------------------------- #
# The gateway                                                                  #
# --------------------------------------------------------------------------- #
RepairFn = Callable[[str, list[str]], str]


class OutputValidator:
    """Runs a validator chain, applies sanitizations, and retries via a repair hook."""

    def __init__(self, validators: list[Validator] | None = None) -> None:
        self.validators = validators or [
            SecretScanner(),
            SchemaValidator(),
            PIIRedactor(),
            ToxicityFilter(),
            UnsafeContentScanner(),
            GroundednessChecker(),
        ]

    def validate(
        self,
        raw_output: str,
        ctx: Context,
        repair_fn: RepairFn | None = None,
        max_retries: int = 1,
    ) -> Report:
        current = raw_output
        attempt = 0

        while True:
            working = current
            findings: list[Finding] = []
            blocked = retry = changed = False

            for v in self.validators:
                f = v.check(working, ctx)
                findings.append(f)
                if f.action is Action.SANITIZE and f.output is not None:
                    working = f.output          # apply and keep going down the chain
                    changed = True
                elif f.action is Action.BLOCK:
                    blocked = True
                elif f.action is Action.RETRY:
                    retry = True

            if blocked:
                return Report(Decision.BLOCKED, working, findings, attempt)

            if retry and repair_fn is not None and attempt < max_retries:
                feedback = [f.message for f in findings if f.action is Action.RETRY]
                current = repair_fn(current, feedback)
                attempt += 1
                continue

            if retry:  # repairable but retries exhausted / no hook -> fail closed
                return Report(Decision.BLOCKED, working, findings, attempt)

            decision = Decision.SANITIZED if changed else Decision.ALLOW
            return Report(decision, working, findings, attempt)


# --------------------------------------------------------------------------- #
# Demo (simulated LLM + repair, fully offline)                                 #
# --------------------------------------------------------------------------- #
def fake_llm_repair(bad_output: str, feedback: list[str]) -> str:
    """Stand-in for a re-ask. Deterministic, network-free."""
    text = " ".join(feedback).lower()
    if "json" in text or "schema" in text:
        return '{"answer": "42", "confidence": 0.9}'
    if "ground" in text:
        return "The Eiffel Tower stands 330 metres tall and was completed in 1889 [1]."
    return bad_output


def _print(title: str, raw: str, report: Report) -> None:
    icon = {Decision.ALLOW: "ALLOW ", Decision.SANITIZED: "SANIT.",
            Decision.BLOCKED: "BLOCK "}[report.decision]
    print(f"\n[{icon}] {title}   (attempts={report.attempts})")
    print(f"   raw : {raw[:70]}{'...' if len(raw) > 70 else ''}")
    if report.output != raw:
        print(f"   out : {report.output[:70]}{'...' if len(report.output) > 70 else ''}")
    for f in report.findings:
        if not f.ok:
            print(f"     - {f.validator:<13} {f.severity.value:<8} {f.message}")


def main() -> None:
    gw = OutputValidator()
    json_ctx = Context(
        expect_json=True,
        pydantic_model=AnswerModel,
        required_fields={"answer": str, "confidence": float},
    )
    eiffel_ctx = Context(grounding=[
        "The Eiffel Tower was completed in 1889. It stands 330 metres tall."
    ])

    print("=" * 72)
    print("Output-validation gateway — demo")
    print(f"pydantic available: {_HAS_PYDANTIC}")
    print("=" * 72)

    # 1) Clean, schema-valid JSON  -> ALLOW
    s1 = '{"answer": "The capital of France is Paris.", "confidence": 0.92}'
    _print("valid JSON", s1, gw.validate(s1, json_ctx, fake_llm_repair))

    # 2) JSON leaking PII          -> SANITIZED (redacted)
    s2 = '{"answer": "Reach John at john.doe@example.com or +1-415-555-0132.", "confidence": 0.8}'
    _print("PII leak", s2, gw.validate(s2, json_ctx, fake_llm_repair))

    # 3) Ungrounded claim          -> RETRY -> repaired -> ALLOW
    s3 = "The Eiffel Tower is 450 metres tall and was built in 1789."
    _print("ungrounded claim", s3, gw.validate(s3, eiffel_ctx, fake_llm_repair))

    # 4) Embedded <script>         -> SANITIZED (HTML-encoded)
    s4 = "<b>Sure!</b> Paste this: <script>fetch('/steal?c='+document.cookie)</script>"
    _print("embedded script", s4, gw.validate(s4, Context(), fake_llm_repair))

    # 5) Leaked credential         -> BLOCKED
    s5 = "Here is the key: AKIAIOSFODNN7EXAMPLE and password=Sup3rSecretValue123"
    _print("secret leak", s5, gw.validate(s5, Context(), fake_llm_repair))

    print("\n" + "=" * 72)
    print("Every output is validated independently of the input before it ships.")
    print("=" * 72)


if __name__ == "__main__":
    main()
