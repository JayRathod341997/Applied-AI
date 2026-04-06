# 01 - Custom Chatbot / Assistant (Implemented)

Local, notebook-first fine-tuning pipeline for a style/domain assistant using:
- OpenAssistant OASST1
- Alpaca Cleaned
- Dolly-15K

This implementation is optimized for fast local iteration by using **subset sampling** and **LoRA**.

## Local Hardware Snapshot
Detected on this machine (`nvidia-smi` on April 6, 2026):
- GPU: `NVIDIA GeForce RTX 2060`
- VRAM: `6 GB`
- CUDA Runtime: `12.5`

## What Is Included
- Data loading + cleaning + dedupe + instruction formatting
- Tokenization and supervised labels (`-100` prompt masking)
- LoRA fine-tuning with `transformers`, `datasets`, `accelerate`, `peft`
- Evaluation script with BLEU, ROUGE, and exact-match accuracy
- FastAPI + `uvicorn` inference server
- Optional GPU monitoring and rollback scripts
- Notebook first: `notebooks/01_custom_chatbot_assistant.ipynb`

## Project Workflow
```text
Raw HF Datasets
  |  (OASST1 + Alpaca + Dolly subsets)
  v
Data Cleaning + Dedupe + Prompt Formatting
  v
Split Dataset (train/validation/test)
  v
Tokenization with Label Masking
  v
LoRA Fine-Tuning (accelerate + Trainer)
  v
Adapter Artifacts + Metrics JSON
  v
Evaluation (BLEU/ROUGE/Exact Match)
  v
FastAPI Inference Service (uvicorn)
```

## Directory Layout
```text
01_chatbot/
  configs/
    train_config.yaml
  notebooks/
    01_custom_chatbot_assistant.ipynb
  src/chatbot_ft/
    config.py
    data.py
    modeling.py
    training.py
    evaluation.py
    utils/logging_utils.py
  scripts/
    prepare_data.py
    train.py
    evaluate.py
    serve.py
    monitor_gpu.py
    rollback.py
  deploy/
    app.py
  tests/
    test_formatting.py
```

## Setup
1. Create env and install package:
```bash
cd fine_tuning_projects/01_chatbot
python -m venv .venv
. .venv/Scripts/activate  # Windows PowerShell: .venv\Scripts\Activate.ps1
pip install -U pip
pip install -e .
```

2. Configure accelerate once:
```bash
accelerate config default
```

## Run End-to-End
1. Prepare data:
```bash
python scripts/prepare_data.py --config configs/train_config.yaml
```

2. Train:
```bash
accelerate launch scripts/train.py --config configs/train_config.yaml
```

3. Evaluate:
```bash
python scripts/evaluate.py --config configs/train_config.yaml --split test --max_eval_samples 300
```

4. Serve API:
```bash
python scripts/serve.py --config configs/train_config.yaml --host 0.0.0.0 --port 8000
```

## API Example
```bash
curl -X POST "http://127.0.0.1:8000/generate" \
  -H "Content-Type: application/json" \
  -d "{\"message\":\"Explain transformers in simple terms.\"}"
```

## Data Cleaning Plan
- Normalize whitespace and trim text
- Remove invalid samples using min prompt/response length thresholds
- Deduplicate using SHA-256 hash of `(instruction,input,output)`
- Convert each sample to instruction format:
  - With input block when context exists
  - Without input block otherwise

## Training Parameters (Default)
- Batch size: `4`
- Gradient accumulation: `8`
- Learning rate: `2e-4`
- Epochs: `1` (fast baseline; increase after first sanity run)
- Gradient checkpointing: `true`
- Mixed precision: `fp16`

Adjust these in [train_config.yaml](/d:/Jay%20Rathod/Tutorials/Applied%20AI/gen-ai-course/11_fine-tuning/04_fine_tuning_projects/fine_tuning_projects/01_chatbot/configs/train_config.yaml).

## Monitoring + Rollback (Optional)
- GPU logging:
```bash
python scripts/monitor_gpu.py --interval 5 --output models/gpu_usage_log.csv
```
- Create backup:
```bash
python scripts/rollback.py backup --source models/custom_chatbot --backup_root models/backups
```
- Rollback:
```bash
python scripts/rollback.py rollback --target models/custom_chatbot --backup_root models/backups
```

## Cloud Training Recommendations
- Google Colab Pro/Pro+: fast prototyping with T4/L4/A100 options.
- AWS SageMaker: managed training jobs and scalable experiment tracking.
- Azure ND/NC GPU VMs or Azure ML compute clusters: strong enterprise integration.

Suggested minimum for larger models than GPT-Neo-125M:
- 16-24 GB VRAM (single GPU) for smoother LoRA experiments
- 32+ GB for larger context windows and faster throughput

## Notes
- The default config is intentionally conservative for local runs.
- To use larger base models, reduce sequence length and batch size first.
- OASST1 parsing uses parent-child message links and English filtering.

