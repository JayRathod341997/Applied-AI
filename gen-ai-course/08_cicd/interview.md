# CI/CD for AI — Senior Interview Deep Dive

Per-subtopic interview questions live in each subtopic's `interview.md` (versioning, automated testing, deployment strategies, AWS CI/CD). This file holds the cross-cutting **senior-level** deep dive that spans the whole CI/CD lifecycle for GenAI.

---

## Senior Deep Dive: CI/CD for GenAI

> Senior interviews probe shipping probabilistic systems safely — eval gates, gradual rollout, and metric-driven rollback. Expect questions that cut across versioning, testing, deployment, and cloud in one answer.

---

### System Design & Scale

#### Q: Design a CI/CD pipeline that gates on AI quality across 20 services.

**Answer:** The core problem is that quality evaluation is expensive and non-trivial — you cannot gate each service independently with a hand-rolled golden set per service and still keep pipeline time reasonable. The solution is a shared, multi-service eval infrastructure.

**Architecture:**

```
Source (Git push)
    │
    ▼
Build & Unit Tests  (per-service, CodeBuild / GitHub Actions runner)
    │
    ▼
Shared Eval Gate  ──► golden-set per service, sampled from a central registry
    │  pass-rate ≥ per-service threshold?
    │  yes → package; no → fail, block deploy
    ▼
Prompt / Model Registry approval  (Azure ML / SageMaker Model Registry)
    │  bundle id: code_sha + model_version + prompt_version + embedding_hash
    ▼
Canary Deploy  (Azure Container Apps revision traffic-split / CodeDeploy Canary10Percent5Minutes)
    │
    ▼
Live quality alarm  (custom metric: GoldenSetPassRate < threshold → auto-rollback)
```

Key design decisions:

1. **Shared golden-set registry.** Each service owns its golden set (stored in a central S3 bucket / Azure Blob with service-namespaced paths) but the eval runner is a shared library invoked by each service's CI job. This keeps infra costs flat and eval methodology consistent across teams.

2. **Per-service quality threshold.** Not all services have the same risk profile — a customer-facing chat service has a tighter threshold (≥ 90%) than an internal summarizer (≥ 80%). Store thresholds in each service's config file, not hardcoded in the shared runner.

3. **Bundle ID as the deployable unit.** Register a single `bundle_id = {code_sha}:{model_version}:{prompt_version}:{embedding_hash}` in the prompt/model registry before deploy. The canary and rollback operate on bundle IDs, not individual artifact versions. This prevents "code was updated but prompt wasn't" drift.

4. **Canary via Azure Container Apps revisions / CodeDeploy.** Each service deploys with a canary split. Auto-rollback triggers on the `GoldenSetPassRate` custom metric, not just HTTP 5xx, because the dangerous LLM regressions return 200 OK with worse answers.

| Pipeline stage | Tool (Azure-primary) | Tool (AWS) |
|---|---|---|
| Build + unit | GitHub Actions / Azure DevOps | CodeBuild |
| Eval gate | Azure DevOps stage, exits non-zero | CodeBuild `buildspec.yml` |
| Registry gate | Azure ML model registry, Approved stage | SageMaker Model Package, Approved status |
| Canary rollout | Azure Container Apps revision traffic | CodeDeploy Canary10Percent5Minutes |
| Live alarm | Azure Monitor custom metric | CloudWatch custom metric |

---

#### Q: How do you keep the pipeline and eval gate fast as the golden set grows?

**Answer:** Speed degrades in two ways as the golden set grows: the eval gate takes too long and blocks the pipeline, and flaky LLM-as-judge calls introduce variance. The answer is a tiered gate with sampling and parallelism.

**Tiered gate design:**

```
Tier 1 — Fast gate (every commit, < 2 min)
    ├── Unit tests (deterministic, ms)
    ├── Integration tests with mocked LLM (seconds)
    └── Keyword/semantic scoring on a SMALL fixed slice of golden set
            (e.g. 20 highest-signal cases, seeded random sample)
            Pass threshold: ≥ 90% on the slice

Tier 2 — Full eval gate (candidate release or scheduled nightly)
    └── Full golden set, LLM-as-judge scoring, parallelized across workers
            Pass threshold: ≥ 85% on the full set
```

**Parallelism.** Each golden-set case is independent — fan out evaluation across workers. In Azure DevOps use matrix jobs; in GitHub Actions use a matrix strategy over shards. A 500-case golden set runs in the same wall-clock time as a 50-case set if you run 10 parallel workers.

