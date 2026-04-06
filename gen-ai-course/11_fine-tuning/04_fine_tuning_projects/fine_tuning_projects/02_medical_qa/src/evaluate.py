"""
Medical Q&A - Evaluation Module

Metrics:
  ROUGE-1 / ROUGE-2 / ROUGE-L, BLEU (sacrebleu), Exact Match, latency

Usage:
  python src/evaluate.py --model_path models/medical_qa_lora/final \
                         --data_path  data/processed/formatted     \
                         --split test --output results/eval_report.json
"""
from __future__ import annotations

import argparse
import json
import logging
import time
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import torch
from datasets import Dataset, load_from_disk
from peft import PeftModel
from rouge_score import rouge_scorer
from sacrebleu.metrics import BLEU
from tqdm.auto import tqdm
from transformers import AutoModelForCausalLM, AutoTokenizer, GenerationConfig

logging.basicConfig(level=logging.INFO,
                    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)


class MedicalQAPredictor:
    """Loads a (LoRA-)fine-tuned model and generates answers."""

    def __init__(self, model_path: str, base_model: Optional[str] = None,
                 max_new_tokens: int = 256, temperature: float = 0.7,
                 top_p: float = 0.9, device: Optional[str] = None):
        self.max_new_tokens = max_new_tokens
        self.device = device or ("cuda" if torch.cuda.is_available() else "cpu")

        logger.info(f"Loading model from {model_path} on {self.device}")
        self.tokenizer = AutoTokenizer.from_pretrained(model_path, trust_remote_code=True)
        if self.tokenizer.pad_token is None:
            self.tokenizer.pad_token = self.tokenizer.eos_token

        dtype = torch.float16 if self.device == "cuda" else torch.float32
        dmap = "auto" if self.device == "cuda" else None

        if base_model:
            base = AutoModelForCausalLM.from_pretrained(
                base_model, torch_dtype=dtype, device_map=dmap, trust_remote_code=True)
            self.model = PeftModel.from_pretrained(base, model_path)
        else:
            self.model = AutoModelForCausalLM.from_pretrained(
                model_path, torch_dtype=dtype, device_map=dmap, trust_remote_code=True)

        self.model.eval()
        self.generation_config = GenerationConfig(
            max_new_tokens=max_new_tokens, temperature=temperature, top_p=top_p,
            do_sample=True, pad_token_id=self.tokenizer.pad_token_id,
            eos_token_id=self.tokenizer.eos_token_id)

    @torch.inference_mode()
    def predict(self, prompt: str) -> str:
        inputs = self.tokenizer(prompt, return_tensors="pt",
                                truncation=True, max_length=512).to(self.device)
        output_ids = self.model.generate(**inputs, generation_config=self.generation_config)
        new_ids = output_ids[0][inputs["input_ids"].shape[1]:]
        return self.tokenizer.decode(new_ids, skip_special_tokens=True).strip()


def compute_rouge(predictions: List[str], references: List[str]) -> Dict[str, float]:
    scorer = rouge_scorer.RougeScorer(["rouge1", "rouge2", "rougeL"], use_stemmer=True)
    agg = {"rouge1": 0.0, "rouge2": 0.0, "rougeL": 0.0}
    for pred, ref in zip(predictions, references):
        scores = scorer.score(ref, pred)
        for key in agg:
            agg[key] += scores[key].fmeasure
    n = max(len(predictions), 1)
    return {k: round(v / n, 4) for k, v in agg.items()}


def compute_bleu(predictions: List[str], references: List[str]) -> float:
    bleu = BLEU(effective_order=True)
    return round(bleu.corpus_score(predictions, [references]).score, 4)


def compute_exact_match(predictions: List[str], references: List[str]) -> float:
    def _norm(t: str) -> str:
        return " ".join(t.lower().strip().split())
    return round(sum(_norm(p) == _norm(r) for p, r in zip(predictions, references))
                 / max(len(predictions), 1), 4)


def evaluate(predictor: MedicalQAPredictor, dataset: Dataset,
             max_samples: Optional[int] = None) -> Tuple[Dict, List[str], List[str]]:
    """Run generation on dataset and compute metrics.
    Dataset must have columns: prompt, response.
    """
    if max_samples:
        dataset = dataset.select(range(min(max_samples, len(dataset))))

    predictions, references, latencies = [], [], []
    for example in tqdm(dataset, desc="Generating"):
        t0 = time.perf_counter()
        pred = predictor.predict(example["prompt"])
        latencies.append(time.perf_counter() - t0)
        predictions.append(pred)
        references.append(example["response"])

    rouge = compute_rouge(predictions, references)
    results = {
        "num_samples": len(predictions),
        **rouge,
        "bleu": compute_bleu(predictions, references),
        "exact_match": compute_exact_match(predictions, references),
        "avg_pred_len_words": round(sum(len(p.split()) for p in predictions) / max(len(predictions), 1), 2),
        "avg_ref_len_words": round(sum(len(r.split()) for r in references) / max(len(references), 1), 2),
        "avg_latency_sec": round(sum(latencies) / max(len(latencies), 1), 3),
        "p50_latency_sec": round(sorted(latencies)[len(latencies) // 2], 3),
    }

    logger.info("=== Evaluation Results ===")
    for k, v in results.items():
        logger.info(f"  {k:<30}: {v}")

    return results, predictions, references


def main() -> None:
    p = argparse.ArgumentParser(description="Evaluate Medical Q&A fine-tuned model")
    p.add_argument("--model_path", required=True)
    p.add_argument("--base_model", default=None)
    p.add_argument("--data_path", default="data/processed/formatted")
    p.add_argument("--split", default="test")
    p.add_argument("--max_samples", type=int, default=200)
    p.add_argument("--max_new_tokens", type=int, default=256)
    p.add_argument("--output", default="results/eval_report.json")
    args = p.parse_args()

    ds_dict = load_from_disk(args.data_path)
    dataset = ds_dict[args.split]

    predictor = MedicalQAPredictor(
        model_path=args.model_path, base_model=args.base_model,
        max_new_tokens=args.max_new_tokens)

    metrics, preds, refs = evaluate(predictor, dataset, max_samples=args.max_samples)

    out_path = Path(args.output)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with open(out_path, "w") as f:
        json.dump({"metrics": metrics,
                   "samples": [{"prediction": preds[i], "reference": refs[i]}
                                for i in range(min(20, len(preds)))]}, f, indent=2)
    logger.info(f"Report saved → {out_path}")


if __name__ == "__main__":
    main()
