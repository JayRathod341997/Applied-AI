"""Evaluation utilities for BLEU, ROUGE, and exact-match accuracy."""

from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any

import evaluate
import torch
from datasets import load_from_disk
from tqdm.auto import tqdm

from .config import AppConfig, load_config, resolve_project_paths
from .data import build_prompt
from .modeling import load_model_for_inference, load_tokenizer

LOGGER = logging.getLogger(__name__)


def _normalize_answer(text: str) -> str:
    return " ".join(text.strip().lower().split())


def _extract_new_text(full_text: str, prompt: str) -> str:
    if full_text.startswith(prompt):
        return full_text[len(prompt) :].strip()
    return full_text.strip()


@torch.no_grad()
def evaluate_model(
    config: AppConfig,
    split: str = "test",
    max_eval_samples: int = 300,
    adapter_dir: str | None = None,
) -> dict[str, float]:
    tokenizer = load_tokenizer(config)

    if adapter_dir is None:
        adapter_dir = str(Path(config.training.output_dir) / "adapter")
    model = load_model_for_inference(config, adapter_dir=adapter_dir)

    raw_split_dir = Path(config.data.processed_dir) / "raw_splits"
    if not raw_split_dir.exists():
        raise FileNotFoundError(
            f"Raw dataset splits not found at {raw_split_dir}. Run prepare_data.py first."
        )
    datasets = load_from_disk(str(raw_split_dir))
    if split not in datasets:
        raise ValueError(f"Split '{split}' not found. Available: {list(datasets.keys())}")

    dataset = datasets[split]
    sample_count = min(len(dataset), max_eval_samples)
    dataset = dataset.select(range(sample_count))

    predictions: list[str] = []
    references: list[str] = []

    for row in tqdm(dataset, total=sample_count, desc=f"Evaluating {split}"):
        prompt = build_prompt(row["instruction"], row.get("input", ""))
        model_inputs = tokenizer(prompt, return_tensors="pt")

        if torch.cuda.is_available():
            model_inputs = {k: v.cuda() for k, v in model_inputs.items()}

        generated = model.generate(
            **model_inputs,
            max_new_tokens=config.generation.max_new_tokens,
            temperature=config.generation.temperature,
            top_p=config.generation.top_p,
            repetition_penalty=config.generation.repetition_penalty,
            do_sample=True,
            eos_token_id=tokenizer.eos_token_id,
            pad_token_id=tokenizer.pad_token_id,
        )
        text = tokenizer.decode(generated[0], skip_special_tokens=True)
        prediction = _extract_new_text(text, prompt)
        reference = row["output"].strip()
        predictions.append(prediction)
        references.append(reference)

    bleu = evaluate.load("bleu")
    rouge = evaluate.load("rouge")

    bleu_result = bleu.compute(predictions=predictions, references=[[ref] for ref in references])
    rouge_result = rouge.compute(predictions=predictions, references=references)

    exact_match = sum(
        _normalize_answer(p) == _normalize_answer(r) for p, r in zip(predictions, references)
    ) / len(predictions)

    metrics = {
        "bleu": float(bleu_result["bleu"]),
        "rouge1": float(rouge_result["rouge1"]),
        "rouge2": float(rouge_result["rouge2"]),
        "rougeL": float(rouge_result["rougeL"]),
        "exact_match_accuracy": float(exact_match),
    }

    metrics_path = Path(config.training.output_dir) / f"evaluation_{split}.json"
    metrics_path.write_text(json.dumps(metrics, indent=2), encoding="utf-8")
    LOGGER.info("Saved evaluation report to %s", metrics_path)
    return metrics


def evaluate_model_from_path(
    config_path: str | Path,
    project_root: str | Path,
    split: str = "test",
    max_eval_samples: int = 300,
    adapter_dir: str | None = None,
) -> dict[str, Any]:
    cfg = load_config(config_path)
    cfg = resolve_project_paths(cfg, project_root=project_root)
    return evaluate_model(
        config=cfg,
        split=split,
        max_eval_samples=max_eval_samples,
        adapter_dir=adapter_dir,
    )