**Sampling.** Maintain a "high-signal core" golden set of ~20–50 cases curated to cover the riskiest regressions (every bug that escaped in the past). Run the core on every commit; run the full set on candidates. Flag any commit that fails the core immediately — it is almost certainly a regression.

**Semantic scoring over LLM-as-judge for Tier 1.** Keyword + cosine similarity scoring is deterministic and free; LLM-as-judge adds latency and cost. Reserve LLM-as-judge for the full gate (Tier 2) or for borderline cases (score between 0.45–0.55).

**Version the golden set.** Adding cases is a reviewed pull request — this prevents golden-set bloat from uncurated additions and keeps the high-signal core compact.

---

#### Q: Describe a versioning strategy for code, prompts, models, and embeddings at scale.

**Answer:** The root problem is that these four artifact types change on different cadences, are produced by different teams, and have different storage needs. The answer is a single deployable bundle ID that ties all four together.

**Single bundle, multiple artifact types:**

```
bundle_id = {app_git_sha}:{model_semver}:{prompt_semver}:{embedding_hash}

Example:
  a3f9b12:2.1.0:3.0.0:sha256:ab12cd

Stored in: artifact registry (Azure Artifacts / S3 + DynamoDB manifest)
Promoted through: dev → staging → production lifecycle stages
```

**Per-artifact versioning rules:**

| Artifact | Storage | Versioning | Immutability |
|---|---|---|---|
| Code | Git | Git SHA + semver tag | Git history is immutable |
| Prompts | Git (YAML files) or prompt registry | `MAJOR.MINOR.PATCH` in filename/metadata | Never edit a registered version |
| Models | DVC pointer in Git, bytes in Azure Blob/S3 | `MAJOR.MINOR.PATCH` + eval metrics | Content-addressed (hash in .dvc file) |
| Embeddings | Azure Blob/S3 with bucket versioning | Content hash + reindex date | Bucket versioning preserves all versions |

**Registry approval gate.** A bundle ID becomes eligible for production only when all four components have passed eval and the bundle has been registered in the model/artifact registry with `Approved` status. The registry is the source of truth for "what is in production right now."

**Reproducibility guarantee.** Given a bundle ID, you can reconstruct the exact system that was running: `git checkout` the SHA, `dvc pull` the model, load the prompt YAML at that version, and fetch the embedding index at that hash. This is what makes rollback trustworthy — the target is byte-identical to what it was.

---

### Trade-offs & Decisions

#### Q: When do you choose canary vs blue-green vs linear for an LLM service?

**Answer:** The choice depends on three factors: how long you need to bake the new version before you trust it, how fast you need rollback to be, and how much infrastructure overhead you can absorb.

| Strategy | When to choose | Rollback speed | Infrastructure cost |
|---|---|---|---|
| **Blue-green** | When you need instant cutover and instant rollback; release is well-tested and you want a clean flip | Instant (one traffic switch) | 2× capacity required during switchover |
| **Canary** | For most LLM service releases; quality bake time matters; gradual exposure to real traffic catches regressions that CI missed | Fast (shift weight to 0%) | Modest — new version runs at small % only |
| **Linear** | For high-risk releases where you want fine-grained visibility into quality degradation at each traffic increment | Fast (shift weight back) | Similar to canary |

**For LLM services, canary is the default choice.** The reason is specific to probabilistic systems: a prompt or model change can pass your golden set at 90%+ but degrade on the long tail of real-world inputs you haven't seen. Canary exposes the new version to 10% of real traffic while the stable version serves 90% — you observe real-world quality on a small blast radius before committing to a full rollout.

**Blue-green makes sense when:** the new version has been shadow-tested extensively, the rollout is a purely infrastructural change (not a model/prompt change), or the service requires instant switchover for contractual reasons (e.g., a new compliance requirement that cannot be partially live).

**Linear makes sense when:** you want to watch the quality metric tick up at each +10% increment and have a dashboard audience that expects predictable ramp schedules — common in regulated industries.

**Quality bake time is the LLM-specific factor.** For canary, choose a bake window long enough to accumulate statistically meaningful signal on the quality metric. `Canary10Percent5Minutes` (10% for 5 minutes) may be too short for a low-traffic service — you might see only 50 requests, which is not enough to detect a 5% quality drop. For low-traffic services, use `Linear10PercentEvery3Minutes` or a longer bake window.

