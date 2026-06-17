# Module 10: AI Governance & Compliance — Quiz

## Instructions
- **20 Multiple Choice Questions** covering Sections 10.1–10.3
- Select the best answer for each question
- Click on each question to reveal the answer
- Score yourself at the end using the interpretation table

---

### Question 1
Which AI risk involves the model generating plausible but factually incorrect information?

A) Data Leakage
B) Prompt Injection
C) Hallucination
D) Model Drift

<details>
<summary>Answer</summary>
**C) Hallucination** — Hallucination occurs when a model generates outputs that sound confident and plausible but are factually wrong or fabricated. Data leakage exposes training data, prompt injection manipulates behavior, and model drift is performance degradation over time.
</details>

---

### Question 2
What is the primary purpose of input guardrails in an AI system?

A) To improve model accuracy
B) To sanitize, validate, and filter user inputs before they reach the model
C) To encrypt model weights
D) To increase inference speed

<details>
<summary>Answer</summary>
**B) To sanitize, validate, and filter user inputs before they reach the model** — Input guardrails act as a protective layer that screens user inputs for injection attacks, PII, excessive length, and disallowed content before the model processes them.
</details>

---

### Question 3
Which of the following is NOT one of the five pillars of Responsible AI?

A) Fairness
B) Profitability
C) Transparency
D) Safety

<details>
<summary>Answer</summary>
**B) Profitability** — The five pillars are Fairness, Transparency, Accountability, Privacy, and Safety. Profitability is a business objective, not a responsible AI principle.
</details>

---

### Question 4
Prompt injection attacks work by:

A) Injecting malicious code into the model's weights
B) Manipulating user input to override the model's system instructions
C) Corrupting the training dataset
D) DDoS-ing the inference endpoint

<details>
<summary>Answer</summary>
**B) Manipulating user input to override the model's system instructions** — Prompt injection involves crafting inputs that trick the model into ignoring its original instructions and following the attacker's directives instead. It does not alter model weights or training data.
</details>

---

### Question 5
What does the GDPR "right to be forgotten" (Article 17) require for AI systems?

A) Models must forget their training after deployment
B) Organizations must delete an individual's personal data upon request, including from training datasets
C) Users can request the model to forget a conversation
D) AI systems must automatically delete data after 30 days

<details>
<summary>Answer</summary>
**B) Organizations must delete an individual's personal data upon request, including from training datasets** — Article 17 gives individuals the right to have their personal data erased. In AI contexts, this can require removing data from training sets, retraining models, or implementing machine unlearning techniques.
</details>

---

### Question 6
Which HIPAA method removes 18 categories of identifiers from health records?

A) Expert Determination
B) Safe Harbor
C) Limited Dataset
D) Differential Privacy

<details>
<summary>Answer</summary>
**B) Safe Harbor** — The Safe Harbor method requires removing all 18 HIPAA-specified identifiers (names, dates, SSNs, addresses, etc.) to de-identify health data. Expert Determination uses statistical methods, and Limited Dataset retains some identifiers under a data use agreement.
</details>

---

### Question 7
Under the EU AI Act, which risk tier requires a conformity assessment and registration in an EU database?

A) Minimal Risk
B) Limited Risk
C) High Risk
D) Unacceptable Risk

<details>
<summary>Answer</summary>
**C) High Risk** — High-risk AI systems must undergo conformity assessments, maintain technical documentation, implement risk management systems, ensure human oversight, and register in the EU database. Unacceptable risk systems are prohibited entirely.
</details>

---

### Question 8
What is a model card?

A) A credit card used to pay for cloud AI services
B) A standardized document describing a model's purpose, performance, limitations, and ethical considerations
C) A GPU hardware specification
D) A license key for model deployment

<details>
<summary>Answer</summary>
**B) A standardized document describing a model's purpose, performance, limitations, and ethical considerations** — Model cards provide transparency by documenting intended use, performance metrics across groups, known limitations, and fairness evaluations, enabling informed decision-making.
</details>

---

### Question 9
Which fairness metric measures whether positive prediction rates are similar across demographic groups?

A) Equalized Odds
B) Demographic Parity
C) Calibration
D) Predictive Parity

<details>
<summary>Answer</summary>
**B) Demographic Parity** — Demographic parity requires that the probability of a positive prediction is the same across all groups: P(Ŷ=1|A=0) = P(Ŷ=1|A=1). Equalized odds additionally conditions on the true label, requiring equal TPR and FPR across groups.
</details>

