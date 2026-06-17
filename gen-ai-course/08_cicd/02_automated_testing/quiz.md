# Quiz

## Question 1

Why can't you use `assert output == expected_string` to test an LLM's generated text?

A) Python doesn't support string equality
B) LLM outputs are probabilistic, so wording varies between runs even for the same input
C) Strings are too long to compare
D) The output is always JSON

---

**Answer: B**

LLM generation is non-deterministic — the same prompt can yield different wording each run. Tests must assert on *properties* (keywords, structure, semantic similarity, or a judge's score), not on one exact string.

---

## Question 2

In the LLM testing pyramid, which layer is fastest and should run on every commit?

A) Manual red-teaming
B) Prompt regression eval
C) Unit tests
D) LLM-as-judge

---

**Answer: C**

Unit tests (parsers, prompt builders, validators) run in milliseconds and are deterministic, so they belong at the wide base of the pyramid and run on every commit. Eval and red-teaming are slower and run later as gates.

---

## Question 3

How should an integration test exercise a pipeline that normally calls an LLM, while staying offline and deterministic?

A) Call the real API with a test key
B) Inject a stub/mock LLM that returns a fixed response
C) Skip the LLM step entirely
D) Sleep until the API responds

---

**Answer: B**

Inject a stub LLM via dependency injection so the flow runs deterministically with no network. This tests the wiring (parsing, branching, error handling) without paying for or depending on a live model.

---

## Question 4

What is a "golden set" in LLM testing?

A) A set of the most expensive GPUs
B) A curated list of input → expected-content cases that defines acceptable output
C) The model's training data
D) A list of banned words

---

**Answer: B**

A golden (reference) set is curated `(input, expectation)` pairs that act as a contract for "good" output. The regression suite runs the prompt against it and scores the results.

---

## Question 5

A real bug escaped to production where the summarizer dropped a key figure. What should you do with your golden set?

A) Nothing — golden sets are fixed
B) Add the escaped case as a new golden case so the bug can never silently return
C) Delete the golden set and start over
D) Lower the threshold so it passes

---

**Answer: B**

Every escaped bug should become a new golden case. This is how the suite grows to cover real-world failure modes and turns each incident into a permanent regression guard.

---

## Question 6

Which scoring method best catches a *paraphrase* that means the same thing but uses different words?

A) Exact string equality
B) Keyword substring match
C) Semantic similarity (embedding cosine)
D) Checking the output length

---

**Answer: C**

Semantic similarity compares embeddings, so "revenue rose 15%" and "sales grew fifteen percent" score as close even though they share few exact tokens. Exact/keyword matching would miss the equivalence.

---

## Question 7

When using LLM-as-judge, which practice most improves reliability?

A) Use a high temperature for creativity
B) Pin temperature=0, supply an explicit rubric, and ask for a numeric score plus reason
C) Let the judge answer in free-form prose only
D) Use the same prompt being tested as the judge

---

**Answer: B**

A deterministic (temperature 0), rubric-driven judge that emits a structured score + rationale is far more consistent and auditable than an unconstrained one. The judge is still non-deterministic and biasable, so structure and pinning matter.

---

## Question 8

What is the main job of a regression *gate*?

A) To format the source code
B) To turn per-case scores into a single pass/fail build decision based on a pass-rate threshold
C) To deploy the model
D) To delete failing test cases

---

**Answer: B**

The gate aggregates per-case scores into an overall pass-rate and fails the build if it falls below a threshold. It is the automated quality control point that blocks regressions from advancing.

---

## Question 9

For a regression gate to actually block a CI deployment, what must it do on failure?

A) Print a warning and continue
B) Exit with a non-zero status code so the pipeline stops
C) Open a browser tab
D) Lower its own threshold

---

**Answer: B**

CI treats a non-zero exit as a failed step and halts the pipeline. A gate that only logs a warning (zero exit) would let a regression sail through to deployment.

---

## Question 10

In a CI pipeline, where should the AI evaluation gate run?

A) Only after production deployment
B) Before any unit tests
C) After unit/integration tests and before the container build/deploy
D) During the Docker image build

---

**Answer: C**

The eval gate runs after cheap deterministic tests pass and before packaging/deploying, so a quality regression is caught before it can reach users — but the pipeline isn't wasting eval time on code that fails basic tests.

---

## Question 11

What does the GitHub Actions `needs:` keyword accomplish in a test → eval-gate → deploy pipeline?

A) Sets environment variables
B) Makes a job run only after the jobs it depends on succeed, enforcing stage order
C) Chooses the runner OS
D) Triggers the workflow on a schedule

---

**Answer: B**

`needs:` defines job dependencies. An `eval-gate` job with `needs: test` runs only if `test` succeeded, so the gate (and any downstream deploy) is correctly sequenced after the basic tests.

---

## Question 12

Which of these is a security failure mode unique to LLM apps that testing should cover?

A) SQL injection
B) Cross-site scripting
C) Prompt injection / data leakage
D) Buffer overflow

---

**Answer: C**

Prompt injection (and the data leakage it can cause) is specific to LLM systems, where untrusted text in the prompt can hijack instructions. Red-team / guardrail tests target it; SQLi/XSS/buffer overflows are classic non-LLM issues.
