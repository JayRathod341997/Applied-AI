# References: Fine-tuning Implementation

## Official Documentation

### Unsloth
- **GitHub Repository**: https://github.com/unslothai/unsloth
- **Documentation**: https://unsloth.ai/docs
- **Colab Notebooks**: https://github.com/unslothai/unsloth/tree/main/notebooks

### Hugging Face
- **Transformers Library**: https://huggingface.co/docs/transformers
- **PEFT Documentation**: https://huggingface.co/docs/peft
- **TRL (Trainer)**: https://huggingface.co/docs/trl
- **Quantization Guide**: https://huggingface.co/docs/transformers/quantization

### Azure ML
- **Documentation**: https://learn.microsoft.com/azure/machine-learning/
- **Fine-tuning Guide**: https://learn.microsoft.com/azure/machine-learning/how-to-tune-hyperparameters
- **MLflow Integration**: https://learn.microsoft.com/azure/machine-learning/concept-mlflow

### AWS SageMaker
- **Documentation**: https://aws.amazon.com/sagemaker/
- **HuggingFace Estimator**: https://sagemaker.readthedocs.io/en/stable/frameworks/huggingface.html
- **Hyperparameter Tuning**: https://docs.aws.amazon.com/sagemaker/latest/dg/automatic-model-tuning-how-it-works.html

### GCP Vertex AI
- **Documentation**: https://cloud.google.com/vertex-ai
- **Custom Training**: https://cloud.google.com/vertex-ai/docs/training/custom-training
- **Model Registry**: https://cloud.google.com/vertex-ai/docs/model-registry

---

## Tutorials and Guides

### Fine-tuning Best Practices
1. **HuggingFace Fine-tuning Guide**: https://huggingface.co/blog/fine-tune-llm
2. **LoRA Paper**: https://arxiv.org/abs/2106.09685
3. **QLoRA Paper**: https://arxiv.org/abs/2305.14314

### Cloud Platform Tutorials
1. **Azure ML Tutorial**: https://learn.microsoft.com/azure/machine-learning/tutorial-train-deploy-notebook
2. **SageMaker Examples**: https://github.com/aws/amazon-sagemaker-examples
3. **GCP Vertex AI Samples**: https://github.com/GoogleCloudPlatform/vertex-ai-samples

---

## Research Papers

1. **LoRA: Low-Rank Adaptation of Large Language Models**
   - https://arxiv.org/abs/2106.09685

2. **QLoRA: Efficient Finetuning of Quantized LLMs**
   - https://arxiv.org/abs/2305.14314

3. **PEFT: Parameter-Efficient Fine-Tuning**
   - https://arxiv.org/abs/2304.01982

4. **LLaMA: Open and Efficient Foundation Language Models**
   - https://arxiv.org/abs/2302.13971

---

## Useful Libraries

### Training Libraries
- **Unsloth**: Fast fine-tuning
- **PEFT**: Parameter-efficient fine-tuning
- **TRL**: Transformer Reinforcement Learning
- **DeepSpeed**: Large-scale training

### Quantization
- **BitsAndBytes**: 8-bit and 4-bit quantization
- **GPTQ**: Post-training quantization
- **AWQ**: Activation-aware weight quantization

### Inference
- **vLLM**: High-throughput inference
- **Text Generation Inference**: HuggingFace's inference server
- **TensorRT-LLM**: NVIDIA's optimized inference

---

## Video Courses

1. **HuggingFace Course**: https://huggingface.co/learn
2. **DeepLearning.AI Courses**: https://www.deeplearning.ai/short-courses/
3. **Unsloth YouTube**: https://www.youtube.com/@unslothai

---

## Community Resources

### Forums
- **HuggingFace Forums**: https://discuss.huggingface.co
- **r/MachineLearning**: https://reddit.com/r/MachineLearning
- **r/LocalLLaMA**: https://reddit.com/r/LocalLLaMA

### GitHub Repositories
- **Awesome LoRA**: https://github.com/jiangyg/awesome-lora
- **LLM-Finetuning**: https://github.com/ashishps1/awesome-llm-fine-tuning
- **Alpaca**: https://github.com/tatsu-lab/stanford_alpaca

---

## Books

1. "Build a Large Language Model (From Scratch)" - Sebastian Raschka
2. "NLP with Transformers" - O'Reilly
3. "Designing Machine Learning Systems" - Chip Huyen

---

## Cheat Sheets

### Quick Commands

```bash
# Install dependencies
pip install transformers datasets peft accelerate bitsandbytes

# Login to HuggingFace
huggingface-cli login

# Run training
python train.py

# Convert to GGUF format
python -m llama_cpp.convert --hgf-model-path ./model --outfile model.bin
```

### Configuration Quick Reference

```python
# LoRA Configuration
lora_config = LoraConfig(
    r=16,              # Rank (8, 16, 32, 64)
    lora_alpha=32,    # Scaling factor
    lora_dropout=0.05,
    target_modules=["q_proj", "k_proj", "v_proj", "o_proj"],
    bias="none",
)

# Quantization Configuration
bnb_config = BitsAndBytesConfig(
    load_in_4bit=True,
    bnb_4bit_quant_type="nf4",
    bnb_4bit_compute_dtype=torch.float16,
)
```

---

## Additional Reading

### Memory Optimization
- Gradient Checkpointing: https://pytorch.org/docs/stable/checkpoint.html
- Mixed Precision: https://pytorch.org/docs/stable/amp.html

### Evaluation
- HELM: https://crfm.stanford.edu/helm
- LM Evaluation Harness: https://github.com/EleutherAI/lm-evaluation-harness

### Deployment
- FastAPI for LLMs: https://github.com/ray-project/serve
- Docker for LLMs: https://github.com/huggingface/docker-images
