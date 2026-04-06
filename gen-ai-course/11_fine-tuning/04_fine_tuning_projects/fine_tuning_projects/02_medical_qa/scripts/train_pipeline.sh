#!/usr/bin/env bash
# ============================================================
#  Medical Q&A - End-to-End Training Pipeline
#  Run from project root:  bash scripts/train_pipeline.sh
# ============================================================
set -euo pipefail

PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$PROJECT_DIR"
echo "Working directory: $PROJECT_DIR"

LOG_DIR="$PROJECT_DIR/logs"
mkdir -p "$LOG_DIR"

TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
LOG_FILE="$LOG_DIR/pipeline_$TIMESTAMP.log"
exec > >(tee -a "$LOG_FILE") 2>&1

echo "========================================"
echo "  Medical Q&A Fine-Tuning Pipeline"
echo "  $(date)"
echo "========================================"

# ── 1. Environment check ─────────────────────────────────────
echo "[1/5] Checking environment ..."
python -c "import torch; print('PyTorch:', torch.__version__); print('CUDA:', torch.cuda.is_available())"
python -c "import transformers; print('Transformers:', transformers.__version__)"
python -c "import peft; print('PEFT:', peft.__version__)"

# ── 2. GPU monitor (background) ──────────────────────────────
echo "[2/5] Starting GPU monitor in background ..."
python scripts/monitor_gpu.py \
  --interval 10 \
  --log "$LOG_DIR/gpu_monitor_$TIMESTAMP.csv" &
MONITOR_PID=$!
echo "Monitor PID: $MONITOR_PID"

# ── 3. Preprocess ────────────────────────────────────────────
echo "[3/5] Preprocessing data ..."
python src/preprocess.py
echo "Preprocessing complete."

# ── 4. Train ─────────────────────────────────────────────────
echo "[4/5] Starting LoRA fine-tuning ..."
python src/train.py --config configs/training_config.yaml
echo "Training complete."

# ── 5. Evaluate ──────────────────────────────────────────────
echo "[5/5] Evaluating model ..."
MODEL_PATH="models/medical_qa_lora/final"
if [ -d "$MODEL_PATH" ]; then
  mkdir -p results
  python src/evaluate.py \
    --model_path "$MODEL_PATH" \
    --data_path  data/processed/formatted \
    --split      test \
    --max_samples 200 \
    --output     results/eval_report_$TIMESTAMP.json
  echo "Evaluation report: results/eval_report_$TIMESTAMP.json"
else
  echo "WARNING: Model not found at $MODEL_PATH — skipping evaluation."
fi

# ── Cleanup ──────────────────────────────────────────────────
kill $MONITOR_PID 2>/dev/null || true
echo "========================================"
echo "  Pipeline finished: $(date)"
echo "  Log: $LOG_FILE"
echo "========================================"
