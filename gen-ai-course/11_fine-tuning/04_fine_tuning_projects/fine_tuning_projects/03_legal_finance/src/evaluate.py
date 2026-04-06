"""
Legal/Finance Model Evaluation

Evaluates fine-tuned model using:
- ROUGE-L for summary quality
- BERTScore for semantic similarity
- Exact Match and F1 for entity extraction
- Perplexity for language modeling

Environment: PyTorch 2.4, Transformers 4.46, evaluate
"""

import os
import json
import logging
import argparse
from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Dict, Any, Optional

import torch
import numpy as np
from datasets import Dataset, load_from_disk
from transformers import (
    AutoModelForCausalLM,
    AutoTokenizer,
    GenerationConfig,
)
from peft import PeftModel
from tqdm.auto import tqdm
import evaluate

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler("logs/evaluation.log"),
        logging.StreamHandler(),
    ],
)
logger = logging.getLogger(__name__)


@dataclass
class EvaluationConfig:
    """Configuration for model evaluation."""

    model_path: str = "experiments/fine_tuned_model"
    base_model: str = "microsoft/finbert-tone"
    test_data_path: str = "data/processed/sft_dataset"
    output_dir: str = "experiments"

    # Generation
    max_new_tokens: int = 150
    temperature: float = 0.7
    top_p: float = 0.9
    num_beams: int = 4
    length_penalty: float = 1.2

    # Evaluation
    num_samples: int = 100
    batch_size: int = 8
    max_length: int = 512


