# Module 1: Generative AI & Prompting — Quiz

## Instructions
- 20 multiple choice questions
- Each question has one correct answer
- Answers with explanations are provided at the end

---

## Questions

### Q1. What is the primary difference between generative AI and discriminative AI?

A) Generative AI uses neural networks, discriminative AI does not  
B) Generative AI creates new content, discriminative AI classifies existing content  
C) Generative AI is faster than discriminative AI  
D) Discriminative AI requires more training data  

---

### Q2. Which paper introduced the transformer architecture?

A) "BERT: Pre-training of Deep Bidirectional Transformers"  
B) "Generative Pre-trained Transformer"  
C) "Attention Is All You Need"  
D) "Language Models are Few-Shot Learners"  

---

### Q3. What is the purpose of the attention mechanism in transformers?

A) To compress the input data  
B) To compute relationships between all token pairs in a sequence  
C) To convert text to numbers  
D) To reduce the model size  

---

### Q4. What does tokenization do in an LLM?

A) Compresses the model weights  
B) Converts text into numerical tokens the model can process  
C) Encrypts the input for security  
D) Translates text to another language  

---

### Q5. Zero-shot prompting means:

A) The model has zero parameters  
B) The model performs a task without any examples in the prompt  
C) The prompt has zero tokens  
D) The model requires zero training  

---

### Q6. Which prompt technique is most effective for mathematical reasoning tasks?

A) Zero-shot prompting  
B) Role-based prompting  
C) Chain-of-thought prompting  
D) Structured output prompting  

---

### Q7. What does the ReAct pattern combine?

A) Reading and Acting  
B) Reasoning and Acting  
C) Reacting and Adapting  
D) Retrieval and Analysis  

---

### Q8. What is a hallucination in the context of LLMs?

A) The model refusing to answer  
B) The model generating plausible but incorrect information  
C) The model taking too long to respond  
D) The model repeating the same output  

---

### Q9. What does the temperature parameter control in LLM generation?

A) The speed of generation  
B) The randomness/creativity of outputs  
C) The maximum output length  
D) The number of tokens in the input  

---

### Q10. What is the context window of an LLM?

A) The visual display area for outputs  
B) The maximum number of tokens the model can process in one request  
C) The time window for API responses  
D) The training data time period  

---

### Q11. Which of the following is NOT a type of bias in LLMs?

A) Representation bias  
B) Historical bias  
C) Compilation bias  
D) Measurement bias  

---

### Q12. What is in-context learning?

A) Training the model on new data  
B) The model adapting behavior based on examples in the prompt without weight updates  
C) Learning from user feedback over time  
D) Fine-tuning the model for a specific task  

---

### Q13. Which architecture is used by GPT models?

A) Encoder-only  
B) Decoder-only  
C) Encoder-Decoder  
D) Recurrent Neural Network  

---

### Q14. What is the scaling law for LLMs?

A) Performance decreases as model size increases  
B) Performance improves predictably with model size, data, and compute  
C) Larger models always produce more hallucinations  
D) Model size has no impact on performance  

---

### Q15. What is RLHF?

A) Reinforcement Learning from Human Feedback  
B) Random Language Heuristic Function  
C) Recursive Logic for Human Features  
D) Regulated Language Handling Framework  

---

### Q16. Which of the following is a defense against prompt injection?

A) Using higher temperature  
B) Clearly separating instructions from data using delimiters  
C) Increasing the context window  
D) Using fewer examples in few-shot prompts  

---

### Q17. What is the complexity of standard self-attention with sequence length n?

A) O(n)  
B) O(n log n)  
C) O(n²)  
D) O(n³)  

---

### Q18. What is the Tree of Thoughts (ToT) pattern?

A) A visual representation of model architecture  
B) Exploring multiple reasoning paths and selecting the best one  
C) A method for organizing training data  
D) A way to visualize token embeddings  

---

### Q19. When should you use RAG over fine-tuning?

A) When you need consistent output formatting  
B) When knowledge changes frequently and source attribution is needed  
C) When you need the lowest possible latency  
D) When you have millions of labeled examples  

---

### Q20. Which principle is NOT part of a responsible AI framework?

A) Transparency  
B) Fairness  
C) Maximizing model size at all costs  
D) Accountability  

---

## Answers and Explanations

### Q1. Answer: B
**Explanation:** Generative AI learns the underlying data distribution to create new content (text, images, code), while discriminative AI learns boundaries between classes for classification or prediction tasks.

### Q2. Answer: C
**Explanation:** "Attention Is All You Need" (Vaswani et al., 2017) introduced the transformer architecture, which replaced recurrent and convolutional layers with self-attention mechanisms, enabling parallel processing and better long-range dependency capture.

### Q3. Answer: B
**Explanation:** The attention mechanism computes weighted relationships between all token pairs in a sequence, allowing the model to focus on relevant parts of the input when processing each token. The formula is Attention(Q,K,V) = softmax(QK^T/√d_k) × V.

### Q4. Answer: B
**Explanation:** Tokenization converts raw text into numerical tokens (typically subword units using BPE, WordPiece, or SentencePiece) that the neural network can process. This allows the model to handle unknown words by breaking them into known subword pieces.

### Q5. Answer: B
**Explanation:** Zero-shot prompting asks the model to perform a task without providing any examples in the prompt. The model relies entirely on its pre-trained knowledge and the instructions given.

