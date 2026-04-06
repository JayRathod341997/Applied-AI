"""Dataset loading, cleaning, formatting, and tokenization for e-commerce support."""

from __future__ import annotations

import hashlib
import json
import logging
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable

import torch
from datasets import Dataset, DatasetDict, load_dataset, load_from_disk
from transformers import PreTrainedTokenizerBase

from .config import AppConfig

LOGGER = logging.getLogger(__name__)


def normalize_text(text: Any) -> str:
    if text is None:
        return ""
    if isinstance(text, list):
        text = " ".join(str(item) for item in text)
    if isinstance(text, dict):
        text = " ".join(str(value) for value in text.values())
    text = str(text).strip()
    text = re.sub(r"\s+", " ", text)
    return text


def build_prompt(instruction: str, input_text: str = "") -> str:
    instruction = normalize_text(instruction)
    input_text = normalize_text(input_text)
    if input_text:
        return (
            "You are an e-commerce customer support assistant. "
            "Provide accurate, concise, policy-safe, and empathetic responses.\n\n"
            f"### Customer Query:\n{instruction}\n\n"
            f"### Product/Order Context:\n{input_text}\n\n"
            "### Agent Response:\n"
        )
    return (
        "You are an e-commerce customer support assistant. "
        "Provide accurate, concise, policy-safe, and empathetic responses.\n\n"
        f"### Customer Query:\n{instruction}\n\n"
        "### Agent Response:\n"
    )


@dataclass(slots=True)
class SupervisedDataCollator:
    tokenizer: PreTrainedTokenizerBase
    pad_to_multiple_of: int | None = 8

    def __call__(self, features: list[dict[str, Any]]) -> dict[str, torch.Tensor]:
        input_features = {
            "input_ids": [feature["input_ids"] for feature in features],
            "attention_mask": [feature["attention_mask"] for feature in features],
        }
        batch = self.tokenizer.pad(
            input_features,
            padding=True,
            return_tensors="pt",
            pad_to_multiple_of=self.pad_to_multiple_of,
        )
        max_len = batch["input_ids"].shape[1]
        labels = torch.full((len(features), max_len), -100, dtype=torch.long)
        for i, feature in enumerate(features):
            sequence = torch.tensor(feature["labels"], dtype=torch.long)
            labels[i, : len(sequence)] = sequence
        batch["labels"] = labels
        return batch


