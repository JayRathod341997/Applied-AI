# Hallucination Theory for RAG Systems

## Root Causes in RAG Systems

Hallucinations in Retrieval-Augmented Generation arise from failures across multiple stages of the pipeline. Identifying these root causes is essential for designing systems that produce accurate, grounded responses.

### 1. Retrieval Failures

The retrieval stage may fetch irrelevant or insufficient context, leaving the generator without proper grounding.

**Example:** A query asking "What is our company's remote work policy?" retrieves documents about office hours instead because the embedding model was trained on general text rather than domain-specific data. The generated response then fabricates policy details that sound plausible but do not exist in any source document.

### 2. Chunking Boundary Issues

Improper document chunking can split related information across retrieval units, preventing the model from synthesizing complete answers.

**Example:** A technical document explaining a three-step process is chunked so that steps one and two appear in one chunk while step three appears in a non-retrieved chunk. The generated response includes only partial instructions, creating an incomplete or incorrect answer.

### 3. Knowledge Base Quality Issues

The vector database may contain outdated, inconsistent, or incomplete source documents.

**Example:** The knowledge base holds two versions of a product pricing document—2024 and 2025. The retrieval system fetches the older version, and the generated response provides incorrect pricing that conflicts with current rates.

### 4. Context Integration Failures

The model may struggle to integrate multiple retrieved contexts, especially when they contain conflicting information.

**Example:** Three documents are retrieved about a meeting: two state "3 PM" and one states "5 PM." Without explicit resolution instructions, the model generates a fabricated time or defaults to one source without acknowledgment.

### 5. Weak Prompt Engineering

Insufficient prompting can leave the model without clear instructions to ground responses in the provided context.

**Example:** A generic prompt like "Answer the question based on the following context" does not require citations or explicit grounding. The model feels confident generating details beyond what the context supports.

### 6. Model Configuration Issues

High temperature settings encourage the model to generate novel—yet ungrounded—content.

**Example:** With temperature set to 0.8, a model explaining a retrieved concept adds creative interpretations unsupported by the source material.

## Hallucination Detection Methods

Robust hallucination detection requires multiple strategies applied at different pipeline stages. Each method has distinct strengths and limitations.

### 1. Confidence Scoring

This method evaluates the probability distribution of token predictions to identify uncertain outputs.

**Mechanism:** The model assigns probability scores to each generated token. Low-confidence tokens (below a threshold, e.g., 0.6) are flagged for review. Aggregating token-level scores provides passage-level confidence.

**Use Case:** A customer support chatbot generates "Our data retention policy states we keep logs for 90 days." The token "90" scores 0.45 confidence. The system flags the response for verification before delivery.

### 2. Semantic Similarity Checks

This method compares semantic alignment between the generated response and retrieved context.

**Mechanism:** Embedding models generate vector representations of context and response. Cosine similarity below 0.7 suggests the response has drifted from source material.

**Use Case:** Retrieved context states "Server restart takes approximately 5 minutes." Generated response claims "Server restart takes approximately 2 hours." Similarity drops to 0.52, triggering review.

### 3. Grounding Verification

This method requires responses to cite specific source passages, enabling traceability.

**Mechanism:** Prompts instruct the model to include citations (e.g., [source 1]). A secondary check validates that each cited source contains the claimed information. Uncited claims are flagged.

**Use Case:** A legal assistant generates "According to Section 4.2, the liability cap is $100,000 [source 3]." Verification confirms source 3 contains this provision. Response passes.

### 4. Contradiction Detection

This method identifies logical inconsistencies within responses or between responses and sources.

**Mechanism:** Natural Language Inference (NLI) models classify statement pairs as entailment, contradiction, or neutral. Detected contradictions trigger warnings.

**Use Case:** Retrieved context states "All employees must complete training by January 1." Generated response says "Employees have until February 1." Contradiction detected; response corrected.

### 5. Self-Consistency Checking

This method generates multiple responses and uses consensus as an accuracy signal.

**Mechanism:** The same prompt executes multiple times (varying temperature or sampling). Responses diverging significantly from consensus are flagged as potentially hallucinatory.

**Use Case:** Three generations answer a headquarters location question. Two say "New York," one says "San Francisco." Outlier flagged; consensus "New York" selected.

### 6. External Knowledge Verification

This method cross-references generated claims against trusted external knowledge bases.

**Mechanism:** Key factual claims are queried against knowledge graphs, APIs, or search engines. Conflicts trigger correction.

**Use Case:** Model generates "Apple Inc. was founded in 1977." External verification reveals founded in 1976. Response corrected before presentation.

### 7. Multimodal Cross-Checking

In multimodal systems, this method ensures consistency across text, tables, and images.

**Mechanism:** Key facts extracted from each modality are compared. Text-table or text-image conflicts trigger flags.

**Use Case:** Retrieved table shows "Q4 Revenue: $2.1M." Generated summary states "$3.2M." Discrepancy detected; summary regenerated.