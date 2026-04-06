# 04 - E-commerce / Customer Support Bot (Implemented)

Local, notebook-first fine-tuning pipeline for customer support and product Q&A using:
- Bitext Customer Support
- Amazon QA (subset)

This implementation is tuned for fast local iteration via subset sampling and LoRA.

## Notebook First
- [01_ecommerce_support_bot.ipynb](/d:/Jay%20Rathod/Tutorials/Applied%20AI/gen-ai-course/11_fine-tuning/04_fine_tuning_projects/fine_tuning_projects/04_ecommerce/notebooks/01_ecommerce_support_bot.ipynb)

## What Is Included
- Dataset loading with fallback candidate strategy
- Data cleaning, dedupe, and instruction formatting
- Tokenization with prompt masking
- LoRA fine-tuning (`transformers`, `datasets`, `accelerate`, `peft`)
- Evaluation (BLEU, ROUGE, exact-match accuracy)
- FastAPI + `uvicorn` deployment
- GPU monitor and rollback utilities

## Workflow
```text
Bitext + Amazon QA subsets
   -> cleaning + dedupe + formatting
   -> train/validation/test split
   -> tokenization + label masking
   -> LoRA fine-tuning
   -> evaluation (BLEU/ROUGE/accuracy)
   -> FastAPI inference with uvicorn
```

## Setup
```bash
cd fine_tuning_projects/04_ecommerce
python -m venv .venv
. .venv/Scripts/activate
pip install -U pip
pip install -e .
accelerate config default
```

## Run
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

4. Serve:
```bash
python scripts/serve.py --config configs/train_config.yaml --host 0.0.0.0 --port 8000
```

## API Example
```bash
curl -X POST "http://127.0.0.1:8000/generate" \
  -H "Content-Type: application/json" \
  -d "{\"message\":\"My order is delayed, what can I do?\",\"context\":\"Order shipped 8 days ago.\"}"
```

## Default Training Parameters
- Batch size: `4`
- Gradient accumulation: `8`
- Learning rate: `2e-4`
- Epochs: `1`
- Gradient checkpointing: `true`
- Mixed precision: `fp16`

Config file: [train_config.yaml](/d:/Jay%20Rathod/Tutorials/Applied%20AI/gen-ai-course/11_fine-tuning/04_fine_tuning_projects/fine_tuning_projects/04_ecommerce/configs/train_config.yaml)

## Optional Utilities
- GPU monitor: `python scripts/monitor_gpu.py --interval 5`
- Backup model: `python scripts/rollback.py backup`
- Rollback model: `python scripts/rollback.py rollback`

## Cloud Recommendations
- Google Colab Pro/Pro+ for prototype runs
- SageMaker for managed experiments
- Azure GPU VMs / Azure ML for scalable training
