# Quiz

## Question 1

Why does a multi-step GenAI workflow with real dependencies and a schedule usually outgrow a single linear script?

A) Scripts cannot use Python imports
B) An orchestrated pipeline gives ordering, per-task retries, parallelism, and run visibility that a linear script lacks
C) Scripts always run faster in production
D) Orchestrators remove the need to write any code

---

**Answer: B**

A linear script reruns everything from the top on failure and has no built-in scheduling, retries, or observability. An orchestrated pipeline models the work as a DAG of named tasks, so it can resume from the failed task, run independent tasks in parallel, and expose run history and alerts.

---

## Question 2

In the DAG model used by orchestrators, what do nodes and edges represent?

A) Nodes are files; edges are network connections
B) Nodes are tasks; edges are dependencies between tasks
C) Nodes are GPUs; edges are data centers
D) Nodes are users; edges are permissions

---

**Answer: B**

A DAG (Directed Acyclic Graph) models a pipeline as nodes (tasks) connected by directed edges (dependencies). An edge from A to B means "B runs after A succeeds."

---

## Question 3

What does a *topological order* of a DAG guarantee?

A) Tasks run in alphabetical order
B) Every task appears after all of the tasks it depends on
C) All tasks run at the exact same time
D) Tasks run in the order they were written in the file

---

**Answer: B**

A topological sort produces a linear order in which each node comes after all its dependencies. Tasks with no dependency relationship between them can appear in either order, which is what allows them to be run in parallel.

---

## Question 4

Kahn's algorithm repeatedly removes nodes whose in-degree is zero. How does it detect a cycle?

A) It throws immediately on the first edge
B) If the produced order contains fewer nodes than the graph, some nodes never reached in-degree zero, indicating a cycle
C) It counts the number of edges
D) It checks whether any node name is repeated

---

**Answer: B**

In a cyclic graph, the nodes participating in the cycle never reach in-degree zero, so they are never emitted. If the final ordered list is shorter than the set of nodes, a cycle exists and the algorithm raises an error.

---

## Question 5

A GenAI fine-tune pipeline runs `prepare → fine_tune → evaluate → register → deploy`. What is the purpose of the `evaluate` step before `register`?

A) To compress the model weights
B) To act as a quality gate that stops the pipeline if the new model fails to beat the baseline or a safety suite
C) To delete the previous model
D) To convert the model to a different file format

---

**Answer: B**

`evaluate` is a quality gate. If the new model does not beat the production baseline on a held-out eval set (and pass safety checks), the pipeline should stop before `register`/`deploy`, so a worse model is never shipped and the existing model keeps serving.

---

## Question 6

Which statement best describes the difference between Airflow, Prefect, and Dagster?

A) They are completely unrelated and share no concepts
B) All three use the DAG model but differ in philosophy — task-centric (Airflow), Pythonic/dynamic flows (Prefect), and software-defined data assets (Dagster)
C) Only Airflow can run on a schedule
D) Dagster does not support dependencies between steps

---

**Answer: B**

All three orchestrate DAGs. Airflow is task-centric with statically defined DAGs, Prefect treats flows as decorated Python with dynamic DAGs, and Dagster centers on declarative software-defined assets with first-class lineage. The shared model transfers across tools.

---

## Question 7

A task is configured with `retries=2`. How many total times can it execute before being marked failed?

A) 2
B) 1
C) 3
D) Unlimited

---

**Answer: C**

Total attempts equal `retries + 1`: the initial attempt plus two retries gives three executions. If all three fail, the task is marked FAILED.

---

## Question 8

Why must a retried or backfilled task be *idempotent*?

A) Because retries are illegal otherwise
B) Because a task may run more than once, so repeating it must be safe and must not create duplicates or double-count
C) Because idempotency makes tasks run faster
D) Because orchestrators cannot retry non-idempotent tasks at all

---

**Answer: B**

Retries and backfills can cause a task to run multiple times. An idempotent task (e.g. UPSERT by an idempotency key, or write to a content-addressed path) produces the same result whether it runs once or five times, avoiding duplicate vectors or inflated counters.

---

## Question 9

A drift monitor reports the input distribution has shifted well past your threshold. Which retraining trigger does this represent?

A) Schedule-based trigger
B) Data-volume-based trigger
C) Drift-based trigger
D) Manual trigger

---

**Answer: C**

A drift-based trigger fires when input or output distributions shift past a threshold (measured via PSI, KL divergence, embedding-distribution shift, or eval-score decay). It retrains exactly when quality is at risk rather than on a fixed clock.

---

## Question 10

When a stage in a pipeline fails permanently (after exhausting its retries), what is the correct behavior for stages that depend on it?

A) Run them anyway with empty input
B) Skip them, because their dependency did not succeed
C) Retry the failed stage forever
D) Run them in parallel with the failed stage

---

**Answer: B**

A downstream stage's precondition (its dependency succeeding) is not met, so it must be SKIPPED, not run with missing/invalid input. The orchestrator records the failure and skips the affected branch while letting unrelated branches continue.
