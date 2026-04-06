# Fine-Tuning Projects Workspace

## Current Status
- `01_chatbot`: implemented end-to-end (notebook-first + modular code + API deploy).
- `02_medical_qa`: structure only.
- `03_legal_finance`: structure/draft only.
- `04_ecommerce`: structure only.

## Workspace Flow
```text
Notebook (exploration + config)
    ->
Data Pipeline (cleaning / dedupe / split / tokenize)
    ->
Training (LoRA + accelerate)
    ->
Evaluation (BLEU / ROUGE / Accuracy)
    ->
Deployment (FastAPI + uvicorn)
    ->
Monitoring + Rollback
```

## Quick Start (Project 01)
```bash
cd 01_chatbot
python -m venv .venv
. .venv/Scripts/activate
pip install -U pip
pip install -e .
python scripts/prepare_data.py --config configs/train_config.yaml
accelerate launch scripts/train.py --config configs/train_config.yaml
python scripts/evaluate.py --config configs/train_config.yaml --split test
python scripts/serve.py --config configs/train_config.yaml --host 0.0.0.0 --port 8000
```

