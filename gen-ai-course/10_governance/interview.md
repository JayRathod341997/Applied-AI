# AI Governance - Interview Questions

This document contains interview questions and answers covering Module 10: AI Governance.

---

## 1. Risks and Guardrails

### Q1: What are the main risks in GenAI systems?

**Answer:** Primary risks:

- **Hallucinations:** Confident but incorrect outputs
- **Bias:** Perpetuating societal biases from training data
- **Prompt Injection:** Malicious manipulation of prompts
- **Data Leakage:** Exposing sensitive information
- **Copyright Issues:** Generating copyrighted content
- **Misinformation:** Creating fake but believable content
- **Security:** Vulnerabilities in AI pipelines

---

### Q2: What is prompt injection and how do you prevent it?

**Answer:** Prompt injection occurs when malicious users inject instructions into prompts to override system behavior.

**Types:**
- Direct injection: "Ignore previous instructions and..."
- Indirect injection: Via retrieved content or documents

**Prevention:**
- Input validation and sanitization
- Instruction boundaries using delimiters
- Separate system prompts from user input
- Output validation
- Monitoring for injection patterns

---

### Q3: What are content moderation and toxicity filters?

**Answer:** Content moderation involves:

- **Input Filtering:** Check user prompts for harmful content
- **Output Filtering:** Scan LLM responses before returning
- **Categories:** Violence, hate speech, sexual content, self-harm
- **Implementation:** 
  - Pre-built APIs (Moderation API, Perspective API)
  - Custom classifiers
  - Rule-based filters

---

### Q4: What is rate limiting and abuse prevention?

**Answer:** Rate limiting strategies:

- **Request Limits:** Max requests per minute/hour per user
- **Token Limits:** Max tokens per request
- **Cost Limits:** Budget controls
- **IP-based:** Prevent DDoS
- **Authentication:** Require API keys
- **Pricing Tiers:** Different limits for different plans

---

### Q5: What is PII redaction and masking?

**Answer:** PII handling:

- **Detection:** Identify PII in inputs and outputs
  - Names, emails, phones, addresses
  - SSN, credit cards, medical IDs
- **Redaction:** Replace with [REDACTED] or placeholders
- **Masking:** Partially hide (e.g., j***@example.com)
- **Tools:** Presidio, regex patterns, NER models

---

### Q6: How do you implement structured output validation?

**Answer:** Validation approach:

1. **Define Schema:** Use Pydantic or JSON Schema
2. **Parse Output:** Extract structured data from LLM response
3. **Validate:** Check against schema rules
4. **Retry:** If invalid, regenerate with stricter prompts
5. **Fallback:** Return error or partial data if validation fails

---

## 2. Responsible AI

### Q7: What are the key principles of Responsible AI?

**Answer:** Key principles:

- **Fairness:** Prevent discrimination, ensure equal treatment
- **Transparency:** Explain how AI makes decisions
- **Accountability:** Clear ownership and responsibility
- **Privacy:** Protect user data
- **Safety:** Prevent harm to users
- **Human Control:** Humans remain in the loop

---

### Q8: How do you mitigate bias in GenAI systems?

**Answer:** Bias mitigation:

1. **Data Level:** 
   - Diverse, representative training data
   - Bias audits of data sources

2. **Model Level:**
   - Fine-tuning on balanced data
   - Debiasing techniques

3. **Output Level:**
   - Test across demographic groups
   - Add fairness constraints
   - Human review for sensitive cases

---

### Q9: What is explainability in AI systems?

**Answer:** Explainability involves:

- **Feature Importance:** Which inputs matter most?
- **Attention Visualization:** Where did model focus?
- **Retrieval Attribution:** Which sources supported the answer?
- **Confidence Scores:** How sure is the model?
- **Audit Trails:** Log decisions for review

Tools: SHAP, LIME, attention visualization, retrieval debugging

---

### Q10: How do you implement Human-in-the-Loop (HITL) design?