class EcommerceDatasetPipeline:
    """Builds instruction datasets from Bitext Customer Support and Amazon QA."""

    def __init__(self, config: AppConfig):
        self.config = config
        self.processed_root = Path(config.data.processed_dir)
        self.raw_split_dir = self.processed_root / "raw_splits"

    def _is_valid(self, row: dict[str, str]) -> bool:
        return (
            len(row["instruction"]) >= self.config.data.min_prompt_chars
            and len(row["output"]) >= self.config.data.min_response_chars
        )

    def _hash_row(self, row: dict[str, str]) -> str:
        digest = hashlib.sha256()
        digest.update(row["instruction"].lower().encode("utf-8"))
        digest.update(row["input"].lower().encode("utf-8"))
        digest.update(row["output"].lower().encode("utf-8"))
        return digest.hexdigest()

    def _pick_first(self, row: dict[str, Any], keys: list[str]) -> str:
        for key in keys:
            if key in row:
                value = normalize_text(row.get(key))
                if value:
                    return value
        return ""

    def _iter_dataset_rows(self, dataset_id: str, scan_limit: int) -> Iterable[dict[str, Any]]:
        try:
            stream = load_dataset(
                dataset_id,
                split="train",
                streaming=True,
                cache_dir=self.config.data.cache_dir,
            )
            for idx, row in enumerate(stream):
                if idx >= scan_limit:
                    break
                yield row
            return
        except Exception as exc:
            LOGGER.warning("Streaming load failed for %s: %s", dataset_id, exc)

        dataset = load_dataset(
            dataset_id,
            split="train",
            cache_dir=self.config.data.cache_dir,
        )
        limit = min(scan_limit, len(dataset))
        for row in dataset.select(range(limit)):
            yield row

    def _load_bitext(self) -> list[dict[str, str]]:
        max_samples = self.config.data.max_samples_per_dataset.get("bitext_customer_support", 7000)
        scan_limit = self.config.data.bitext_scan_examples

        prompt_keys = [
            "instruction",
            "question",
            "customer_message",
            "utterance",
            "input",
            "prompt",
            "text",
        ]
        context_keys = ["context", "category", "intent", "product", "product_title", "title"]
        response_keys = [
            "response",
            "answer",
            "output",
            "agent_response",
            "assistant_response",
            "target",
        ]

        for dataset_id in self.config.data.bitext_dataset_candidates:
            LOGGER.info("Trying Bitext dataset candidate: %s", dataset_id)
            rows: list[dict[str, str]] = []
            try:
                for record in self._iter_dataset_rows(dataset_id, scan_limit=scan_limit):
                    instruction = self._pick_first(record, prompt_keys)
                    output = self._pick_first(record, response_keys)
                    input_text = self._pick_first(record, context_keys)
                    if not instruction or not output:
                        continue
                    rows.append(
                        {
                            "instruction": instruction,
                            "input": input_text,
                            "output": output,
                            "source": "bitext_customer_support",
                        }
                    )
                    if len(rows) >= max_samples:
                        break
                if rows:
                    LOGGER.info("Loaded %d rows from %s", len(rows), dataset_id)
                    return rows
            except Exception as exc:
                LOGGER.warning("Bitext candidate failed (%s): %s", dataset_id, exc)

        LOGGER.warning("Bitext dataset unavailable. Using synthetic fallback rows.")
        return self._fallback_bitext_samples(max_samples=max_samples)

    def _coerce_answer(self, answer: Any) -> str:
        if isinstance(answer, dict):
            if "text" in answer:
                return normalize_text(answer["text"])
            return normalize_text(answer)
        if isinstance(answer, list):
            if not answer:
                return ""
            return normalize_text(answer[0])
        return normalize_text(answer)

    def _load_amazon_qa(self) -> list[dict[str, str]]:
        max_samples = self.config.data.max_samples_per_dataset.get("amazon_qa", 7000)
        scan_limit = self.config.data.amazon_scan_examples

        question_keys = ["question", "query", "instruction", "title", "prompt"]
        context_keys = [
            "context",
            "product_title",
            "product",
            "category",
            "description",
            "metadata",
        ]
        answer_keys = ["answer", "answers", "best_answer", "response", "output", "target"]

        for dataset_id in self.config.data.amazon_qa_dataset_candidates:
            LOGGER.info("Trying Amazon QA dataset candidate: %s", dataset_id)
            rows: list[dict[str, str]] = []
            try:
                for record in self._iter_dataset_rows(dataset_id, scan_limit=scan_limit):
                    instruction = self._pick_first(record, question_keys)

                    output = ""
                    for key in answer_keys:
                        if key in record:
                            output = self._coerce_answer(record[key])
                            if output:
                                break

                    input_text = self._pick_first(record, context_keys)
                    if not instruction or not output:
                        continue
                    rows.append(
                        {
                            "instruction": instruction,
                            "input": input_text,
                            "output": output,
                            "source": "amazon_qa",
                        }
                    )
                    if len(rows) >= max_samples:
                        break
                if rows:
                    LOGGER.info("Loaded %d rows from %s", len(rows), dataset_id)
                    return rows
            except Exception as exc:
                LOGGER.warning("Amazon QA candidate failed (%s): %s", dataset_id, exc)

        LOGGER.warning("Amazon QA dataset unavailable. Using synthetic fallback rows.")
        return self._fallback_amazon_samples(max_samples=max_samples)

    def _fallback_bitext_samples(self, max_samples: int) -> list[dict[str, str]]:
        seed_rows = [
            {
                "instruction": "My package says delivered but I did not receive it. What can you do?",
                "input": "Order status: delivered 4 hours ago. Item: wireless mouse.",
                "output": "I am sorry this happened. I can start a missing package claim and offer a replacement or refund based on your preference.",
                "source": "bitext_customer_support",
            },
            {
                "instruction": "Can I return shoes after 20 days if worn once indoors?",
                "input": "Return policy: 30 days. Condition: lightly used allowed for footwear.",
                "output": "Yes, this qualifies for return within 30 days. Please use the returns portal and select the original order.",
                "source": "bitext_customer_support",
            },
            {
                "instruction": "How long does international shipping take to Germany?",
                "input": "Shipping options: standard 7-12 business days, express 3-5 business days.",
                "output": "Standard shipping usually takes 7 to 12 business days, and express shipping takes 3 to 5 business days.",
                "source": "bitext_customer_support",
            },
        ]
        rows: list[dict[str, str]] = []
        while len(rows) < max_samples:
            rows.extend(seed_rows)
        return rows[:max_samples]

    def _fallback_amazon_samples(self, max_samples: int) -> list[dict[str, str]]:
        seed_rows = [
            {
                "instruction": "Does this charger support fast charging for Samsung S22?",
                "input": "Product: 25W USB-C charger. Compatibility notes mention Samsung PPS support.",
                "output": "Yes, this charger supports Samsung fast charging through PPS for compatible devices like the S22.",
                "source": "amazon_qa",
            },
            {
                "instruction": "Is this blender jar dishwasher safe?",
                "input": "Product details: BPA-free jar; top-rack dishwasher safe.",
                "output": "Yes, the jar is dishwasher safe on the top rack.",
                "source": "amazon_qa",
            },
            {
                "instruction": "Will this keyboard work with macOS?",
                "input": "Product description: Bluetooth keyboard compatible with Windows, macOS, iOS, Android.",
                "output": "Yes, it works with macOS over Bluetooth. Media key mapping may vary by app.",
                "source": "amazon_qa",
            },
        ]
        rows: list[dict[str, str]] = []
        while len(rows) < max_samples:
            rows.extend(seed_rows)
        return rows[:max_samples]

    def build_raw_splits(self, force_rebuild: bool = False) -> DatasetDict:
        if self.raw_split_dir.exists() and not force_rebuild:
            LOGGER.info("Loading cached raw split dataset from %s", self.raw_split_dir)
            return load_from_disk(str(self.raw_split_dir))

        rows: list[dict[str, str]] = []
        rows.extend(self._load_bitext())
        rows.extend(self._load_amazon_qa())

        deduped_rows: list[dict[str, str]] = []
        seen_hashes: set[str] = set()
        for row in rows:
            row["instruction"] = normalize_text(row["instruction"])
            row["input"] = normalize_text(row["input"])
            row["output"] = normalize_text(row["output"])
            if not self._is_valid(row):
                continue
            row_hash = self._hash_row(row)
            if row_hash in seen_hashes:
                continue
            seen_hashes.add(row_hash)
            deduped_rows.append(row)

        if not deduped_rows:
            raise RuntimeError("No valid training data available after cleaning/deduplication.")

        max_total = min(self.config.data.max_samples_total, len(deduped_rows))
        dataset = Dataset.from_list(deduped_rows).shuffle(seed=self.config.seed).select(range(max_total))

        first_split = dataset.train_test_split(
            test_size=(1.0 - self.config.data.train_split),
            seed=self.config.seed,
        )
        holdout = first_split["test"]
        holdout_test_size = self.config.data.test_split / (
            self.config.data.val_split + self.config.data.test_split
        )
        second_split = holdout.train_test_split(test_size=holdout_test_size, seed=self.config.seed)
        dataset_dict = DatasetDict(
            {
                "train": first_split["train"],
                "validation": second_split["train"],
                "test": second_split["test"],
            }
        )

        self.raw_split_dir.mkdir(parents=True, exist_ok=True)
        dataset_dict.save_to_disk(str(self.raw_split_dir))
        self._save_data_report(dataset_dict)
        LOGGER.info("Saved raw split dataset to %s", self.raw_split_dir)
        return dataset_dict

    def _tokenized_dir(self, tokenizer: PreTrainedTokenizerBase) -> Path:
        model_tag = tokenizer.name_or_path.replace("/", "__")
        return self.processed_root / f"tokenized_{model_tag}_{self.config.model.max_seq_length}"

    def tokenize_splits(
        self,
        tokenizer: PreTrainedTokenizerBase,
        force_rebuild: bool = False,
    ) -> DatasetDict:
        tokenized_dir = self._tokenized_dir(tokenizer)
        if tokenized_dir.exists() and not force_rebuild:
            LOGGER.info("Loading cached tokenized dataset from %s", tokenized_dir)
            return load_from_disk(str(tokenized_dir))

        raw = self.build_raw_splits(force_rebuild=force_rebuild)

        if tokenizer.pad_token is None:
            tokenizer.pad_token = tokenizer.eos_token
        eos = tokenizer.eos_token or ""
        max_len = self.config.model.max_seq_length

        def _tokenize_row(row: dict[str, Any]) -> dict[str, list[int]]:
            prompt = build_prompt(row["instruction"], row.get("input", ""))
            response = normalize_text(row["output"]) + eos
            prompt_tokens = tokenizer(prompt, add_special_tokens=False)
            full_tokens = tokenizer(
                prompt + response,
                add_special_tokens=False,
                truncation=True,
                max_length=max_len,
            )
            input_ids = full_tokens["input_ids"]
            attention_mask = full_tokens["attention_mask"]
            labels = input_ids.copy()
            prompt_len = min(len(prompt_tokens["input_ids"]), len(labels))
            labels[:prompt_len] = [-100] * prompt_len
            return {
                "input_ids": input_ids,
                "attention_mask": attention_mask,
                "labels": labels,
            }

        tokenized = DatasetDict()
        for split_name in raw.keys():
            tokenized[split_name] = raw[split_name].map(
                _tokenize_row,
                remove_columns=raw[split_name].column_names,
                desc=f"Tokenizing {split_name}",
            )

        tokenized_dir.mkdir(parents=True, exist_ok=True)
        tokenized.save_to_disk(str(tokenized_dir))
        LOGGER.info("Saved tokenized dataset to %s", tokenized_dir)
        return tokenized

    def _save_data_report(self, dataset_dict: DatasetDict) -> None:
        source_counts: dict[str, int] = {}
        for split_name in dataset_dict.keys():
            if "source" in dataset_dict[split_name].column_names:
                for source in dataset_dict[split_name]["source"]:
                    source_counts[source] = source_counts.get(source, 0) + 1

        report = {
            "train_samples": len(dataset_dict["train"]),
            "validation_samples": len(dataset_dict["validation"]),
            "test_samples": len(dataset_dict["test"]),
            "source_counts": source_counts,
        }
        report_path = self.processed_root / "dataset_report.json"
        report_path.parent.mkdir(parents=True, exist_ok=True)
        report_path.write_text(json.dumps(report, indent=2), encoding="utf-8")