class LegalFinanceEvaluator:
    """Evaluator for legal-finance model."""

    def __init__(self, config: EvaluationConfig):
        self.config = config
        self.tokenizer = None
        self.model = None
        self.rouge = None
        self.bertscore = None
        self.perplexity = None

    def load_model(self):
        """Load model and tokenizer."""
        logger.info(f"Loading base model: {self.config.base_model}")

        self.tokenizer = AutoTokenizer.from_pretrained(
            self.config.base_model,
            trust_remote_code=True,
        )

        if self.tokenizer.pad_token is None:
            self.tokenizer.pad_token = self.tokenizer.eos_token

        device = "cuda" if torch.cuda.is_available() else "cpu"

        base_model = AutoModelForCausalLM.from_pretrained(
            self.config.base_model,
            torch_dtype=torch.float16 if device == "cuda" else torch.float32,
            device_map="auto" if device == "cuda" else None,
            trust_remote_code=True,
        )

        if os.path.exists(self.config.model_path):
            logger.info(f"Loading PEFT adapters from: {self.config.model_path}")
            self.model = PeftModel.from_pretrained(
                base_model,
                self.config.model_path,
                is_trainable=False,
            )
        else:
            logger.warning("PEFT model path not found, using base model")
            self.model = base_model

        self.model.eval()
        logger.info("Model loaded successfully")

    def initialize_metrics(self):
        """Initialize evaluation metrics."""
        logger.info("Initializing metrics...")

        self.rouge = evaluate.load("rouge")
        self.bertscore = evaluate.load("bertscore")
        self.perplexity = evaluate.load(
            "perplexity", device="cuda" if torch.cuda.is_available() else "cpu"
        )

        logger.info("Metrics initialized")

    def generate_summary(self, instruction: str, context: str = "") -> str:
        """Generate summary for a document."""
        prompt = f"""Below is a legal or financial document. Provide a concise, accurate summary.

### Document:
{context[:1500]}

### Summary:
"""

        inputs = self.tokenizer(
            prompt,
            return_tensors="pt",
            truncation=True,
            max_length=self.config.max_length - self.config.max_new_tokens,
        )

        if torch.cuda.is_available():
            inputs = {k: v.to(self.model.device) for k, v in inputs.items()}

        generation_config = GenerationConfig(
            max_new_tokens=self.config.max_new_tokens,
            temperature=self.config.temperature,
            top_p=self.config.top_p,
            num_beams=self.config.num_beams,
            length_penalty=self.config.length_penalty,
            do_sample=True,
            pad_token_id=self.tokenizer.pad_token_id,
            eos_token_id=self.tokenizer.eos_token_id,
        )

        with torch.no_grad():
            outputs = self.model.generate(
                **inputs,
                generation_config=generation_config,
            )

        input_length = inputs["input_ids"].shape[1]
        generated_tokens = outputs[0][input_length:]

        return self.tokenizer.decode(generated_tokens, skip_special_tokens=True).strip()

    def evaluate_summaries(self, dataset: Dataset) -> Dict[str, Any]:
        """Evaluate summary generation."""
        logger.info(f"Evaluating {len(dataset)} samples...")

        references = []
        predictions = []

        for i, sample in enumerate(tqdm(dataset, desc="Generating summaries")):
            if i >= self.config.num_samples:
                break

            # Get input and reference
            context = sample.get("text", "")
            reference = sample.get("output", "")

            # Extract just the response part if needed
            if "### Response:" in context:
                context = context.split("### Response:")[-1].strip()

            # Generate
            generated = self.generate_summary(
                instruction="Summarize this document",
                context=context,
            )

            predictions.append(generated)
            references.append(reference)

        logger.info("Computing ROUGE scores...")
        rouge_scores = self.rouge.compute(
            predictions=predictions,
            references=references,
            use_aggregator=True,
        )

        logger.info("Computing BERTScore...")
        bert_scores = self.bertscore.compute(
            predictions=predictions,
            references=references,
            model_type="microsoft/deberta-xlarge-mnli",
        )

        logger.info("Computing Perplexity...")
        perplexity_inputs = self.tokenizer(
            references,
            return_tensors="pt",
            padding=True,
            truncation=True,
            max_length=self.config.max_length,
        )

        if torch.cuda.is_available():
            perplexity_inputs = {
                k: v.to(self.model.device) for k, v in perplexity_inputs.items()
            }

        ppl = self.perplexity.compute(
            model_id=self.config.base_model,
            input_ids=perplexity_inputs["input_ids"],
            attention_mask=perplexity_inputs["attention_mask"],
        )

        # Exact match
        exact_matches = sum(
            1
            for pred, ref in zip(predictions, references)
            if pred.strip().lower() == ref.strip().lower()
        )
        exact_match = exact_matches / len(predictions) if predictions else 0

        metrics = {
            "rouge_1": rouge_scores.get("rouge1", 0),
            "rouge_2": rouge_scores.get("rouge2", 0),
            "rouge_l": rouge_scores.get("rougeL", 0),
            "rouge_lsum": rouge_scores.get("rougeLsum", 0),
            "bertscore_precision": np.mean(bert_scores["precision"]),
            "bertscore_recall": np.mean(bert_scores["recall"]),
            "bertscore_f1": np.mean(bert_scores["f1"]),
            "perplexity": ppl.get("mean_perplexity", 0),
            "exact_match": exact_match,
            "num_samples": len(predictions),
        }

        return metrics

    def evaluate_entity_extraction(
        self,
        dataset: Dataset,
        extract_fn,
    ) -> Dict[str, Any]:
        """Evaluate entity extraction F1."""
        logger.info("Evaluating entity extraction...")

        all_pred_entities = []
        all_true_entities = []

        for i, sample in enumerate(tqdm(dataset, desc="Extracting entities")):
            if i >= self.config.num_samples:
                break

            text = sample.get("text", "")

            # Get predicted entities from model (using extract_fn)
            pred_entities = extract_fn(text)

            # Get true entities from dataset
            true_entities = []
            if "entities" in sample:
                true_entities = (
                    json.loads(sample["entities"])
                    if isinstance(sample["entities"], str)
                    else sample["entities"]
                )

            all_pred_entities.append(pred_entities)
            all_true_entities.append(true_entities)

        # Calculate F1 for each entity type
        entity_types = ["MONEY", "DATE", "PERCENTAGE", "LEGAL_REGULATION", "COMPANY"]
        f1_scores = {}

        for entity_type in entity_types:
            true_positive = 0
            false_positive = 0
            false_negative = 0

            for pred, true in zip(all_pred_entities, all_true_entities):
                pred_set = set(
                    [e["text"] for e in pred if e.get("type") == entity_type]
                )
                true_set = set(
                    [e["text"] for e in true if e.get("type") == entity_type]
                )

                true_positive += len(pred_set & true_set)
                false_positive += len(pred_set - true_set)
                false_negative += len(true_set - pred_set)

            precision = (
                true_positive / (true_positive + false_positive)
                if (true_positive + false_positive) > 0
                else 0
            )
            recall = (
                true_positive / (true_positive + false_negative)
                if (true_positive + false_negative) > 0
                else 0
            )
            f1 = (
                2 * precision * recall / (precision + recall)
                if (precision + recall) > 0
                else 0
            )

            f1_scores[entity_type] = {
                "precision": precision,
                "recall": recall,
                "f1": f1,
            }

        return f1_scores

    def run_evaluation(self, extract_fn=None) -> Dict[str, Any]:
        """Run full evaluation."""
        logger.info("=" * 60)
        logger.info("Starting Model Evaluation")
        logger.info("=" * 60)

        self.load_model()
        self.initialize_metrics()

        # Load test dataset
        try:
            dataset = load_from_disk(self.config.test_data_path)
            if "test" in dataset:
                test_dataset = dataset["test"]
            else:
                test_dataset = dataset["train"].select(
                    range(min(self.config.num_samples, len(dataset["train"])))
                )
        except Exception as e:
            logger.error(f"Could not load test data: {e}")
            return {}

        # Evaluate summaries
        summary_metrics = self.evaluate_summaries(test_dataset)

        # Evaluate entities if extraction function provided
        entity_metrics = {}
        if extract_fn:
            entity_metrics = self.evaluate_entity_extraction(test_dataset, extract_fn)

        # Compile results
        results = {
            "summary_metrics": summary_metrics,
            "entity_extraction_f1": entity_metrics,
            "config": {
                "model_path": self.config.model_path,
                "base_model": self.config.base_model,
                "num_samples": self.config.num_samples,
            },
        }

        # Save results
        output_path = Path(self.config.output_dir)
        output_path.mkdir(parents=True, exist_ok=True)

        with open(output_path / "evaluation_results.json", "w") as f:
            json.dump(results, f, indent=2)

        logger.info(f"Results saved to {output_path / 'evaluation_results.json'}")

        # Print summary
        logger.info("=" * 60)
        logger.info("EVALUATION RESULTS")
        logger.info("=" * 60)

        logger.info("Summary Metrics:")
        for key, value in summary_metrics.items():
            if isinstance(value, float):
                logger.info(f"  {key}: {value:.4f}")
            else:
                logger.info(f"  {key}: {value}")

        if entity_metrics:
            logger.info("\nEntity Extraction F1:")
            for entity_type, scores in entity_metrics.items():
                logger.info(
                    f"  {entity_type}: P={scores['precision']:.4f}, R={scores['recall']:.4f}, F1={scores['f1']:.4f}"
                )

        return results


