# References

Authoritative sources for the patterns in this subtopic. Read the Fowler and Nygard pieces first for the conceptual core, then the AWS and Google SRE material for production practice.

1. **Martin Fowler — CircuitBreaker**
   The canonical write-up of the breaker state machine, thresholds, and half-open probing.
   https://martinfowler.com/bliki/CircuitBreaker.html

2. **Michael Nygard — *Release It!* (2nd ed.)**
   The book that popularized circuit breakers, bulkheads, timeouts, and "stability patterns" for production systems.
   https://pragprog.com/titles/mnee2/release-it-second-edition/

3. **AWS Architecture Blog — Exponential Backoff and Jitter**
   Marc Brooker's analysis of full vs. equal vs. decorrelated jitter and why jitter beats plain backoff.
   https://aws.amazon.com/blogs/architecture/exponential-backoff-and-jitter/

4. **AWS Well-Architected Framework — Reliability Pillar**
   Production guidance on failure management, throttling, retries, and graceful degradation.
   https://docs.aws.amazon.com/wellarchitected/latest/reliability-pillar/welcome.html

5. **Google SRE Book — Handling Overload & Addressing Cascading Failures**
   How retries, load shedding, and graceful degradation prevent cascading outages at scale.
   https://sre.google/sre-book/handling-overload/
   https://sre.google/sre-book/addressing-cascading-failures/

6. **tenacity — Python retry library documentation**
   Declarative retries with `stop_after_attempt`, `wait_exponential_jitter`, and retry predicates.
   https://tenacity.readthedocs.io/

7. **Polly — .NET resilience and transient-fault-handling library**
   Reference implementation of retry, circuit breaker, timeout, bulkhead, and fallback policies.
   https://github.com/App-vNext/Polly

8. **Kubernetes — Configure Liveness, Readiness and Startup Probes**
   Official guidance on the three probe types and the restart-vs-drain distinction.
   https://kubernetes.io/docs/tasks/configure-pod-container/configure-liveness-readiness-startup-probes/

9. **Netflix Hystrix — How it Works (wiki)**
   Influential JVM circuit-breaker/bulkhead library; the design notes remain a great primer even though it's now maintenance-only.
   https://github.com/Netflix/Hystrix/wiki/How-it-Works

10. **Microsoft Azure Architecture Center — Resiliency patterns**
    Catalog of Circuit Breaker, Retry, Bulkhead, and Throttling patterns with sequence diagrams.
    https://learn.microsoft.com/en-us/azure/architecture/patterns/category/resiliency
