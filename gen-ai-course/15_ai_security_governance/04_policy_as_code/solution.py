"""
solution.py - A small, dependency-free policy engine for AI governance.

Governance-through-code: a declarative ruleset (data) is evaluated against a
request context (data) to produce a DECISION plus a matched-rule TRACE for audit.
This mirrors how OPA/Rego works (input JSON -> decision) but in plain Python so you
can see every moving part.

Design:
  - PolicyEngine is the PDP (Policy Decision Point). It knows nothing about your app.
  - The calling code (see __main__) is the PEP (Policy Enforcement Point): it builds
    the context, asks the PDP for a decision, and enforces it.
  - Rules are declarative: {id, description, effect, priority, when: [conditions]}.
  - Effects: DENY > REQUIRE_REVIEW > ALLOW (deny always wins; most-restrictive-wins).
  - Every evaluation returns a trace listing which rules matched -> audit evidence.

Run:  python solution.py     (no network, no third-party deps)
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Callable

# --------------------------------------------------------------------------- #
# 1. Decision effects. Ordered by restrictiveness so we can pick a winner.
# --------------------------------------------------------------------------- #


class Effect(str, Enum):
    ALLOW = "ALLOW"
    REQUIRE_REVIEW = "REQUIRE_REVIEW"
    DENY = "DENY"


# Higher number == more restrictive == wins a conflict.
_RESTRICTIVENESS = {Effect.ALLOW: 0, Effect.REQUIRE_REVIEW: 1, Effect.DENY: 2}


# --------------------------------------------------------------------------- #
# 2. Condition operators. A rule matches when ALL of its conditions are true
#    (logical AND). Each condition is {field, op, value}.
# --------------------------------------------------------------------------- #

# op name -> function(actual_value_from_context, expected_value_from_rule) -> bool
OPERATORS: dict[str, Callable[[Any, Any], bool]] = {
    "eq": lambda a, b: a == b,
    "ne": lambda a, b: a != b,
    "in": lambda a, b: a in b,
    "not_in": lambda a, b: a not in b,
    "gte": lambda a, b: a is not None and a >= b,
    "lte": lambda a, b: a is not None and a <= b,
    "is_true": lambda a, _b: a is True,
    "is_false": lambda a, _b: a is False,
    "contains": lambda a, b: b in a if a is not None else False,
}


@dataclass(frozen=True)
class Condition:
    field: str
    op: str
    value: Any = None

    def evaluate(self, context: dict[str, Any]) -> bool:
        if self.op not in OPERATORS:
            raise ValueError(f"Unknown operator: {self.op!r}")
        actual = context.get(self.field)
        return OPERATORS[self.op](actual, self.value)


@dataclass(frozen=True)
class Rule:
    id: str
    description: str
    effect: Effect
    when: tuple[Condition, ...]
    priority: int = 100  # lower = evaluated/reported first; ties broken by restrictiveness

    def matches(self, context: dict[str, Any]) -> bool:
        # Empty `when` == catch-all (matches everything). Useful for default rules.
        return all(cond.evaluate(context) for cond in self.when)


# --------------------------------------------------------------------------- #
# 3. Decision object = what the PDP returns. Serializable for the audit log.
# --------------------------------------------------------------------------- #


@dataclass
class Decision:
    effect: Effect
    reason: str
    winning_rule_id: str | None
    matched_rules: list[dict[str, str]] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "effect": self.effect.value,
            "reason": self.reason,
            "winning_rule_id": self.winning_rule_id,
            "matched_rules": self.matched_rules,
        }


# --------------------------------------------------------------------------- #
# 4. The engine (PDP). Load rules once, evaluate many contexts.
# --------------------------------------------------------------------------- #


class PolicyEngine:
    def __init__(self, rules: list[Rule], default_effect: Effect = Effect.ALLOW):
        # Deny-by-default is safer for high-risk systems; default here is ALLOW so
        # the demo shows explicit rules firing. Flip to DENY for fail-closed posture.
        self.default_effect = default_effect
        # Stable order: by priority, then by restrictiveness (deny first) for readable traces.
        self.rules = sorted(
            rules, key=lambda r: (r.priority, -_RESTRICTIVENESS[r.effect])
        )

    @classmethod
    def from_policy(cls, policy: dict[str, Any]) -> "PolicyEngine":
        """Build an engine from a declarative policy document (JSON/YAML-shaped dict)."""
        rules = []
        for raw in policy.get("rules", []):
            conditions = tuple(
                Condition(field=c["field"], op=c["op"], value=c.get("value"))
                for c in raw.get("when", [])
            )
            rules.append(
                Rule(
                    id=raw["id"],
                    description=raw["description"],
                    effect=Effect(raw["effect"]),
                    when=conditions,
                    priority=raw.get("priority", 100),
                )
            )
        default = Effect(policy.get("default_effect", "ALLOW"))
        return cls(rules, default_effect=default)

    def evaluate(self, context: dict[str, Any]) -> Decision:
        matched = [r for r in self.rules if r.matches(context)]

        matched_trace = [
            {"id": r.id, "effect": r.effect.value, "description": r.description}
            for r in matched
        ]

        if not matched:
            return Decision(
                effect=self.default_effect,
                reason=f"No rule matched; falling back to default_effect={self.default_effect.value}",
                winning_rule_id=None,
                matched_rules=[],
            )

        # Most-restrictive-wins. DENY beats REQUIRE_REVIEW beats ALLOW.
        winner = max(matched, key=lambda r: _RESTRICTIVENESS[r.effect])
        return Decision(
            effect=winner.effect,
            reason=winner.description,
            winning_rule_id=winner.id,
            matched_rules=matched_trace,
        )


# --------------------------------------------------------------------------- #
# 5. Sample policy. In production this lives in a versioned file (policy.json /
#    policy.yaml / .rego) reviewed via PR and deployed by CI, NOT hard-coded.
# --------------------------------------------------------------------------- #

SAMPLE_POLICY: dict[str, Any] = {
    "version": "2026-07-01",
    "default_effect": "ALLOW",
    "rules": [
        {
            "id": "AIA-001-usecase-approved",
            "description": "Deny if the use-case is not on the approved-inventory allow-list.",
            "effect": "DENY",
            "priority": 10,
            "when": [
                {
                    "field": "use_case",
                    "op": "not_in",
                    "value": ["customer_support", "code_assist", "internal_search"],
                }
            ],
        },
        {
            "id": "GDPR-A22-pii-external",
            "description": "Deny PII in a prompt sent to an external/third-party model (data residency + GDPR Art.22).",
            "effect": "DENY",
            "priority": 20,
            "when": [
                {"field": "contains_pii", "op": "is_true"},
                {"field": "model_destination", "op": "eq", "value": "external"},
            ],
        },
        {
            "id": "NIST-RMF-high-risk-review",
            "description": "Require human review for high-risk-tier requests (NIST AI RMF MANAGE / EU AI Act high-risk).",
            "effect": "REQUIRE_REVIEW",
            "priority": 30,
            "when": [{"field": "risk_tier", "op": "gte", "value": 3}],
        },
        {
            "id": "SEC-untrusted-user-external",
            "description": "Require review when an untrusted (external) user targets an external model.",
            "effect": "REQUIRE_REVIEW",
            "priority": 40,
            "when": [
                {"field": "user_trust", "op": "eq", "value": "external"},
                {"field": "model_destination", "op": "eq", "value": "external"},
            ],
        },
    ],
}


# --------------------------------------------------------------------------- #
# 6. Sample requests (the "input JSON" a PEP would build per call).
# --------------------------------------------------------------------------- #

SAMPLE_REQUESTS: list[dict[str, Any]] = [
    {
        "label": "Approved support chat, internal model, no PII, low risk",
        "user": "alice", "user_trust": "internal", "use_case": "customer_support",
        "risk_tier": 1, "contains_pii": False, "model_destination": "internal",
    },
    {
        "label": "PII sent to an external model",
        "user": "bob", "user_trust": "internal", "use_case": "customer_support",
        "risk_tier": 2, "contains_pii": True, "model_destination": "external",
    },
    {
        "label": "Unapproved use-case (marketing_autogen)",
        "user": "carol", "user_trust": "internal", "use_case": "marketing_autogen",
        "risk_tier": 2, "contains_pii": False, "model_destination": "internal",
    },
    {
        "label": "High-risk tier -> human review",
        "user": "dave", "user_trust": "internal", "use_case": "code_assist",
        "risk_tier": 4, "contains_pii": False, "model_destination": "internal",
    },
    {
        "label": "Overlapping rules: unapproved use-case AND PII external (deny wins)",
        "user": "erin", "user_trust": "external", "use_case": "marketing_autogen",
        "risk_tier": 5, "contains_pii": True, "model_destination": "external",
    },
]


def _render(decision: Decision) -> str:
    icon = {"ALLOW": "[ALLOW]", "REQUIRE_REVIEW": "[REVIEW]", "DENY": "[DENY ]"}[
        decision.effect.value
    ]
    return f"{icon} winner={decision.winning_rule_id or '<default>'} :: {decision.reason}"


def main() -> None:
    engine = PolicyEngine.from_policy(SAMPLE_POLICY)
    print(f"Loaded policy version {SAMPLE_POLICY['version']} "
          f"with {len(engine.rules)} rules (default={engine.default_effect.value}).\n")

    audit_log: list[dict[str, Any]] = []
    for req in SAMPLE_REQUESTS:
        label = req.pop("label")
        decision = engine.evaluate(req)
        print(f"REQUEST: {label}")
        print(f"  context: {json.dumps(req, sort_keys=True)}")
        print(f"  {_render(decision)}")
        if decision.matched_rules:
            for m in decision.matched_rules:
                mark = "  <== winner" if m["id"] == decision.winning_rule_id else ""
                print(f"    - matched {m['id']} ({m['effect']}){mark}")
        print()

        audit_log.append({
            "user": req["user"],
            "use_case": req["use_case"],
            "decision": decision.to_dict(),
        })

    print("=" * 68)
    print("AUDIT LOG (one JSON line per request; ship this to your SIEM/WORM store):")
    for entry in audit_log:
        print(json.dumps(entry, sort_keys=True))


if __name__ == "__main__":
    main()