---

#### Q: Should you block the build on eval pass-rate or warn-only?

**Answer:** Block. Warn-only means developers learn to ignore the warning and the gate becomes theatre. The value of an eval gate is precisely that it is a hard stop — if it never blocks a deploy, teams stop trusting it and stop maintaining the golden set.

**The practical concern is false fails.** If the gate is too tight or the golden set covers edge cases that vary with model temperature, the gate fires spuriously and teams raise the threshold or disable it. The right response is not to switch to warn-only — it is to fix the gate:

1. **Set a threshold with margin.** If your baseline pass-rate on main is 88%, set the gate threshold at 80%, not 87%. The 8-point margin absorbs normal variance without letting a real 10-point regression through.

2. **Seed temperature for determinism.** Where possible, set `temperature=0` or a fixed seed in the eval runner so the same case produces the same output. LLM-as-judge calls are harder to fix — use semantic similarity scoring for determinism in CI and reserve LLM-as-judge for the full eval.

3. **Allow one retry.** A single retry (re-run the eval job once on failure) catches transient API issues without making false failures a norm. Three retries is too many — you are masking a real signal.

4. **Track the gate history.** If a gate fires on a commit that has no prompt/model changes, that is signal: your golden set has non-deterministic cases or your threshold is too tight. Fix the root cause, don't demote to warn-only.

Warn-only is acceptable for a net-new service in its first two weeks while the golden set is being calibrated. Once calibrated, flip to blocking.

---

#### Q: Native cloud CI/CD (CodePipeline / Azure DevOps) vs GitHub Actions — how do you decide?

**Answer:** Both can run a production GenAI pipeline. The decision turns on where your identity, secrets, and deployment targets live, not on features.

| Factor | Choose Azure DevOps / CodePipeline | Choose GitHub Actions |
|---|---|---|
| **Secrets & identity** | Azure Key Vault / AWS Secrets Manager deeply integrated; OIDC to cloud resources is native | Needs GitHub OIDC → cloud role trust, or manually sync secrets; more setup for cloud deployments |
| **Deployment targets** | Native integration with Azure Container Apps, AKS, Lambda, ECS — approval gates, environment tracking built in | Actions deployments work but approval gates are more limited; deploying to Azure/AWS needs marketplace actions |
| **Compliance & audit** | Enterprise audit logs, approval workflows, compliance gates (Azure DevOps) built in | Requires third-party actions or custom workflows for enterprise audit |
| **Code hosting** | Code lives in Azure Repos / CodeCommit | Code lives in GitHub |
| **Portability** | Pipeline definition is cloud-specific | Workflow files are portable across GitHub-hosted repos |
| **OSS / community** | Fewer community-built integrations | Massive marketplace of reusable actions |

**Practical heuristic:** if your team already uses GitHub for source control and most of your cloud access is through OIDC federation, GitHub Actions is lower friction and has the better community ecosystem. If you are in an enterprise Azure shop with Azure AD, Key Vault, and Azure Repos, Azure DevOps gives you tighter native integration with fewer moving parts.

**Hybrid is common and fine.** Use GitHub Actions for CI (build, unit tests, eval gate) and Azure DevOps Release Pipelines or CodeDeploy for the CD part that touches production. The AI eval gate runs in the CI half where the golden set and model assets live; the deploy half handles approvals, environment promotion, and rollback.

---

### Failure Modes & Incidents

#### Q: A model change passed CI but degraded quality in production. How do you detect it and roll back?

**Answer:** This is the most common GenAI-specific incident pattern: the golden set was not representative of real-world inputs, so CI passed, but production traffic exposed the regression.

**Detection — the live quality alarm:**

The eval gate runs in CI against a static golden set. In production, you must also run a continuous quality signal:

1. **Sample live traffic.** On every N-th request (e.g. every 20th), log the input + output to a quality evaluation queue.
2. **Async eval worker.** A background worker scores sampled outputs using keyword scoring or an LLM-as-judge and publishes a `GoldenSetPassRate` (or `SampledQualityScore`) custom metric to CloudWatch / Azure Monitor.
3. **Alarm threshold.** Set an alarm: if `SampledQualityScore` drops below threshold for 5 consecutive minutes, enter `ALARM` state.
4. **Alarm → CodeDeploy / Container Apps rollback.** The CodeDeploy deployment group or Azure Container Apps revision rule is pre-wired to watch this alarm. When it fires, traffic shifts back to the prior bundle ID automatically.