### Q6. Answer: C
**Explanation:** Chain-of-thought prompting encourages the model to break down reasoning into intermediate steps before producing a final answer, which significantly improves performance on mathematical, logical, and multi-step reasoning tasks.

### Q7. Answer: B
**Explanation:** ReAct (Reasoning + Acting) combines reasoning with tool use in an iterative loop. The model alternates between Thought (reasoning), Action (using a tool), and Observation (processing the tool's output).

### Q8. Answer: B
**Explanation:** Hallucination occurs when an LLM generates information that sounds plausible but is factually incorrect or not grounded in the provided context. This is one of the most significant challenges in production LLM applications.

### Q9. Answer: B
**Explanation:** Temperature controls the randomness of token sampling. Low temperature (near 0) produces deterministic, focused outputs. High temperature (near 1) produces more diverse, creative outputs but with potential coherence issues.

### Q10. Answer: B
**Explanation:** The context window is the maximum number of tokens (input + output combined) the model can process in a single request. Modern models range from 4K to 200K+ tokens.

### Q11. Answer: C
**Explanation:** Compilation bias is not a recognized type of bias in LLMs. The recognized types include representation bias, historical bias, measurement bias, aggregation bias, and evaluation bias.

### Q12. Answer: B
**Explanation:** In-context learning is the ability of LLMs to adapt their behavior based on examples provided in the prompt, without updating model weights. This includes zero-shot, few-shot, and many-shot learning.

### Q13. Answer: B
**Explanation:** GPT models use a decoder-only architecture with causal (unidirectional) attention, which generates text autoregressively—one token at a time, conditioning on previously generated tokens.

### Q14. Answer: B
**Explanation:** Scaling laws describe how LLM performance improves predictably with model size (parameters), training data size (tokens), and compute budget (FLOPs). Performance follows a power law with scale.

### Q15. Answer: A
**Explanation:** RLHF (Reinforcement Learning from Human Feedback) aligns LLMs with human preferences through supervised fine-tuning, reward model training, and RL optimization using PPO.

### Q16. Answer: B
**Explanation:** Using delimiters to clearly separate instructions from data is a key defense against prompt injection. Other defenses include input sanitization, output filtering, and sandboxing tool access.

### Q17. Answer: C
**Explanation:** Standard self-attention has O(n²) complexity because it computes pairwise relationships between all n tokens in the sequence, creating an n×n attention matrix. This is a key bottleneck for long sequences.

### Q18. Answer: B
**Explanation:** Tree of Thoughts extends chain-of-thought by exploring multiple reasoning paths simultaneously, evaluating them, and using search strategies (BFS, DFS, beam search) to find the optimal reasoning path.

### Q19. Answer: B
**Explanation:** RAG (Retrieval-Augmented Generation) is ideal when knowledge changes frequently and source attribution is needed. Fine-tuning is better for consistent style/format adaptation and domain-specific language patterns.

### Q20. Answer: C
**Explanation:** "Maximizing model size at all costs" is not a responsible AI principle. Core principles include transparency, fairness, accountability, privacy, and safety. Model size should be balanced with efficiency, cost, and environmental impact.

---

## Score Interpretation

| Score | Level | Recommendation |
|-------|-------|----------------|
| 18-20 | Excellent | Ready for Module 2 |
| 14-17 | Good | Review weak areas before proceeding |
| 10-13 | Fair | Re-read concepts.md and retry |
| Below 10 | Needs Work | Study the module thoroughly before advancing |

---

## Bonus: Senior / JD-Aligned Questions (Hallucination & Synthetic Data)

> Self-contained — answer follows each question. See the [interview-questions.md](interview-questions.md) *Senior Deep Dive* for full explanations.

### BQ1. In a RAG system, which metric most directly measures whether each claim in the answer traces to the retrieved context?

A) Perplexity  
B) Groundedness / faithfulness  
C) BLEU score  
D) Token throughput  

**Answer: B** — RAG engineering targets faithfulness/groundedness (claims supported by retrieved spans), measurable without world knowledge.

### BQ2. An LLM returns a fact that happens to be true but is not supported by the provided context. This is best described as:

A) A factual hallucination  
B) A faithfulness hallucination  
C) Correct behavior, no issue  
D) A tokenization error  

**Answer: B** — it's unfaithful to the context even though coincidentally true; this points you at the generator/prompt, not the retriever.

### BQ3. Which is NOT a valid hallucination-mitigation technique?

A) Grounding with RAG and requiring citations  
B) Lowering temperature and validating against a schema  
C) Raising temperature to maximize creativity for factual answers  
D) A verification pass / groundedness check before returning the answer  

**Answer: C** — higher temperature increases variability and hallucination risk for factual tasks; mitigation favors lower temperature plus grounding and verification.

### BQ4. What is "model collapse" in the context of training on synthetic data?

A) The GPU running out of memory  
B) Progressive loss of diversity and amplification of errors when models are repeatedly trained on model-generated data  
C) A model file becoming corrupted on disk  
D) The API returning a 500 error  

**Answer: B** — mitigate by mixing with real data, capping the synthetic ratio, and filtering generated samples.

### BQ5. A primary legitimate reason to use synthetic data in a regulated risk domain is:

A) It is always more accurate than real data  
B) Privacy — generate realistic non-identifiable records (and rare edge cases like fraud) to train without exposing PII/PHI  
C) It eliminates the need for any evaluation  
D) It guarantees zero bias  

**Answer: B** — privacy preservation and edge-case coverage are key drivers; synthetic data still requires filtering, balancing with real data, and downstream validation (and isn't automatically private).
