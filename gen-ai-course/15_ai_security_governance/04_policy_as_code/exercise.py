"""
exercise.py - STARTER scaffold: build a Python policy engine for AI governance.

Fill in the TODOs. When done, `python exercise.py` should behave like solution.py:
load the sample policy, evaluate each request, and print a decision + which rule fired.

Rules of the game:
  - A rule = {id, description, effect, priority, when:[conditions]}.
  - A condition = {field, op, value}. A rule matches when ALL conditions are true (AND).
  - Effects: ALLOW, REQUIRE_REVIEW, DENY. Most-restrictive-wins (DENY > REQUIRE_REVIEW > ALLOW).
  - evaluate() must return a Decision carrying the winning effect AND the matched-rule trace
    (audit evidence: you must be able to answer "which rule denied this and why?").

No network, no third-party deps. Standard library only.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Callable


class Effect(str, Enum):
    ALLOW = "ALLOW"
    REQUIRE_REVIEW = "REQUIRE_REVIEW"
    DENY = "DENY"


# TODO 1: map each Effect to a restrictiveness rank so you can pick a winner
#         (DENY should outrank REQUIRE_REVIEW should outrank ALLOW).
_RESTRICTIVENESS: dict[Effect, int] = {
    Effect.ALLOW: 0,
    Effect.REQUIRE_REVIEW: 0,  # TODO: fix ranks
    Effect.DENY: 0,            # TODO: fix ranks
}


# TODO 2: implement the comparison operators used by conditions.
#         Each is a function(actual_from_context, expected_from_rule) -> bool.
OPERATORS: dict[str, Callable[[Any, Any], bool]] = {
    "eq": lambda a, b: False,       # TODO
    "ne": lambda a, b: False,       # TODO
    "in": lambda a, b: False,       # TODO
    "not_in": lambda a, b: False,   # TODO
    "gte": lambda a, b: False,      # TODO (guard against None)
    "is_true": lambda a, _b: False, # TODO
}


@dataclass(frozen=True)
class Condition:
    field: str
    op: str
    value: Any = None

    def evaluate(self, context: dict[str, Any]) -> bool:
        # TODO 3: look up context[self.field], apply OPERATORS[self.op].
        return False


@dataclass(frozen=True)
class Rule:
    id: str
    description: str
    effect: Effect
    when: tuple[Condition, ...]
    priority: int = 100

    def matches(self, context: dict[str, Any]) -> bool:
        # TODO 4: rule matches when ALL conditions are true (empty when == catch-all).
        return False


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


class PolicyEngine:
    def __init__(self, rules: list[Rule], default_effect: Effect = Effect.ALLOW):
        self.default_effect = default_effect
        self.rules = rules  # (optionally sort by priority for readable traces)

    @classmethod
    def from_policy(cls, policy: dict[str, Any]) -> "PolicyEngine":
        # TODO 5: parse the policy dict into Rule/Condition objects and return an engine.
        return cls([], default_effect=Effect(policy.get("default_effect", "ALLOW")))

    def evaluate(self, context: dict[str, Any]) -> Decision:
        # TODO 6:
        #   1. collect all matching rules
        #   2. if none, return Decision(default_effect, ...) with empty trace
        #   3. else pick the most-restrictive matched rule as the winner
        #   4. return a Decision with winner.effect, winner.id, and the full matched trace
        return Decision(self.default_effect, "not implemented", None, [])


SAMPLE_POLICY: dict[str, Any] = {
    "version": "2026-07-01",
    "default_effect": "ALLOW",
    "rules": [
        {
            "id": "AIA-001-usecase-approved",
            "description": "Deny if the use-case is not on the approved allow-list.",
            "effect": "DENY",
            "priority": 10,
            "when": [
                {"field": "use_case", "op": "not_in",
                 "value": ["customer_support", "code_assist", "internal_search"]},
            ],
        },
        {
            "id": "GDPR-A22-pii-external",
            "description": "Deny PII in a prompt sent to an external model.",
            "effect": "DENY",
            "priority": 20,
            "when": [
                {"field": "contains_pii", "op": "is_true"},
                {"field": "model_destination", "op": "eq", "value": "external"},
            ],
        },
        {
            "id": "NIST-RMF-high-risk-review",
            "description": "Require human review for high-risk-tier requests.",
            "effect": "REQUIRE_REVIEW",
            "priority": 30,
            "when": [{"field": "risk_tier", "op": "gte", "value": 3}],
        },
    ],
}

SAMPLE_REQUESTS: list[dict[str, Any]] = [
    {"label": "clean internal request", "user": "alice", "use_case": "customer_support",
     "risk_tier": 1, "contains_pii": False, "model_destination": "internal"},
    {"label": "PII to external model", "user": "bob", "use_case": "customer_support",
     "risk_tier": 2, "contains_pii": True, "model_destination": "external"},
    {"label": "unapproved use-case", "user": "carol", "use_case": "marketing_autogen",
     "risk_tier": 2, "contains_pii": False, "model_destination": "internal"},
    {"label": "high risk tier", "user": "dave", "use_case": "code_assist",
     "risk_tier": 4, "contains_pii": False, "model_destination": "internal"},
]


def main() -> None:
    engine = PolicyEngine.from_policy(SAMPLE_POLICY)
    print(f"Loaded {len(engine.rules)} rules (default={engine.default_effect.value}).\n")
    for req in SAMPLE_REQUESTS:
        label = req.pop("label")
        decision = engine.evaluate(req)
        print(f"REQUEST: {label}")
        print(f"  context : {json.dumps(req, sort_keys=True)}")
        print(f"  decision: {decision.effect.value} "
              f"(winner={decision.winning_rule_id}) :: {decision.reason}")
        print()


if __name__ == "__main__":
    main()
