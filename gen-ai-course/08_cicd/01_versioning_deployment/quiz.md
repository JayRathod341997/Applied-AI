# Quiz

## Question 1

Why is plain Git insufficient for versioning a fine-tuned model's weights?

A) Git cannot track binary files at all
B) Large binary files bloat the repo, produce meaningless diffs, and make clones slow
C) Git deletes files larger than 1 MB
D) Git only works for Python code

---

**Answer: B**

Git was built for line-based text. A multi-GB `.safetensors` file bloats history, has no useful diff, and slows every clone. The fix is to keep a small pointer in Git and store the bytes in a system built for them (Git LFS or a DVC remote).

---

## Question 2

What does `dvc add models/llm.safetensors` actually place under Git's control?

A) The full model file, compressed
B) A small `.dvc` metadata file containing a content hash, plus a `.gitignore` entry
C) Nothing — DVC bypasses Git entirely
D) A symlink to your home directory

---

**Answer: B**

DVC replaces the large file with a tiny `.dvc` pointer (a content hash and metadata) that Git tracks, and ignores the real file. The bytes go to the DVC remote via `dvc push`; the pointer goes to Git via `git push`.

---

## Question 3

You have a 14 GB dataset and a need to reproduce training pipelines. Which tool fits best?

A) Git LFS
B) DVC
C) Plain Git with `.gitignore`
D) Email the dataset to teammates

---

**Answer: B**

DVC is designed for large datasets/models *and* pipeline reproducibility (`dvc repro`, `dvc.yaml`). Git LFS handles in-repo binaries but offers no pipeline/lineage features; plain Git can't carry the bytes at all.

---

## Question 4

What capability does a model registry provide that DVC does not?

A) Storing large files
B) Lifecycle stage management (None → Staging → Production → Archived) and run lineage
C) Hashing file contents
D) Running unit tests

---

**Answer: B**

DVC answers "what bytes did this commit reference?" A registry (MLflow/Azure ML) adds lifecycle *stages*, governance, and lineage back to the run (params, metrics, data) that produced each version.

---

## Question 5

A teammate edits an already-registered model version's artifact in place to "fix" it. Why is this a problem?

A) It's fine — registries are meant to be edited
B) It breaks immutability, so rolling back to that version no longer reproduces the original behaviour
C) It doubles storage cost
D) It deletes the staging environment

---

**Answer: B**

Registered versions must be immutable. If you mutate a version, the thing you roll back to is no longer what it was — destroying the trust that makes rollback safe. The correct move is to register a *new* version.

---

## Question 6

Why are prompts described as "soft" assets that need their own versioning discipline?

A) They are written in a soft font
B) A small wording change can dramatically swing output quality, so changes must be tracked, tested, and reversible
C) They never affect model behaviour
D) They are compiled into the model weights

---

**Answer: B**

Prompts are prose, but a one-line change can move quality a lot. Versioning them (with eval thresholds attached) makes prompt changes auditable, testable, and rollback-able just like code.

---

## Question 7

For a team just starting to manage prompts, which strategy is the recommended default?

A) Hardcode prompts as string constants in the app
B) Git-based YAML prompt files
C) A custom distributed prompt database with sharding
D) Store prompts inside the training data

---

**Answer: B**

Git-based YAML files are simple, diff-able, and auditable with zero new infrastructure. Teams graduate to a registry or feature flags only when they need runtime promotion or live A/B testing.

---

## Question 8

In feature-flag A/B prompt routing, why bucket users with `hash(user_id) % 100`?

A) To make routing random on every request
B) To assign each user *deterministically* and consistently to the same variant
C) To encrypt the user ID
D) To rate-limit users

---

**Answer: B**

Hashing the stable user ID gives a deterministic bucket, so the same user always sees the same variant. Pure randomness per request would flip a user between control and treatment, contaminating the experiment.

---

## Question 9

What is the difference between promotion and rollback?

A) They are the same thing
B) Promotion moves a chosen version *up* the environment ladder (gated); rollback re-points the active pointer *back* to a known-good version
C) Promotion deletes old versions; rollback creates new ones
D) Promotion is manual; rollback is impossible to automate

---

**Answer: B**

Promotion advances one version through Dev → Staging → Production behind quality gates. Rollback is the inverse: it switches the active pointer back to a prior stable version. The artifacts themselves never change — only which version each environment points at.

---

## Question 10

Which two ingredients does reliable, fast rollback most depend on?

A) A large GPU and a fast network
B) Immutable versions plus a deployment-history audit trail
C) Manual approval from three managers
D) Deleting the failing version

---

**Answer: B**

Immutability guarantees the rollback target is byte-identical to what it was; the deployment-history trail (`version, env, timestamp, action`) tells you *which* version was the previous stable one to roll back to.

---

## Question 11

Which rollback trigger is specific to GenAI rather than generic web apps?

A) Error-rate spike above 5%
B) P99 latency above 3000 ms
C) Output quality dropping below threshold on a golden set
D) CPU usage above 90%

---

**Answer: C**

Error rate, latency, and CPU are generic. A *quality* drop measured by a live regression/golden-set eval is AI-specific — a model or prompt change can pass code tests yet degrade output quality, which only an evaluation gate catches.
