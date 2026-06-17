# References

- **AWS Well-Architected Framework — Machine Learning Lens** — design principles for reliable, scalable ML/AI workloads on AWS: https://docs.aws.amazon.com/wellarchitected/latest/machine-learning-lens/machine-learning-lens.html
- **Martin Fowler — Microservices** — the canonical essay on the microservices style, its trade-offs, and the "monolith first" guidance: https://martinfowler.com/articles/microservices.html
- **Martin Fowler — MonolithFirst** — why most systems should begin as a monolith before being split: https://martinfowler.com/bliki/MonolithFirst.html
- **vLLM Documentation** — PagedAttention, continuous batching, quantization, and tensor-parallel serving: https://docs.vllm.ai/
- **vLLM — Distributed Inference & Tensor Parallelism** — how `--tensor-parallel-size` shards a model across GPUs: https://docs.vllm.ai/en/latest/serving/distributed_serving.html
- **HuggingFace Text Generation Inference (TGI)** — production LLM serving with sharding (`--num-shard`) and continuous batching: https://huggingface.co/docs/text-generation-inference/index
- **Kong API Gateway Documentation** — auth, rate limiting, routing, and plugin patterns at the edge: https://docs.konghq.com/
- **LiteLLM** — an AI-native gateway: unified provider interface, routing, fallbacks, and cost tracking across 100+ LLMs: https://docs.litellm.ai/
- **Envoy Proxy** — L7 load balancing, gRPC, and observability for service-mesh architectures: https://www.envoyproxy.io/docs
- **Apache Kafka Documentation** — event-driven and streaming ingestion pipelines for decoupled, scalable processing: https://kafka.apache.org/documentation/