---

### Question 10
NeMo Guardrails uses which language for defining conversational flows and safety rules?

A) Python
B) YAML
C) Colang
D) SQL

<details>
<summary>Answer</summary>
**C) Colang** — NeMo Guardrails uses Colang (a DSL for conversational AI) to define guardrail flows, user/bot messages, and safety checks. Configuration files use YAML, but the conversational logic is written in Colang.
</details>

---

### Question 11
What is the primary goal of differential privacy?

A) To encrypt all data at rest
B) To provide mathematical guarantees that individual records cannot be inferred from aggregate query results
C) To anonymize data by removing names
D) To compress data for efficient storage

<details>
<summary>Answer</summary>
**B) To provide mathematical guarantees that individual records cannot be inferred from aggregate query results** — Differential privacy adds calibrated noise to outputs, quantified by the epsilon parameter, ensuring that the inclusion or exclusion of any single record does not significantly change the result.
</details>

---

### Question 12
Under GDPR Article 22, individuals have the right to:

A) Access any AI model's source code
B) Not be subject to solely automated decisions that produce legal or similarly significant effects
C) Force companies to retrain models on their data
D) Delete any AI system that uses their data

<details>
<summary>Answer</summary>
**B) Not be subject to solely automated decisions that produce legal or similarly significant effects** — Article 22 provides protection against purely automated decision-making that significantly affects individuals, requiring human intervention, the ability to express views, and the right to contest the decision.
</details>

---

### Question 13
Which of the following is classified as an UNACCEPTABLE (prohibited) practice under the EU AI Act?

A) Using AI for spam filtering
B) Real-time remote biometric identification in publicly accessible spaces for law enforcement
C) Deploying a chatbot without disclosure
D) Using AI for credit scoring

<details>
<summary>Answer</summary>
**B) Real-time remote biometric identification in publicly accessible spaces for law enforcement** — The EU AI Act prohibits real-time biometric surveillance in public spaces by law enforcement, with narrow exceptions. Chatbots without disclosure are limited risk, credit scoring is high risk, and spam filtering is minimal risk.
</details>

---

### Question 14
What is the purpose of the "minimum necessary" principle in HIPAA?

A) To minimize the cost of healthcare
B) To limit PHI use and disclosure to only what is needed for the intended purpose
C) To reduce model complexity
D) To minimize inference latency

<details>
<summary>Answer</summary>
**B) To limit PHI use and disclosure to only what is needed for the intended purpose** — The minimum necessary standard requires covered entities to make reasonable efforts to limit access to and use of PHI to the minimum amount necessary to accomplish the intended purpose.
</details>

---

### Question 15
Which data privacy pattern ensures each record is indistinguishable from at least k-1 other records?

A) Pseudonymization
B) Differential Privacy
C) K-Anonymity
D) Data Minimization

<details>
<summary>Answer</summary>
**C) K-Anonymity** — K-anonymity ensures that every combination of quasi-identifier values appears in at least k records, making each individual indistinguishable from at least k-1 others within the dataset.
</details>

---

### Question 16
What should a comprehensive AI audit framework include?

A) Only pre-deployment testing
B) Pre-deployment testing, deployment controls, and post-deployment monitoring
C) Only post-deployment monitoring
D) Only model accuracy metrics

<details>
<summary>Answer</summary>
**B) Pre-deployment testing, deployment controls, and post-deployment monitoring** — A comprehensive audit framework covers the entire lifecycle: bias testing and red-teaming before deployment, monitoring and rollback mechanisms during deployment, and ongoing performance reviews and bias audits after deployment.
</details>

---

### Question 17
Which output guardrail technique cross-references model claims against verified knowledge bases?

A) PII redaction
B) Toxicity screening
C) Factuality checking
D) Format validation

<details>
<summary>Answer</summary>
**C) Factuality checking** — Factuality checks verify model outputs against trusted knowledge bases, databases, or retrieval systems to detect hallucinations and misinformation. PII redaction removes personal data, toxicity screening filters harmful content, and format validation checks structural correctness.
</details>

---

### Question 18
What does the term "model drift" refer to?

A) The model physically moving between servers
B) A degradation in model performance as the underlying data distribution changes over time
C) Users switching to a different model
D) The model generating random outputs

<details>
<summary>Answer</summary>
**B) A degradation in model performance as the underlying data distribution changes over time** — Model drift (or data drift) occurs when the statistical properties of the production data diverge from the training data, causing the model's predictions to become less accurate. It requires continuous monitoring and periodic retraining.
</details>