**Rollback target:**

Rollback does not mean "redeploy the previous Docker image." It means "switch the active bundle ID to the prior Approved bundle." The prior bundle's image is still in ECR/ACR (never delete a previously deployed image), and the model/prompt versions are still in the registry. Rollback is a traffic-weight change, not a new build.

```
Incident timeline:
  T+0    New bundle deployed as canary (10%)
  T+5    SampledQualityScore alarm fires (quality < threshold)
  T+5    CodeDeploy auto-rollback: canary weight → 0%, stable resumes 100%
  T+10   On-call receives alert: "Canary auto-rolled back — quality alarm"
  T+15   Team investigates: which golden-set cases now fail? Add them to the set.
  T+30   Root cause: new model handles numeric inputs worse. Logged as known regression.
```

**Post-incident.** Every incident of this type should produce at least one new golden-set case that would have caught the regression in CI. Over time this hardens the gate.

---

#### Q: A flaky eval gate is blocking deploys randomly. How do you fix it?

**Answer:** Flakiness in an eval gate is almost always one of three root causes: model non-determinism, an LLM-as-judge that itself varies, or external API timeouts. Each has a distinct fix.

**Diagnose first.** Run the eval gate 5 times on the same commit without any code changes. If it passes 3 and fails 2, it is flaky. Record which specific golden-set cases flip — that tells you whether the issue is non-determinism in the model call or in the judge.

**Fix 1 — Seed temperature for determinism.**

```python
# In the eval runner, always set temperature=0 and a fixed seed
response = client.chat.completions.create(
    model="gpt-4o",
    temperature=0,          # deterministic output
    seed=42,                # reproducible across runs (where supported)
    messages=[...]
)
```

This eliminates flakiness from model sampling variance. Most golden-set cases should be testable at `temperature=0`.

**Fix 2 — Semantic scoring instead of exact match for borderline cases.**

If a case has a reference answer and the LLM paraphrases it differently each run, exact-match scoring is inherently flaky. Switch to cosine similarity against a reference embedding — it is deterministic (the reference embedding is fixed) and tolerates paraphrase.

**Fix 3 — Raise the threshold with margin (not lower the bar).**

If baseline pass-rate on main is 88% ± 3%, a threshold of 87% will fire spuriously. Set the threshold at 80% — the 8-point margin absorbs normal run-to-run variance. The threshold is not "how good do we need to be" (that is the baseline); it is "how much degradation are we willing to accept before blocking."

**Fix 4 — One retry, not three.**

Add a single retry on gate failure (re-run the eval job). One retry catches transient API timeouts. More than one retry masks real regressions.

**Fix 5 — Replace LLM-as-judge in CI with semantic scoring; use judge only in the full eval.**

LLM-as-judge calls are inherently non-deterministic (and expensive). In the fast CI gate (Tier 1), replace them with cosine similarity. Reserve LLM-as-judge for the full nightly eval where you can afford retries and cost.

**Fix 6 — Fix the non-deterministic golden-set cases.**

If a case has no stable correct answer (e.g. "write a creative tagline for this product"), it should not be in the CI eval gate — it belongs in manual red-teaming. Audit the golden set for cases whose expected output is inherently subjective and remove or replace them.

---

#### Q: A secret was leaked into a container layer. What is your response and how do you prevent it next time?

**Answer:** A secret in a container layer is a permanent leak — Docker image layers are immutable and the history is preserved. Treat it as a production incident, not just a cleanup task.

**Immediate response:**

1. **Rotate the credential immediately.** Before anything else, invalidate the leaked secret (API key, service principal, database password). A rotated credential that has been leaked is harmless; an unrotated one is an open door.
2. **Assess exposure window.** Check when the image was first pushed (ECR/ACR push timestamp) and whether it was ever pulled from an external registry or a public repository. If public: assume the secret was harvested.
3. **Delete the affected image tags.** Remove the image from the registry — but do not rely on deletion to protect you, because images may have been pulled and cached elsewhere. Rotation is the real protection.
4. **Scrub the image history.** If the secret was committed to Git before being baked in, rewrite Git history (`git filter-repo`) to remove the commit. Push force with a team notification.
5. **Audit usage logs.** Check cloud access logs (CloudTrail / Azure Activity Log) for any API calls made with the leaked credential after the image was pushed.
6. **Notify security.** File an incident report per your org's policy — even if exposure appears contained.

**Prevention — three layers:**