**Answer:** HITL implementation:

1. **Identify Critical Points:** Where mistakes are costly
2. **Define Triggers:** When to involve humans
3. **Design Interface:** How humans review/decide
4. **Handle Responses:** Integrate human decisions
5. **Continuous Improvement:** Learn from human feedback

---

## 3. Compliance

### Q11: What are key compliance regulations for AI?

**Answer:** Regulations include:

- **GDPR (EU):** Data privacy, right to explanation
- **CCPA (California):** Consumer data rights
- **HIPAA (Healthcare):** Medical data protection
- **SOC 2:** Security and availability
- **PCI DSS:** Payment card data
- **AI-specific:** EU AI Act, upcoming regulations

---

### Q12: What is the EU AI Act and how does it affect GenAI?

**Answer:** EU AI Act:

- **Risk-based Approach:** Different requirements for risk levels
- **High-risk AI:** Must meet strict requirements
  - Transparency
  - Human oversight
  - Documentation
  - Bias testing
- **GenAI Specific:** 
  - Must disclose AI-generated content
  - Publish training data summaries
  - Ensure copyright compliance

---

### Q13: How do you maintain audit trails for AI systems?

**Answer:** Audit trail components:

- **Request Logging:** User ID, timestamp, prompt
- **Response Logging:** Output, tokens used
- **Retrieval Logs:** What was retrieved
- **Decision Logs:** Why certain actions taken
- **Change Logs:** System, model, prompt versions
- **Access Logs:** Who accessed what

---

### Q14: What is incident response for AI failures?

**Answer:** Incident response:

1. **Detection:** Monitor for failures, user reports
2. **Triage:** Assess severity and scope
3. **Containment:** Stop the bleeding (disable feature, rollback)
4. **Investigation:** Root cause analysis
5. **Remediation:** Fix the issue
6. **Communication:** Notify stakeholders
7. **Post-mortem:** Document and improve

---

### Q15: How do you handle data minimization?

**Answer:** Data minimization:

- **Collect Only What's Needed:** Don't gather excess data
- **Retention Policies:** Delete after defined period
- **Anonymization:** Remove identifiers when possible
- **Access Controls:** Limit who sees what data
- **Purpose Limitation:** Use data only for stated purposes

---

## Production Guardrail Questions

### Q16: How do you implement guardrails in a RAG system?

**Answer:** Guardrail implementation:

1. **Input Guardrails:**
   - Prompt injection detection
   - PII detection in queries
   - Toxicity filtering

2. **Retrieval Guardrails:**
   - Access control filtering
   - Metadata-based restrictions

3. **Output Guardrails:**
   - Content filtering
   - PII redaction
   - Format validation
   - Fact-checking against sources

---

### Q17: What is role-based access in RAG?

**Answer:** RBAC implementation:

1. **Document Level:** Users can only access permitted documents
2. **Chunk Level:** Filter by sensitivity tags
3. **Query Level:** Restrict certain query types
4. **Output Level:** Redact based on user role

Implementation: 
- Add user context to retrieval queries
- Filter results based on permissions
- Audit all access

---

### Q18: How do you validate LLM outputs against schemas?

**Answer:** Validation process:

1. **Define Schema:** Use Pydantic models
2. **Parse Response:** Extract structured data
3. **Validate Types:** Check data types
4. **Validate Values:** Check ranges, enums
5. **Handle Errors:** Retry or return error
6. **Log Failures:** Track for debugging

---

## Security Questions

### Q19: What are common security vulnerabilities in GenAI?

**Answer:** Vulnerabilities:

- **Prompt Injection:** Attack via prompts
- **Data Exfiltration:** Leaking sensitive data
- **Model Inversion:** Reconstructing training data
- **Adversarial Attacks:** Malicious inputs
- **API Security:** Unprotected endpoints
- **Dependency Vulnerabilities:** Compromised libraries

---

### Q20: How do you secure LLM API endpoints?

**Answer:** Security measures:

- **Authentication:** API keys, OAuth, JWT
- **Authorization:** Check permissions per request
- **Rate Limiting:** Prevent abuse
- **Input Validation:** Sanitize all inputs
- **Output Filtering:** Scan for sensitive data
- **TLS:** Encrypt all traffic
- **Logging:** Audit all access

---

## Follow-up Questions

### Q21: How do you test guardrail effectiveness?

**Answer:** Testing approach:

1. **Red Team Testing:** Try to bypass guards
2. **Edge Cases:** Test boundary conditions
3. **Adversarial Testing:** Malicious inputs
4. **Regression Testing:** Ensure fixes don't break
5. **Real Traffic Analysis:** Monitor production
6. **User Feedback:** Report inappropriate outputs

---

### Q22: What is the difference between guardrails and governance?

**Answer:**

| Aspect | Guardrails | Governance |
|--------|-----------|------------|
| Scope | Technical controls | Policy/framework |
| Implementation | Code, APIs | Processes, people |
| Timing | Runtime | Design-time + runtime |
| Examples | Filters, validation | Policies, reviews |

Both needed: Governance defines rules, guardrails enforce them

---

### Q23: How do you handle copyright issues with generated content?

**Answer:** Handling approaches:

1. **Training Data:** Use licensed/permitted data
2. **Output:** Don't reproduce copyrighted text verbatim
3. **Attribution:** Credit sources when possible
4. **Monitoring:** Check for copyrighted outputs
5. **Legal Review:** Consult IP lawyers
6. **Insurance:** Consider AI liability coverage

---

### Q24: What metrics would you track for AI governance?

**Answer:** Governance metrics:

- **Security:** Incidents, vulnerabilities
- **Compliance:** Audit findings, violations
- **Fairness:** Bias tests, complaints
- **Safety:** Harmful content detected
- **Privacy:** PII breaches, access violations
- **Accountability:** Response times, resolutions

---

## Scenario Questions

### Q25: A user asks your chatbot to generate harmful content. How do you handle this?

**Answer:** Response:

1. **Input Filter:** Detect harmful intent in query
2. **Refusal:** Politely decline with explanation
3. **Alternative:** Offer safe alternative if possible
4. **Log:** Record the attempt
5. **Escalate:** If severe, notify security team

---

### Q26: Your system generates factually incorrect information that causes harm. What do you do?

**Answer:** Response:

1. **Immediate:** Disable feature or add warning
2. **Investigate:** Root cause analysis
3. **Fix:** Add verification, improve retrieval
4. **Communicate:** Notify affected users
5. **Report:** Document for compliance
6. **Prevent:** Add guardrails to prevent recurrence

---

## Senior Deep Dive: AI in Risk Management & Responsible AI (Regulated/Global)

> *For roles deploying AI/ML in risk management at global, regulated enterprises. Interviewers test whether you can ship models that survive model-risk audits, regulators, and independent challenge — not just accurate ones.*

### Q: What is Model Risk Management (MRM) and how does SR 11-7 shape how you build models?

**Answer:** **MRM** is the discipline of identifying, measuring, and controlling the risk that a model is wrong or misused. The foundational guidance is the US Fed/OCC **SR 11-7**; the UK equivalent is the PRA's **SS1/23**. Engineering implications: build for **"effective challenge"** by an independent validation function (documented assumptions, reproducible training, data lineage); operate the **three lines of defence** (developers → independent validation/MRM → internal audit); govern the **full lifecycle** (development → validation → approval → monitoring → revalidation → retirement); maintain a **model inventory** with risk tiers (materiality × complexity) driving validation depth; and provide **conceptual soundness + outcomes analysis + benchmarking**, not just a test metric. **LLM wrinkle:** SR 11-7 predates GenAI — a non-deterministic, third-party, opaque LLM stresses reproducibility, explainability, and vendor dependency. Senior move: treat the *whole system* (prompts + retrieval + guardrails + pinned model version) as the model under management, log all I/O, and add LLM-specific validation (hallucination rate, jailbreak resistance, prompt-injection tests).

