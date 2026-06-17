# References

Curated, real external reading for scalability and performance of GenAI systems.

## Scaling & Autoscaling

- **Kubernetes — Horizontal Pod Autoscaler** — official docs on HPA, custom metrics, and scaling behavior.
  https://kubernetes.io/docs/tasks/run-application/horizontal-pod-autoscale/
- **KEDA — Kubernetes Event-Driven Autoscaling** — event-driven autoscaling and scale-to-zero.
  https://keda.sh/docs/latest/concepts/
- **Knative Serving — Autoscaling (scale-to-zero)** — request-driven autoscaling down to zero replicas.
  https://knative.dev/docs/serving/autoscaling/
- **AWS Auto Scaling — User Guide** — target tracking, step scaling, and scaling policies on AWS.
  https://docs.aws.amazon.com/autoscaling/application/userguide/what-is-application-auto-scaling.html

## Load Balancing

- **AWS — Load Balancing patterns (Elastic Load Balancing)** — algorithms, health checks, and routing.
  https://docs.aws.amazon.com/elasticloadbalancing/latest/userguide/what-is-load-balancing.html
- **NGINX — HTTP load balancing methods** — round-robin, least-connections, and weighted upstreams.
  https://docs.nginx.com/nginx/admin-guide/load-balancer/http-load-balancer/

## Caching

- **Redis — Caching & TTL / expiration** — using Redis as a cache, key expiry, and eviction policies.
  https://redis.io/docs/latest/develop/use/keyspace/#key-expiration
- **GPTCache** — open-source semantic cache for LLM applications (embedding + similarity lookup).
  https://github.com/zilliztech/GPTCache
- **AWS Architecture — Caching best practices** — caching patterns, invalidation, and TTL guidance.
  https://aws.amazon.com/caching/best-practices/

## Model Serving & Throughput

- **vLLM — Continuous batching & PagedAttention** — high-throughput LLM serving internals.
  https://docs.vllm.ai/en/latest/
- **vLLM blog — "Easy, Fast, and Cheap LLM Serving with PagedAttention"** — the original throughput deep-dive.
  https://blog.vllm.ai/2023/06/20/vllm.html

## Connection Pooling

- **HTTPX — Connection pools & limits** — keep-alive, `max_connections`, and pooling in Python clients.
  https://www.python-httpx.org/advanced/#pool-limit-configuration
