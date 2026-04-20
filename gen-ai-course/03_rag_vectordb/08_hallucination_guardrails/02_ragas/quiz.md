# Quiz: Hallucination Guardrails with RAGAS and TruLens

## Section 1: Theory

**1. What is the primary difference between RAGAS and TruLens?**
   - A) RAGAS is for production, TruLens is for testing
   - B) RAGAS is reference-free, TruLens requires ground truth
   - C) RAGAS is for offline evaluation, TruLens is for real-time guardrails
   - D) They are essentially the same tool

**2. Which RAGAS metric measures if the answer adds unverified information?**
   - A) Answer Relevancy
   - B) Context Recall
   - C) Faithfulness
   - D) Context Precision

**3. In TruLens, what does the groundedness score indicate?**
   - A) How relevant the answer is to the question
   - B) How many chunks were retrieved
   - C) How well the answer is supported by the context
   - D) How much the answer differs from baseline

**4. What is a "factual hallucination" in RAG?**
   - A) The model refusing to answer
   - B) The model generating false information
   - C) The model using only old information
   - D) The model answering from memory instead of context

**5. Which layer of defense prevents the model from receiving irrelevant context?**
   - A) Generation Layer
   - B) Retrieval Layer
   - C) Prompt Layer
   - D) Validation Layer

## Section 2: RAGAS Implementation

**6. What is required to compute context recall?**
   - A) Only the question and answer
   - B) Ground truth context
   - C) Multiple temperature settings
   - D) No special requirements

**7. In RAGAS, what dataset format is required?**
   - A) Only JSON
   - B) HuggingFace Dataset format
   - C) CSV
   - D) Excel

**8. Which metric does NOT require ground truth?**
   - A) Context Recall
   - B) Context Entity Recall
   - C) Faithfulness
   - D) All require ground truth

**9. How do you run multiple RAGAS metrics together?**
   - A) Call each metric separately
   - B) Use the evaluate() function with a list
   - C) Use the evaluate() function with a single metric
   - D) This is not supported

**10. What is the recommended threshold for faithfulness in production?**
   - A) 0.5
   - B) 0.7
   - C) 0.95
   - D) 1.0

## Section 3: TruLens Implementation

**11. What is a feedback function in TruLens?**
   - A) A user feedback collection form
   - B) A function that evaluates outputs
   - C) A logging mechanism
   - D) A database query function

**12. In TruLens, what does on_failure="fallback" do?**
   - A) Fails the entire request
   - B. Uses a predefined fallback response
   - C) Retries the query
   - D) Logs an error

**13. What is the purpose of the ThresholdGuardrail?**
   - A) To limit response length
   - B) To block responses below a quality threshold
   - C) To filter input queries
   - D) To cache responses

**14. Which integration is supported by TruLens?**
   - A) Only LangChain
   - B) LangChain and LangGraph
   - C. LangChain, LangGraph, and LlamaIndex
   - D) Only LlamaIndex

**15. How does TruLens evaluate in real-time?**
   - A) At query time (synchronously)
   - B) In batch mode after response
   - C) Only in development
   - D) Not at all

## Section 4: Best Practices

**16. What is "defense in depth" in hallucination protection?**
   - A) Using multiple guardrails at different layers
   - B) Having redundant systems
   - C) Testing thoroughly
   - D) Using multiple evaluation metrics

**17. Which is NOT a recommended fallback strategy?**
   - A) Return "I don't know"
   - B) Use a different model
   - C) Try with higher temperature
   - D) Answer anyway

**18. What should you do if faithfulness is low but context precision is high?**
   - A) Improve retrieval
   - B) Fix generation/prompt
   - C) Add more documents
   - D) Nothing

**19. Why should you avoid thresholds > 0.9?**
   - A) They are impossible to achieve
   - B) They cause too many fallbacks
   - C) They are not measurable
   - D) They don't improve quality

**20. For CI/CD, which framework is more appropriate?**
   - A) TruLens
   - B) RAGAS
   - C) Both equally
   - D) Neither

## Answers

1. C - RAGAS for offline, TruLens for real-time
2. C - Faithfulness measures unverified info
3. C - Groundedness = supported by context
4. B - False info presented as fact
5. B - Retrieval Layer
6. B - Context recall needs ground truth
7. B - HuggingFace Dataset
8. C - Faithfulness is reference-free
9. B - Use evaluate() with list
10. B - 0.7 is standard
11. B - Function evaluating outputs
12. B - Uses fallback response
13. B - Blocks low-quality responses
14. C - Multiple integrations
15. A - At query time
16. A - Multiple protection layers
17. D - Answering anyway causes hallucinations
18. B - Generation issue, not retrieval
19. B - Too strict causes fallbacks
20. B - RAGAS for CI/CD