1. **Never put secrets in Dockerfiles or source code.** Use a secrets manager at runtime: Azure Key Vault / AWS Secrets Manager, injected as environment variables by the container runtime, never baked into the image. The Dockerfile should have no `ENV SECRET_KEY=...` lines.

2. **Pre-commit and pre-push secret scanning.** Install `detect-secrets` or `trufflehog` as a Git pre-commit hook. Wire the same scanner into the CI pipeline as a build phase that fails on any detected secret pattern.

   ```yaml
   # In buildspec.yml / GitHub Actions
   - name: Secret scan
     run: trufflehog filesystem . --fail
   ```

3. **Container image scanning at build and at pull.** Enable ECR scan-on-push (Amazon Inspector) / Azure Defender for Containers. These scanners detect secrets in image layers and will flag the image before it reaches a deployment stage. Use `trivy image --scanners secret <image>` in CodeBuild / the Actions workflow.

**Structural fix.** Audit your Dockerfiles and CI configs for any hardcoded secrets or `ARG`/`ENV` variables that reference secrets. Replace all with runtime injection patterns. Run `docker history <image>` on every production image to verify no secret is visible in layer commands.

---

### Leadership & Behavioral

#### Q: How do you get teams to trust an automated quality gate they can't fully explain?

**Answer:** Trust in an automated gate is earned, not assumed. Teams distrust gates that fire mysteriously, block work without clear cause, and offer no path to appeal. The fix is transparency, shared ownership, and a visible track record.

**Make the gate legible.** Every gate failure should produce a human-readable report: which golden-set cases failed, what the expected output was, what the actual output was, and what the pass-rate was vs the threshold. If a developer cannot read the failure report and understand why the gate fired, the gate is not yet production-ready. Invest in the report before enforcing the gate.

**Co-own the golden set.** Involve the teams whose services are gated in the curation of their golden sets. A team that wrote the golden cases understands what each one tests and trusts the gate because they built it. A gate imposed externally with a golden set the team has never read will generate resentment.

**Show the track record.** Build a dashboard showing: how many times the gate fired over the past 90 days, how many of those were true positives (caught a real regression), how many were false positives (spurious fires), and what the recall is (how many regressions escaped to production despite the gate passing). A gate with a visible 80%+ true-positive rate becomes trusted quickly. A gate with no track record is just overhead.

**Allow a fast appeal path, not an override path.** If a team believes a gate fire is spurious, they should be able to open a PR to fix the golden case or raise the threshold with justification — not bypass the gate entirely. An override path (manual approval to skip the gate) should exist for genuine production emergencies only, require two approvers, and be logged as a security/quality incident.

**Introduce it incrementally.** Start warn-only for two weeks so teams see the gate's output without being blocked. Fix false positives during this period. Flip to blocking only when the false-positive rate is low. Teams that watched the gate fire accurately in warn-only mode for two weeks will accept it as blocking.

---

#### Q: Tell me about a time you introduced canary deployment with auto-rollback to a team that was deploying all-at-once. (STAR)

**Answer:**

**Situation.** The team ran a GenAI summarization service for an internal product. Every release was an all-at-once deployment: `kubectl set image` or a container swap, 100% of traffic switched in one step. Twice in three months a prompt change that passed CI degraded quality in production — users noticed before the team did, and rollback required a new image build and redeploy (15–30 minutes).

**Task.** I needed to introduce canary deployment with automated quality-driven rollback without disrupting the team's weekly release cadence or requiring new infrastructure they didn't understand.

**Action.** I started by framing the problem in terms the team already cared about: "the last two incidents took 20 minutes to recover from and both started with a prompt change that looked fine in CI." That got buy-in for the principle before I proposed a solution.

I introduced the change in three phases over six weeks:

1. **Week 1–2: Add the live quality metric.** I added a sampled-output eval worker that published a `SampledQualityScore` custom metric to Azure Monitor. No change to the deploy process — just visibility. I demoed the dashboard to the team so they could see the metric moving with each release.

2. **Week 3–4: Canary traffic split, manual promotion.** I converted the Azure Container Apps deployment to use revision traffic splitting: new revision starts at 10%, old revision at 90%. Promotion to 100% was still a manual step (the developer checked the dashboard and ran a CLI command). This gave the team confidence in the canary mechanics without automating a critical path.

