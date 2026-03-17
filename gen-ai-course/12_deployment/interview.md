# Deployment - Interview Questions

This document contains interview questions and answers covering Module 12: Deployment.

---

## 1. Deployment Overview

### Q1: What are the different deployment options for GenAI?

**Answer:** Deployment options:

- **Cloud APIs:** OpenAI, Anthropic, Azure OpenAI
- **Self-hosted:** Run models on your infrastructure
- **Serverless:** Cloud functions for inference
- **Edge:** Deploy to edge devices
- **Hybrid:** Combine cloud and on-prem

---

### Q2: What are the factors to consider for GenAI deployment?

**Answer:** Factors:

- **Latency:** Response time requirements
- **Cost:** Inference costs, infrastructure
- **Scalability:** Traffic volume
- **Security:** Data privacy requirements
- **Customization:** Need fine-tuning?
- **Maintenance:** Ongoing support needs

---

### Q3: What are the deployment patterns?

**Answer:** Patterns:

- **API First:** REST/gRPC endpoints
- **Embedded:** Library integration
- **Streaming:** Real-time responses
- **Batch:** Offline processing
- **Agentic:** Autonomous workflows

---

## 2. Deployment Techniques

### Q4: What is serverless deployment?

**Answer:** Serverless:

- **No Server Management:** Cloud handles infrastructure
- **Scale Automatically:** Pay per request
- **Examples:** AWS Lambda, Azure Functions, GCP Cloud Functions
- **Use Cases:** Variable traffic, cost optimization
- **Limitations:** Cold starts, timeout limits

---

### Q5: What is container deployment?

**Answer:** Container deployment:

- **Docker:** Package application + dependencies
- **Kubernetes:** Orchestrate containers
- **Benefits:** Consistent environment, portable
- **Use Cases:** Production workloads, scaling

```dockerfile
FROM python:3.10
COPY . /app
RUN pip install -r requirements.txt
CMD ["python", "app.py"]
```

---

### Q6: How do you deploy with Kubernetes?

**Answer:** Kubernetes deployment:

1. **Containerize:** Create Docker image
2. **Define Resources:** CPU, memory limits
3. **Configure HPA:** Auto-scaling
4. **Service:** Expose the deployment
5. **Ingress:** Route external traffic

---

## 3. Implementation

### Q7: How do you deploy to Azure?

**Answer:** Azure deployment:

1. **Azure OpenAI:** Use managed service
2. **Azure Container Apps:** Serverless containers
3. **Azure Kubernetes Service:** Full control
4. **Azure ML:** Managed ML deployment

```python
from azure.ai.ml import MLClient
# Deploy model
```

---

### Q8: How do you deploy to AWS?

**Answer:** AWS deployment:

1. **SageMaker Endpoints:** Managed inference
2. **Lambda:** Serverless (for small models)
3. **ECS/EKS:** Container deployment
4. **Bedrock:** Managed foundation models

---

### Q9: What is the deployment process?

**Answer:** Process:

1. **Build:** Package application
2. **Test:** Integration testing
3. **Stage:** Deploy to staging
4. **Validate:** Smoke tests
5. **Production:** Blue/green or canary
6. **Monitor:** Watch for issues
7. **Rollback:** If problems occur

---

## Production Questions

### Q10: How do you handle deployment failures?

**Answer:** Handling:

1. **Health Checks:** Verify deployment
2. **Rollback:** Revert to previous version
3. **Circuit Breaker:** Stop traffic to failing service
4. **Alerting:** Notify team
5. **Logging:** Record failures

---

### Q11: What are deployment strategies?

**Answer:** Strategies:

- **Blue-Green:** Two identical environments
- **Canary:** Gradual rollout to subset
- **Rolling:** Gradually replace instances
- **Feature Flags:** Toggle features

---

### Q12: How do you optimize deployment costs?

**Answer:** Optimization:

1. **Right-size Resources:** Match needs
2. **Auto-scaling:** Scale down when idle
3. **Caching:** Cache responses
4. **Spot Instances:** Use preemptible
5. **Serverless:** Pay per use

---

## Summary

Key deployment topics:

1. **Overview:** Options, factors
2. **Techniques:** Serverless, containers
3. **Implementation:** Azure, AWS
4. **Production:** Failures, strategies

---

## References

- [Deployment Best Practices](references.md)
- [Cloud Deployment Guides](references.md)