---

### Question 19
Which of the following is a required element for HIGH-RISK AI systems under the EU AI Act?

A) A marketing budget
B) A risk management system and human oversight measures
C) A patent filing
D) Social media presence

<details>
<summary>Answer</summary>
**B) A risk management system and human oversight measures** — High-risk AI systems must implement risk management, data governance, technical documentation, record-keeping, transparency, human oversight, accuracy, robustness, and cybersecurity standards.
</details>

---

### Question 20
What is the primary difference between anonymization and pseudonymization?

A) Anonymization is faster
B) Anonymization is irreversible; pseudonymization allows re-identification with a key
C) Pseudonymization is required by HIPAA
D) Anonymization only works for text data

<details>
<summary>Answer</summary>
**B) Anonymization is irreversible; pseudonymization allows re-identification with a key** — Anonymization permanently removes all links to identity and cannot be reversed. Pseudonymization replaces identifiers with tokens that can be reversed using a separate key, maintaining re-identification capability for authorized parties.
</details>

---

## Score Interpretation

| Score | Level | Recommendation |
|---|---|---|
| **18–20** | Expert | Strong grasp of AI governance. Consider leading governance initiatives at your organization. |
| **14–17** | Proficient | Solid understanding. Review the areas where you missed questions and study the relevant concepts. |
| **10–13** | Intermediate | Good foundation. Revisit sections 10.1–10.3 and focus on regulatory frameworks. |
| **6–9** | Developing | Needs reinforcement. Study all concept sections thoroughly and review code examples. |
| **0–5** | Beginner | Start with Section 10.1 and work through each section systematically. Focus on the risk taxonomy first. |

---

## Bonus: Senior / JD-Aligned Questions (AI Risk Management & Responsible AI)

> Self-contained — answer follows each question. See the [interview-questions.md](interview-questions.md) *Senior Deep Dive* for full explanations.

### BQ1. Which supervisory guidance is the foundation of Model Risk Management for banks, requiring independent "effective challenge"?

A) GDPR Article 22  
B) SR 11-7 (Fed/OCC); UK equivalent PRA SS1/23  
C) ISO 9001  
D) PCI-DSS  

**Answer: B** — SR 11-7 defines model risk governance, the three lines of defence, and independent validation. GDPR Art. 22 is about automated decisions, not model risk per se.

### BQ2. A regulator requires per-decision reason codes for a credit model. Which technique most directly supports this?

A) Increasing model temperature  
B) SHAP feature attributions mapped to human-readable, non-discriminatory reason codes  
C) Dropout at inference  
D) Larger embedding dimensions  

**Answer: B** — SHAP gives locally accurate attributions; you must still map them to stable, lawful reason codes. Monotonic-constrained GBMs or scorecards also help.

### BQ3. Why can't you generally satisfy both within-group calibration and equalized odds at the same time?

A) It's a software bug in Fairlearn  
B) Because of an impossibility result when base rates differ across groups — fairness becomes a business/legal trade-off  
C) Calibration is illegal under the EU AI Act  
D) Equalized odds only applies to images  

**Answer: B** — when base rates differ, these fairness criteria are mathematically incompatible; you choose the operating point deliberately.

### BQ4. Under the EU AI Act, credit scoring and insurance pricing are classified as:

A) Minimal risk — no obligations  
B) Prohibited  
C) High-risk — requiring conformity assessment, risk management, human oversight, logging, and transparency  
D) Out of scope  

**Answer: C** — high-risk systems carry the heaviest obligations short of prohibition.

### BQ5. Which Azure capability detects when a RAG answer is *not grounded* in the retrieved sources?

A) Azure Key Vault  
B) Azure AI Content Safety groundedness detection (and Foundry groundedness evaluators)  
C) Azure Blob Storage  
D) Azure DevOps Pipelines  

**Answer: B** — groundedness detection flags ungrounded (hallucinated) claims; pair it with content-safety filters and prompt shields.

### BQ6. A previously accurate risk model now shows PSI > 0.25 on key features in production. The first MRM-appropriate action is to:

A) Ignore it until the next annual review  
B) Trigger the drift alert, contain via fallback/human review for material decisions, then diagnose and revalidate before redeploying  
C) Immediately delete the model  
D) Increase the learning rate  

**Answer: B** — never silently keep serving a drifting risk model; contain, diagnose (drift vs data break vs feedback loop), remediate, and revalidate through the second line.
