"""Dataset loading, cleaning, formatting, and tokenization."""

from __future__ import annotations

import hashlib
import json
import logging
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import torch
from datasets import Dataset, DatasetDict, load_dataset, load_from_disk
from transformers import PreTrainedTokenizerBase

from .config import AppConfig

LOGGER = logging.getLogger(__name__)


def normalize_text(text: str | None) -> str:
    if text is None:
        return ""
    text = text.strip()
    text = re.sub(r"\s+", " ", text)
    return text


def build_prompt(instruction: str, input_text: str = "") -> str:
    instruction = normalize_text(instruction)
    input_text = normalize_text(input_text)
    if input_text:
        return (
            "Below is an instruction describing a task, paired with an input "
            "that provides context. Write a helpful response.\n\n"
            f"### Instruction:\n{instruction}\n\n"
            f"### Input:\n{input_text}\n\n"
            "### Response:\n"
        )
    return (
        "Below is an instruction describing a task. Write a helpful response.\n\n"
        f"### Instruction:\n{instruction}\n\n"
        "### Response:\n"
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


class ChatbotDatasetPipeline:
    """Builds instruction datasets from OASST1, Alpaca, and Dolly."""

    def __init__(self, config: AppConfig):
        self.config = config
        self.processed_root = Path(self.config.data.processed_dir)
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

    def _load_oasst1(self) -> list[dict[str, str]]:
        max_samples = self.config.data.max_samples_per_dataset.get("oasst1", 6000)
        scan_limit = self.config.data.oasst1_scan_messages
        LOGGER.info("Loading OASST1 with scan_limit=%d max_samples=%d", scan_limit, max_samples)

        dataset = load_dataset(
            self.config.data.oasst1_dataset,
            split="train",
            cache_dir=self.config.data.cache_dir,
        )
        scan_limit = min(scan_limit, len(dataset))
        sampled_rows = dataset.select(range(scan_limit)).to_list()

        id_to_row: dict[str, dict[str, Any]] = {}
        for row in sampled_rows:
            row_id = row.get("message_id")
            if row_id:
                id_to_row[row_id] = row

        examples: list[dict[str, str]] = []
        for row in sampled_rows:
            if row.get("role") != "assistant":
                continue
            if row.get("lang") not in (None, "en"):
                continue
            parent = id_to_row.get(row.get("parent_id"))
            if not parent:
                continue
            if parent.get("role") not in ("prompter", "user"):
                continue

            instruction = normalize_text(parent.get("text", ""))
            output = normalize_text(row.get("text", ""))
            if not instruction or not output:
                continue

            examples.append(
                {
                    "instruction": instruction,
                    "input": "",
                    "output": output,
                    "source": "oasst1",
                }
            )
            if len(examples) >= max_samples:
                break

        LOGGER.info("Parsed %d OASST1 instruction pairs", len(examples))
        return examples

    def _load_alpaca(self) -> list[dict[str, str]]:
        max_samples = self.config.data.max_samples_per_dataset.get("alpaca_cleaned", 3000)
        LOGGER.info("Loading Alpaca Cleaned max_samples=%d", max_samples)

        dataset = load_dataset(
            self.config.data.alpaca_dataset,
            split="train",
            cache_dir=self.config.data.cache_dir,
        )
        dataset = dataset.shuffle(seed=self.config.seed).select(range(min(max_samples, len(dataset))))

        examples: list[dict[str, str]] = []
        for row in dataset:
            examples.append(
                {
                    "instruction": normalize_text(row.get("instruction", "")),
                    "input": normalize_text(row.get("input", "")),
                    "output": normalize_text(row.get("output", "")),
                    "source": "alpaca_cleaned",
                }
            )
        LOGGER.info("Loaded %d Alpaca samples", len(examples))
        return examples

    def _load_dolly(self) -> list[dict[str, str]]:
        max_samples = self.config.data.max_samples_per_dataset.get("dolly_15k", 3000)
        LOGGER.info("Loading Dolly-15K max_samples=%d", max_samples)

        dataset = load_dataset(
            self.config.data.dolly_dataset,
            split="train",
            cache_dir=self.config.data.cache_dir,
        )
        dataset = dataset.shuffle(seed=self.config.seed).select(range(min(max_samples, len(dataset))))

        examples: list[dict[str, str]] = []
        for row in dataset:
            examples.append(
                {
                    "instruction": normalize_text(row.get("instruction", "")),
                    "input": normalize_text(row.get("context", "")),
                    "output": normalize_text(row.get("response", "")),
                    "source": "dolly_15k",
                }
            )
        LOGGER.info("Loaded %d Dolly samples", len(examples))
        return examples

    def build_raw_splits(self, force_rebuild: bool = False) -> DatasetDict:
        if self.raw_split_dir.exists() and not force_rebuild:
            LOGGER.info("Loading cached raw split dataset from %s", self.raw_split_dir)
            return load_from_disk(str(self.raw_split_dir))

        all_rows: list[dict[str, str]] = []
        for loader in (self._load_oasst1, self._load_alpaca, self._load_dolly):
            try:
                all_rows.extend(loader())
            except Exception as exc:  # pragma: no cover - internet/runtime failures
                LOGGER.warning("Dataset loader failed: %s", exc)

        deduped_rows: list[dict[str, str]] = []
        seen_hashes: set[str] = set()
        for row in all_rows:
            if not self._is_valid(row):
                continue
            row_hash = self._hash_row(row)
            if row_hash in seen_hashes:
                continue
            seen_hashes.add(row_hash)
            deduped_rows.append(row)

        if not deduped_rows:
            raise RuntimeError("No training samples were created. Check dataset access and config.")

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

        max_len = self.config.model.max_seq_length

        def _tokenize_row(row: dict[str, Any]) -> dict[str, list[int]]:
            prompt = build_prompt(row["instruction"], row.get("input", ""))
            response = normalize_text(row["output"]) + tokenizer.eos_token
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
        report = {
            "train_samples": len(dataset_dict["train"]),
            "validation_samples": len(dataset_dict["validation"]),
            "test_samples": len(dataset_dict["test"]),
        }
        report_path = self.processed_root / "dataset_report.json"
        report_path.parent.mkdir(parents=True, exist_ok=True)
        report_path.write_text(json.dumps(report, indent=2), encoding="utf-8")

