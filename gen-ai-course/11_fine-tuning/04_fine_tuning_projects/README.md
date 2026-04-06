# Fine-Tuning Projects

A collection of fine-tuning projects using Python, Transformers, PEFT, and FastAPI + Uvicorn for deployment.

## Projects Overview

| # | Project | Dataset | Status |
|---|---------|---------|--------|
| 01 | Custom Chatbot / Assistant | OASST1, Alpaca, Dolly-15K | ✅ Implemented |
| 02 | Medical Q&A | MedQuAD (~47K) | 📋 Structure Only |
| 03 | Legal / Finance Assistant | LegalBench, Finance-Alpaca | ✅ Implemented |
| 04 | E-commerce / Customer Support | Bitext, Amazon QA | 📋 Structure Only |

## Project Architecture

```
fine_tuning_projects/
├── 01_chatbot/              # Custom Chatbot (Implemented)
│   ├── configs/
│   ├── notebooks/
│   ├── src/chatbot_ft/
│   ├── scripts/
│   ├── deploy/
│   └── tests/
│
├── 02_medical_qa/           # Medical Q&A (Structure)
│   ├── configs/
│   ├── notebooks/
│   ├── src/
│   ├── scripts/
│   ├── deploy/
│   └── tests/
│
├── 03_legal_finance/        # Legal/Finance (Implemented)
│   ├── configs/
│   ├── notebooks/
│   ├── src/
│   ├── scripts/
│   ├── deploy/
│   └── tests/
│
└── 04_ecommerce/            # E-commerce (Structure)
    ├── configs/
    ├── notebooks/
    ├── src/
    ├── scripts/
    ├── deploy/
    └── tests/
```

## Common Workflow

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         FINE-TUNING PIPELINE                                │
└─────────────────────────────────────────────────────────────────────────────┘

  ┌──────────┐     ┌──────────────┐     ┌─────────────┐     ┌────────────┐
  │  Raw     │     │   Data       │     │  Tokenize   │     │  LoRA      │
  │  Dataset │ ──► │   Cleaning   │ ──► │  + Format   │ ──► │  Training  │
  │  (HF)    │     │  (Dedup,     │     │  (Masking)  │     │  (PEFT)    │
  └──────────┘     │   Filter)    │     └─────────────┘     └────────────┘
                   └──────────────┘                                  │
                                                                  ▼
  ┌──────────┐     ┌──────────────┐     ┌─────────────┐     ┌────────────┐
  │  Metrics │ ◄── │   Evaluate   │ ◄── │   Adapter   │ ◄── │  Save      │
  │  (BLEU,  │     │   (BLEU,     │     │   Artifacts │     │  Checkpoint│
  │  ROUGE)  │     │   ROUGE)     │     └─────────────┘     └────────────┘
  └──────────┘     └──────────────┘
                            │
                            ▼
                   ┌─────────────────┐
                   │   FastAPI +     │
                   │   Uvicorn       │
                   │   Deployment    │
                   └─────────────────┘
```

## Dataset Summary

### Project 01: Custom Chatbot
- **OpenAssistant OASST1**: ~1.16M messages
- **Alpaca-cleaned**: ~52K rows  
- **Dolly-15K**: ~15K rows

### Project 02: Medical Q&A
- **MedQuAD**: ~47K rows (primary)
- **ChatDoctor**: ~100K rows (fallback)

### Project 03: Legal/Finance
- **LegalBench**: Instruction set (size varies)
- **Finance-Alpaca**: ~68K rows

### Project 04: E-commerce
- **Bitext Customer Support**: ~27K rows
- **Amazon QA**: (size varies)

## Data Cleaning Plan

For each project:

1. **Remove duplicates** - SHA-256 hash of (instruction + input + output)
2. **Filter invalid entries** - Min instruction length (10), min response length (20)
3. **Text normalization** - Trim whitespace, normalize newlines
4. **Instruction formatting** - Alpaca-style format with prompt/response sections
5. **Tokenization** - With label masking (prompt tokens = -100)

## Training Configuration

```yaml
# Default training parameters
batch_size: 4
gradient_accumulation: 4
learning_rate: 2e-4
epochs: 3
max_length: 512
gradient_checkpointing: true
mixed_precision: bf16

# LoRA configuration
lora_r: 16
lora_alpha: 32
lora_dropout: 0.05
target_modules: [q_proj, v_proj, k_proj, o_proj]
```

## Evaluation Metrics

| Metric | Description |
|--------|-------------|
| BLEU | N-gram overlap score |
| ROUGE-L | Longest common subsequence |
| Exact Match | String equality |
| Perplexity | Model confidence |

## Deployment

Each project includes FastAPI + Uvicorn deployment:

```python
# Start server
uvicorn deploy.main:app --host 0.0.0.0 --port 8000

# API endpoint
POST /generate
{
  "instruction": "Your question here",
  "input_text": "Optional context",
  "temperature": 0.7,
  "max_new_tokens": 256
}
```

## Monitoring & Rollback

```bash
# Monitor GPU usage
python scripts/monitor.py --mode monitor --interval 30

# Create backup checkpoint
python scripts/rollback.py backup --source models/project_name

# Rollback to previous checkpoint
python scripts/rollback.py rollback --target models/project_name
```

## Cloud Training Recommendations

| Provider | Instance Type | Use Case |
|----------|--------------|----------|
| Google Colab Pro+ | A100, T4 | Fast prototyping |
| AWS SageMaker | ml.g5.xlarge | Managed training |
| Azure GPU VM | NC-series | Enterprise |

## Setup Instructions

1. **Create virtual environment**:
```bash
cd fine_tuning_projects/01_chatbot
python -m venv .venv
. .venv/Scripts/activate
```

2. **Install dependencies**:
```bash
pip install -e .
```

3. **Configure accelerate**:
```bash
accelerate config default
```

4. **Run preprocessing**:
```bash
python scripts/prepare_data.py --config configs/train_config.yaml
```

5. **Train model**:
```bash
accelerate launch scripts/train.py --config configs/train_config.yaml
```

6. **Evaluate**:
```bash
python scripts/evaluate.py --config configs/train_config.yaml
```

7. **Deploy**:
```bash
uvicorn deploy.main:app --host 0.0.0.0 --port 8000
```

## Requirements

All projects use:
- `transformers` - Model loading and training
- `datasets` - Dataset handling
- `accelerate` - Distributed training
- `peft` - LoRA/QLoRA fine-tuning
- `fastapi` - API framework
- `uvicorn` - ASGI server
- `evaluate` - Metrics calculation
- `torch` - Deep learning framework

## License

MIT License