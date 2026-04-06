# Scripts

- `prepare_data.py`: load/clean/dedupe/format and tokenize Bitext + Amazon QA subsets.
- `train.py`: LoRA fine-tuning runner via `accelerate`.
- `evaluate.py`: BLEU, ROUGE, exact-match accuracy evaluation.
- `serve.py`: FastAPI app launcher with `uvicorn`.
- `monitor_gpu.py`: GPU usage logger using `nvidia-smi`.
- `rollback.py`: backup and rollback utility for model artifacts.