def create_parser() -> argparse.ArgumentParser:
    """Create argument parser."""
    parser = argparse.ArgumentParser(description="Legal/Finance Model Evaluator")

    parser.add_argument(
        "--model_path", type=str, default="experiments/fine_tuned_model"
    )
    parser.add_argument("--base_model", type=str, default="microsoft/finbert-tone")
    parser.add_argument(
        "--test_data_path", type=str, default="data/processed/sft_dataset"
    )
    parser.add_argument("--output_dir", type=str, default="experiments")
    parser.add_argument("--num_samples", type=int, default=100)
    parser.add_argument("--max_new_tokens", type=int, default=150)

    return parser


def main():
    """Main entry point."""
    parser = create_parser()
    args = parser.parse_args()

    config = EvaluationConfig(
        model_path=args.model_path,
        base_model=args.base_model,
        test_data_path=args.test_data_path,
        output_dir=args.output_dir,
        num_samples=args.num_samples,
        max_new_tokens=args.max_new_tokens,
    )

    evaluator = LegalFinanceEvaluator(config)
    results = evaluator.run_evaluation()

    print("\n" + "=" * 60)
    print("FINAL EVALUATION METRICS")
    print("=" * 60)
    print(json.dumps(results, indent=2))


if __name__ == "__main__":
    main()
