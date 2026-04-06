# Medical Q&A Fine-Tuning Project

Fine-tune a biomedical language model (`BioGPT-Large`) with LoRA on a medical Q&A dataset, then serve it via a FastAPI + Uvicorn inference API.

---

## Workflow (ASCII Diagram)

```
┌─────────────────────────────────────────────────────────────────────────┐
│                     MEDICAL Q&A FINE-TUNING PIPELINE                    │
└─────────────────────────────────────────────────────────────────────────┘

  ┌────────────────────────────┐
  │  DATASETS (HuggingFace Hub)│
  │  ─────────────────────────│
  │  Primary:                  │
  │  lavita/ChatDoctor-        │
  │  HealthCareMagic-100k      │
  │  (100 K rows, subset 5 K) │
  │                            │
  │  Fallback:                 │
  │  medalpaca/medical_meadow  │
  │  _medqa                    │
  └────────────┬───────────────┘
               │
               ▼
  ┌────────────────────────────┐
  │  src/preprocess.py         │
  │  ─────────────────────────│
  │  1. Load (Hub or local)    │
  │  2. Normalise columns      │
  │  3. Length filter          │
  │  4. SHA-256 deduplication  │
  │  5. Instruction template   │
  │     ### Question: ...      │
  │     ### Response: ...      │
  │  6. Tokenise (BioGPT tok.) │
  │  7. Label masking (-100    │
  │     on prompt tokens)      │
  │  8. 90/5/5 split           │
  │  9. Save → data/processed/ │
  └────────────┬───────────────┘
               │
               ▼
  ┌────────────────────────────┐
  │  src/train.py              │
  │  ─────────────────────────│
  │  Base: BioGPT-Large        │
  │  LoRA (r=16, alpha=32)     │
  │  applied to q_proj, v_proj │
  │                            │
  │  TrainingArguments:        │
  │  • epochs=3                │
  │  • batch=2, grad_acc=8     │
  │  • lr=2e-4 (cosine)        │
  │  • grad checkpointing=True │
  │  • early stopping (p=2)    │
  │                            │
  │  Saves checkpoints +       │
  │  final model               │
  └────────────┬───────────────┘
               │
               ▼
  ┌────────────────────────────┐
  │  src/evaluate.py           │
  │  ─────────────────────────│
  │  • ROUGE-1 / 2 / L         │
  │  • BLEU (sacrebleu)        │
  │  • Exact Match             │
  │  • Avg / P50 latency       │
  │  Output: results/*.json    │
  └────────────┬───────────────┘
               │
               ▼
  ┌────────────────────────────┐
  │  deploy/app.py             │
  │  FastAPI + Uvicorn         │
  │  ─────────────────────────│
  │  POST /answer              │
  │  POST /answer/batch        │
  │  GET  /health              │
  │  GET  /model/info          │
  └────────────────────────────┘

  Side process (optional):
  ┌────────────────────────────┐
  │  scripts/monitor_gpu.py   │
  │  • GPU util / VRAM / temp  │
  │  • CPU + RAM               │
  │  • CSV log                 │
  └────────────────────────────┘
```

---

## Project Structure

```
02_medical_qa/
├── notebooks/
│   └── medical_qa_finetune.ipynb   ← start here
├── src/
│   ├── __init__.py
│   ├── preprocess.py               ← data pipeline
│   ├── train.py                    ← LoRA training
│   ├── evaluate.py                 ← ROUGE / BLEU / EM
│   └── inference.py                ← inference engine
├── deploy/
│   └── app.py                      ← FastAPI server
├── configs/
│   └── training_config.yaml        ← all hyperparameters
├── scripts/
│   ├── monitor_gpu.py              ← GPU / system monitor
│   └── train_pipeline.sh           ← one-click pipeline
├── tests/
│   ├── test_preprocess.py
│   └── test_inference.py
├── data/
│   ├── raw/                        ← HuggingFace cache
│   └── processed/                  ← tokenised datasets
├── models/
│   └── medical_qa_lora/
│       ├── checkpoint-*/
│       └── final/                  ← best model
├── results/                        ← eval reports
└── logs/                           ← training + GPU logs
```

---

## Dataset

| Dataset | Source | Size | Notes |
|---|---|---|---|
| ChatDoctor-HealthCareMagic-100k | `lavita/ChatDoctor-HealthCareMagic-100k` | 100 K | Primary |
| Medical Meadow MedQA | `medalpaca/medical_meadow_medqa` | ~10 K | Fallback |
| Synthetic | Built-in | 5 rows | Offline safety net |

Default training uses a **5 000-row subset**. Set `subset_size: null` in `configs/training_config.yaml` for the full dataset.

---

## Model Architecture

```
BioGPT-Large (1.5B params)
    │
    └─ LoRA Adapters (trainable, ~0.5% of total params)
         ├─ q_proj  (rank 16)
         └─ v_proj  (rank 16)
```

| Parameter | Value |
|---|---|
| Base model | `microsoft/BioGPT-Large` |
| LoRA rank (r) | 16 |
| LoRA alpha | 32 |
| LoRA dropout | 0.05 |
| Target modules | q_proj, v_proj |
| Task type | CAUSAL_LM |

---

## Training Configuration

| Parameter | Value | Notes |
|---|---|---|
| Epochs | 3 | with early stopping (patience=2) |
| Batch size (per device) | 2 | 1 for CPU |
| Gradient accumulation | 8 | effective batch = 16 |
| Learning rate | 2e-4 | cosine decay |
| Warmup ratio | 5% | |
| Weight decay | 0.01 | |
| Max grad norm | 1.0 | |
| Gradient checkpointing | ✓ | reduces VRAM |
| Mixed precision | fp16 (CUDA) | float32 on CPU |
| Sequence length | 512 tokens | |

