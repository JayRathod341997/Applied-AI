# Quiz: Prompt Filtering & Input Defense

## Questions

### Question 1
Which OWASP LLM Top 10 entry covers prompt injection?

A) LLM02: Insecure Output Handling
B) LLM01: Prompt Injection
C) LLM06: Sensitive Information Disclosure
D) LLM10: Model Theft

### Question 2
What makes **indirect (RAG-borne)** prompt injection especially dangerous?

A) It requires the user to be malicious
B) The attack payload arrives via retrieved content, so filtering the user's message never sees it
C) It only affects fine-tuned models
D) It is blocked automatically by delimiters

### Question 3
Why is prompt injection considered fundamentally hard to eliminate?

A) LLMs are too slow to check inputs
B) There is no strict separation between instructions and data inside the model's token stream
C) Regex engines are not powerful enough
D) It only happens with open-source models

### Question 4
An attacker sends a base64 blob that decodes to "ignore all previous instructions." What must your
filter do to catch it?

A) Increase the temperature
B) Decode candidate encodings and re-run the detectors on the plaintext
C) Block all messages containing uppercase letters
D) Nothing — the model will refuse it anyway

### Question 5
Why prefer an **allowlist** over a **denylist** when the input shape is known (e.g., a ZIP code)?

A) Allowlists are faster to type
B) A denylist blocks known-bad and is trivially evaded; an allowlist only accepts known-good shapes
C) Denylists cannot use regex
D) Allowlists never produce false positives

### Question 6
What is the purpose of a **canary token** in the system prompt?

A) To speed up inference
B) It is a tripwire: if it appears in the model's output, a system-prompt leak occurred
C) To authenticate the user
D) To compress the prompt

### Question 7
Why return a tiered **ALLOW / FLAG / BLOCK** decision instead of a single boolean?

A) It looks more professional
B) To manage the false-positive vs false-negative trade-off per risk tier (proceed-but-log vs refuse)
C) Booleans are deprecated in Python
D) It reduces token usage

### Question 8
Which statement about **input filtering** is correct?

A) It is sufficient on its own to stop all prompt injection
B) It is one layer of defense-in-depth; output validation and least-privilege tools are still required
C) It should replace output validation
D) It makes canary tokens unnecessary

### Question 9
"Spotlighting" / data-marking primarily helps by…

A) Encrypting the user's message end-to-end
B) Making untrusted data visibly distinguishable so the model treats it as data, not instructions
C) Removing all punctuation from inputs
D) Caching frequent prompts

### Question 10
Using an **LLM-as-judge** to screen inputs has which key weakness?

A) It cannot read English
B) The judge is itself an LLM and can be prompt-injected
C) It only works offline
D) It always has zero latency

## Answers

1. B - Prompt injection is OWASP **LLM01**.
2. B - In indirect injection the user is innocent; the payload hides in retrieved content, so filtering the user field misses it entirely.
3. B - An LLM processes one token stream with no hard instruction/data boundary — the root cause; filtering is mitigation, not a cure.
4. B - Normalize and **decode-then-rescan**; otherwise every detector is blind to the encoded payload.
5. B - Allowlists accept only known-good shapes, defeating arbitrary injection; denylists are an endless cat-and-mouse.
6. B - A canary is a leak tripwire checked on the **output**; its presence signals a system-prompt leak/injection.
7. B - Tiered decisions let you bias toward blocking on high-risk actions and toward allowing+logging on low-risk chat.
8. B - Input filtering is one layer; indirect injection, novel paraphrases, and downstream damage require output validation and least-privilege tools too.
9. B - Data-marking/spotlighting makes injected imperatives stand out so the model treats marked text as data.
10. B - The judge model can itself be injected, so it needs a hardened prompt and must never blend judged text into its instruction channel.
