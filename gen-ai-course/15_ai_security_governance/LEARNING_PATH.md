# 4-Hour Learning Path — AI Security & Governance Engineering

A guided sequence to take a beginner engineer from zero to **interview-ready** on runtime AI security
and governance controls. Budget ~4 hours. Each block = read `concepts.md` → run `solution.py` → do the
quiz → attempt the exercise if time allows.

> **How to work each topic (the loop):**
> 1. Read `concepts.md` (theory + threat model + code).
> 2. Run the reference code: `python solution.py` — watch it block/allow/redact/audit.
> 3. Take `quiz.md` (answers at the bottom).
> 4. Optional stretch: implement `exercise.py` yourself, compare to `solution.py`.

---

## Timeline

| Block | Time | Topic | Outcome |
|-------|------|-------|---------|
| Warm-up | 0:00–0:10 | This page + [OWASP LLM Top 10](https://genai.owasp.org/) skim | Shared threat vocabulary |
| 1 | 0:10–0:55 | [01_prompt_filtering](01_prompt_filtering/) | Stop malicious input before it reaches the model |
| 2 | 0:55–1:40 | [02_output_validation](02_output_validation/) | Stop unsafe/leaky/malformed output before it reaches the user |
| Break | 1:40–1:50 | — | — |
| 3 | 1:50–2:30 | [03_misuse_protection](03_misuse_protection/) | Prevent abuse, DoS, and cost blow-ups |
| 4 | 2:30–3:10 | [04_policy_as_code](04_policy_as_code/) | Enforce governance as versioned, testable code |
| 5 | 3:10–3:45 | [05_audit_traceability](05_audit_traceability/) | Produce audit evidence a regulator will accept |
| 6 | 3:45–4:15 | [06_safety_patterns](06_safety_patterns/) | Compose everything into one reusable gateway |
| Wrap | 4:15+ | [interview.md](interview.md) | Rehearse fundamentals + Senior Deep Dive |

*(Blocks 4–6 run tight; the 4-hour target assumes you skim exercises and focus on concepts + running the
solutions. Add ~1 hour if you code every exercise from scratch.)*

---

## The mental model to hold throughout

Every AI request should pass through a **control plane** with five checkpoints. This module builds one per topic,
then assembles them in Topic 6:

```
                 ┌──────────────────────────────────────────────────────────┐
   user ───────▶ │  [1] INPUT FILTER  →  [4] POLICY CHECK  →  ( LLM / AGENT ) │
                 │                                              │             │
   user ◀─────── │  [5] AUDIT LOG  ◀──  [2] OUTPUT VALIDATION ◀─┘             │
                 │            ▲                                               │
                 │            └── [3] MISUSE GUARD (rate/cost/abuse) wraps all│
                 └──────────────────────────────────────────────────────────┘
   Fail-closed: any checkpoint may BLOCK or escalate to human review.
```

- **[1] Input filter** (Topic 1) — is this prompt an attack?
- **[2] Output validation** (Topic 2) — is this response safe, grounded, well-formed, leak-free?
- **[3] Misuse guard** (Topic 3) — is this user within rate/cost/abuse limits?
- **[4] Policy check** (Topic 4) — is this use-case *allowed* by governance rules right now?
- **[5] Audit** (Topic 5) — record everything, tamper-evidently.
- **[6] Safety patterns** (Topic 6) — the reusable framework that wires 1–5 into every agent.

Keep asking: *"Which checkpoint catches this attack? What happens if it fails open?"*

---

## Self-assessment — you've mastered this module when you can…

- [ ] Explain prompt injection (direct vs indirect) and name **three** layered defenses.
- [ ] Justify why output validation is needed *even if* input filtering is perfect.
- [ ] Implement a token-bucket rate limiter and an abuse-score suspension from memory.
- [ ] Write a policy rule in a rule engine and explain the PEP/PDP/PIP model.
- [ ] Explain why audit logs must be append-only/hash-chained and what to log per request.
- [ ] Draw the centralized AI security gateway and argue fail-closed vs fail-open.
- [ ] Map each OWASP LLM risk to a concrete control you'd build.
- [ ] Answer the Senior Deep Dive questions in [interview.md](interview.md).

---

## After this module

- Pair with [Module 10: AI Governance](../10_governance/) for the policy/compliance and Responsible-AI side.
- Pair with [Module 09: Monitoring](../09_monitoring/) — security controls feed monitoring/alerting.
- See [interview_preparation_guide.md](../interview_preparation_guide.md) for the consolidated Senior Deep Dive index.