---

## Evaluation Metrics

| Metric | Description |
|---|---|
| ROUGE-1 | Unigram F1 overlap |
| ROUGE-2 | Bigram F1 overlap |
| ROUGE-L | Longest common subsequence F1 |
| BLEU | sacrebleu corpus score |
| Exact Match | Normalised string equality |
| Avg Latency | Mean inference time per sample (s) |
| P50 Latency | Median inference time (s) |

---

## Setup

### Prerequisites

- Python 3.9+
- Git
- (Optional) CUDA GPU with ≥8 GB VRAM

### 1. Navigate to project

```bash
cd fine_tuning_projects/02_medical_qa
```

### 2. Create virtual environment

```bash
python -m venv .venv
# Windows
.venv\Scripts\activate
# Linux / macOS
source .venv/bin/activate
```

### 3. Install dependencies

```bash
pip install transformers datasets peft accelerate \
            sacrebleu rouge-score psutil pynvml \
            fastapi uvicorn httpx pytest pydantic \
            pandas tqdm PyYAML matplotlib
```

### 4. Run the full pipeline

```bash
bash scripts/train_pipeline.sh
```

Or step-by-step:

```bash
python src/preprocess.py
python src/train.py --config configs/training_config.yaml
python src/evaluate.py \
  --model_path models/medical_qa_lora/final \
  --data_path  data/processed/formatted \
  --split      test \
  --output     results/eval_report.json
```

### 5. Start the API server

```bash
uvicorn deploy.app:app --host 0.0.0.0 --port 8000 --reload
```

### 6. Test the API

```bash
# Health check
curl http://localhost:8000/health

# Single question
curl -X POST http://localhost:8000/answer \
     -H "Content-Type: application/json" \
     -d '{"question": "What are the symptoms of Type 2 diabetes?"}'

# Batch
curl -X POST http://localhost:8000/answer/batch \
     -H "Content-Type: application/json" \
     -d '{"questions": ["What is hypertension?", "What does metformin do?"]}'
```

### 7. Run tests

```bash
pytest tests/ -v --tb=short
```

---

## Notebook

Open `notebooks/medical_qa_finetune.ipynb` — covers all steps interactively with visualisations.

---

## GPU Monitoring

```bash
# Poll every 5 s, log to CSV
python scripts/monitor_gpu.py --interval 5 --log logs/gpu_monitor.csv

# Run for 2 hours
python scripts/monitor_gpu.py --interval 10 --log logs/gpu.csv --duration 7200
```

---

## Deployment API Reference

### `POST /answer`

```json
Request:  { "question": "What are symptoms of Type 2 diabetes?", "context": "" }
Response: { "question": "...", "answer": "Common symptoms include...", "latency_ms": 342.5 }
```

### `POST /answer/batch`

```json
Request:  { "questions": ["Q1", "Q2"], "contexts": ["ctx1", ""] }
Response: { "answers": ["A1", "A2"], "latency_ms": 680.1 }
```

### Environment variables

| Variable | Default | Description |
|---|---|---|
| `MODEL_PATH` | `models/medical_qa_lora/final` | Path to fine-tuned model |
| `BASE_MODEL` | `None` | Base model (if adapter-only path) |
| `MAX_NEW_TOKENS` | `512` | Max generation length |
| `TEMPERATURE` | `0.7` | Sampling temperature |
| `PORT` | `8000` | Server port |

---

## Cloud Training Resources

| Platform | GPU | VRAM | ~Time (5k/3ep) | Cost/hr |
|---|---|---|---|---|
| Google Colab (free) | T4 | 16 GB | ~45 min | Free |
| Kaggle Notebooks | P100 | 16 GB | ~40 min | Free |
| AWS SageMaker `ml.g4dn.xlarge` | T4 | 16 GB | ~40 min | ~$0.74 |
| Azure `NC6s_v3` | V100 | 16 GB | ~25 min | ~$0.90 |
| RunPod RTX 3090 | 3090 | 24 GB | ~20 min | ~$0.34 |
| Local laptop (CPU) | — | — | hours | Free |

### Colab quick-start

```python
!git clone <your-repo-url>
%cd 02_medical_qa
!pip install -q transformers datasets peft accelerate sacrebleu rouge-score
!python src/preprocess.py
!python src/train.py --config configs/training_config.yaml
```

---

## Local CPU Tips

1. `subset_size: 200` in `training_config.yaml`
2. `num_train_epochs: 1`
3. Change `base_model` to `"EleutherAI/gpt-neo-125m"` for a much smaller model
4. `fp16: false`
5. `gradient_checkpointing: false`

---

## Rollback

```bash
# Use a specific checkpoint instead of the final model
MODEL_PATH=models/medical_qa_lora/checkpoint-500 \
  uvicorn deploy.app:app --port 8000
```

---

## License

For educational purposes. Datasets and base models retain their respective licenses.
**Do not use in production medical settings without clinical validation.**

## Datasets
- **MedQuAD** (~47K rows)
- **ChatDoctor-HealthCareMagic-100k** (fallback)
- **MedAlpaca** (fallback)

## Model Architecture
- Base Model: Llama2-7B or microsoft/BioGPT-Large
- Fine-tuning Method: LoRA (PEFT)

## Training Configuration
- Batch Size: 4-8 (adjust based on GPU memory)
- Learning Rate: 2e-4
- Epochs: 3-5
- Gradient Checkpointing: Enabled
- Mixed Precision: BF16

## Evaluation Metrics
- BLEU Score
- ROUGE-L Score
- Validation Accuracy

## Deployment
- FastAPI + Uvicorn ASGI server

## Setup
See main README.md for detailed setup instructions.