### Q: How do you make a credit/risk model explainable enough for regulators and adverse-action notices?

**Answer:** Two layers. **(1) Intrinsic interpretability** where possible — regulators (e.g. ECOA/Reg B requiring adverse-action reason codes) favor explainable models: logistic regression / scorecards (WoE binning) or **monotonic-constrained GBMs** (`monotone_constraints`) that enforce sensible directionality (more missed payments never lowers risk). **(2) Post-hoc explanations** for complex models — **SHAP** (locally accurate, consistent; the de-facto standard for per-decision reason codes), **LIME** (cheaper, less stable), **counterfactuals** ("minimal change that flips the decision" → maps to recourse), and PDP/ALE for global behavior. Nuance: SHAP gives *attribution*, not a legally sufficient *reason* — you must map features to human-readable, non-discriminatory, stable reason codes and watch proxy features (ZIP proxying race). For LLMs, "explainability" becomes citation/grounding + decision logs, not SHAP.

### Q: How do you detect and mitigate bias/fairness in a risk model?

**Answer:** **Measure** across protected groups with complementary, sometimes-conflicting metrics: demographic parity (equal approval rates), equal opportunity (equal TPR), equalized odds (equal TPR **and** FPR), disparate-impact ratio (<0.8 = "four-fifths rule" flag), and within-group calibration. Cite the **impossibility result**: you generally can't satisfy calibration *and* equalized odds when base rates differ — fairness is a business/legal trade-off. **Mitigate** at three stages: pre-processing (reweighing, resampling), in-processing (fairness constraints / adversarial debiasing), post-processing (group thresholds — legally sensitive, get counsel). Tools: **Fairlearn** (tight with Azure ML), AIF360.

### Q: Which regulations/frameworks must a global AI risk system account for?

**Answer:** **EU AI Act** (risk-tiered; credit scoring & insurance pricing are **high-risk** → conformity assessment, risk-management system, data governance, human oversight, logging, transparency; phased 2025–2027); **GDPR Art. 22** (no solely-automated decisions with significant effect without meaningful human review + explanation); **SR 11-7 / PRA SS1/23** (MRM); **NIST AI RMF** (Govern/Map/Measure/Manage) and certifiable **ISO/IEC 42001**; sector rules (Basel capital models, IFRS 9 / CECL expected-credit-loss, fair-lending ECOA/FCRA); and **data residency/sovereignty** (Azure region selection, EU Data Boundary). Map each to concrete controls so an auditor sees evidence (model inventory, validation reports, monitoring logs, human-oversight records), not intentions.

### Q: How do you operationalize responsible AI on Azure specifically?

**Answer:** Map principles to services: **Azure ML Responsible AI dashboard** (error analysis, SHAP interpretability, Fairlearn fairness, counterfactuals, causal analysis → exportable **Responsible AI scorecard** as audit evidence); **Azure AI Content Safety** (hate/sexual/violence/self-harm filters, **prompt shields** for jailbreak/injection, **groundedness detection** for ungrounded RAG answers); **Azure AI Foundry evaluations** (groundedness/relevance/coherence/safety in CI and on prod samples); **model cards + MLflow lineage** in the Azure ML registry; **Microsoft Purview** (data classification, lineage, DLP); and **human-in-the-loop + full request/response logging** (Azure Monitor / Log Analytics) for Art. 22 and the audit trail.

---

## Summary

Key governance topics:

1. **Risks:** Hallucinations, bias, security
2. **Guardrails:** Input/output filtering, validation
3. **Responsible AI:** Fairness, transparency, accountability
4. **Compliance:** GDPR, EU AI Act, audit trails
5. **Security:** API protection, incident response

---

## References

- [Guardrails Documentation](references.md)
- [AI Ethics Guidelines](references.md)
- [Compliance Frameworks](references.md)