3. **Week 5–6: Automated rollback wired to the quality alarm.** I added an Azure Monitor alert rule: if `SampledQualityScore` drops below 80% for 5 consecutive minutes, fire a webhook that sets the new revision's traffic weight to 0%. I demonstrated this in staging with a deliberately bad prompt — the team watched the dashboard, saw the alarm fire, and saw the traffic shift back automatically.

I documented the runbook, ran a game day (intentional bad deploy in staging), and announced the feature in the team's weekly sync.

**Result.** The team shipped the next three releases as canaries without incident. Four weeks after going live, a model version update caused a real quality regression — the alarm fired at 3 a.m., the canary auto-rolled back, and the on-call engineer found a Slack notification and a system that had already recovered. Recovery time dropped from 20 minutes to under 2 minutes. The team now treats canary + auto-rollback as the default and has back-ported the pattern to two other services.

---

> **Staff/Principal stretch:** Define the org's release-safety standard for GenAI (required gates, rollback SLAs, who can override).

**Answer:** A release-safety standard for GenAI is a written policy that makes the implicit explicit: which gates are mandatory for every service, what the rollback SLA is, and under what conditions a gate can be bypassed.

**Required gates (mandatory for any GenAI service touching production):**

| Gate | Minimum bar | Enforcement |
|---|---|---|
| Unit + integration tests | All pass | CI blocks merge |
| Prompt regression / eval gate | ≥ 80% on service's golden set (adjust up for higher-risk services) | CI blocks merge; threshold in service config, reviewed on change |
| Secret scanning | Zero detected secrets | CI blocks merge |
| Container image scan | No critical CVEs unmitigated | CI blocks image push |
| Canary rollout | Minimum 10% canary, minimum 5-min bake, then ramp | Deploy pipeline enforces; no `AllAtOnce` in production |
| Live quality alarm | Custom quality metric wired to deployment group; auto-rollback on breach | Deployment configuration enforces |

**Rollback SLAs:**

- **Canary auto-rollback** (quality alarm → traffic shift): ≤ 5 minutes from alarm to stable-only traffic. This is automated; human action not required.
- **Manual rollback** (on-call decides to roll back a fully-promoted release): ≤ 15 minutes from decision to 100% traffic on prior bundle. Runbook must be documented and tested quarterly.
- **Emergency rollback** (production incident, on-call cannot wait for automation): ≤ 5 minutes to 0% on new bundle. On-call must have pre-provisioned access to the traffic-split CLI without approvals.

**Who can override a gate:**

Override means skipping a required gate to ship to production. This must be exceptional, audited, and time-bounded.

- Allowed for: genuine production outages where the fix is blocked by a gate fire that is confirmed to be a false positive.
- Requires: two approvers (tech lead + engineering manager), written justification, incident ticket filed.
- Not allowed for: "we're in a hurry," "the gate is annoying," or routine releases.
- Every override is reviewed in the next week's tech review and must produce either a fix to the gate (if false positive) or a golden-set case (if the override revealed a gap).

**Golden-set maintenance standard:**

- Each service's golden set is owned by the team; changes require a PR with at least one reviewer who is not the author.
- Minimum size: 20 cases covering happy path + known-tricky inputs.
- Every production incident that resulted from a quality regression adds at least one new golden-set case before the incident is closed.
- Quarterly review: remove stale cases, re-calibrate thresholds against current baseline pass-rate.

**Why this matters at Staff/Principal level:** the standard removes ambiguity that individual teams fill in inconsistently. Without it, one team has a 95% threshold (trigger-happy, slows velocity), another has a 50% threshold (useless), and no team agrees on who can override. The standard is the floor, not the ceiling — teams can add stricter gates; they cannot remove required ones without a policy change.

---

## Summary

CI/CD for GenAI adds an AI quality gate and quality-driven rollback to the normal pipeline. At senior level it is about scaling eval gates across services, choosing the right rollout strategy, and an org-wide release-safety standard.

See the subtopic guides: [versioning](01_versioning_deployment/interview.md) · [automated testing](02_automated_testing/interview.md) · [deployment strategies](03_deployment_strategies/interview.md) · [AWS CI/CD](04_aws_cicd/interview.md).

## References

- AWS CodeDeploy — deployment configurations: https://docs.aws.amazon.com/codedeploy/latest/userguide/deployment-configurations.html
- Google SRE — Canarying Releases: https://sre.google/workbook/canarying-releases/
- Azure Container Apps — revisions & traffic splitting: https://learn.microsoft.com/azure/container-apps/revisions
