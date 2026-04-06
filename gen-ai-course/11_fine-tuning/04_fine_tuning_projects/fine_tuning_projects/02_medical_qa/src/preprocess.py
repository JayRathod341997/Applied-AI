"""
Medical Q&A - Data Preprocessing Module

Handles:
1. Loading MedQuAD / ChatDoctor / MedAlpaca datasets from Hugging Face Hub
2. Cleaning: deduplication, length filters, text normalisation
3. Instruction-following format conversion
4. Tokenisation with label masking (prompt tokens = -100)
5. Train / val / test split and saving to disk

Dataset used (subset-friendly):
  Primary  : lavita/ChatDoctor-HealthCareMagic-100k
  Fallback : medalpaca/medical_meadow_medqa
"""

from __future__ import annotations

import hashlib
import logging
import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional

import pandas as pd
from datasets import Dataset, DatasetDict, load_dataset
from transformers import AutoTokenizer
from tqdm.auto import tqdm

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


# ── Configuration ─────────────────────────────────────────────────────────────

@dataclass
class PreprocessConfig:
    """All knobs for the preprocessing pipeline."""

    # Paths
    raw_data_dir: str = "data/raw"
    processed_dir: str = "data/processed"

    # Dataset
    dataset_name: str = "lavita/ChatDoctor-HealthCareMagic-100k"
    fallback_dataset: str = "medalpaca/medical_meadow_medqa"
    subset_size: Optional[int] = 5000    # None → full dataset
    cache_dir: Optional[str] = "data/raw"

    # Model / tokeniser
    model_name: str = "microsoft/BioGPT-Large"
    max_seq_length: int = 512

    # Splits
    train_split: float = 0.90
    val_split: float = 0.05
    test_split: float = 0.05
    seed: int = 42

    # Cleaning thresholds
    remove_duplicates: bool = True
    min_instruction_len: int = 10
    min_response_len: int = 20


# ── Helpers ───────────────────────────────────────────────────────────────────

def _sha256(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def _clean_text(text: str) -> str:
    if not isinstance(text, str):
        return ""
    return " ".join(text.strip().split())


def _format_instruction(instruction: str, context: str, response: str) -> Dict[str, str]:
    """
    Alpaca-style instruction template.

    Prompt ends at '### Response:\n' so label masking can ignore the prompt.
    """
    if context.strip():
        prompt = (
            "Below is a medical question with additional context. "
            "Provide a clear, accurate, and helpful answer.\n\n"
            f"### Question:\n{instruction}\n\n"
            f"### Context:\n{context}\n\n"
            "### Response:\n"
        )
    else:
        prompt = (
            "Below is a medical question. "
            "Provide a clear, accurate, and helpful answer.\n\n"
            f"### Question:\n{instruction}\n\n"
            "### Response:\n"
        )

    full_text = prompt + response + "\n"
    return {
        "instruction": instruction,
        "context": context,
        "response": response,
        "prompt": prompt,
        "text": full_text,
    }


# ── Loader ────────────────────────────────────────────────────────────────────

class MedicalDataLoader:
    """Load and normalise medical QA datasets into a common schema."""

    def __init__(self, config: PreprocessConfig):
        self.config = config

    def load(self) -> pd.DataFrame:
        """Try primary dataset, fall back gracefully."""
        df = self._try_load_primary()
        if df is None or len(df) == 0:
            df = self._try_load_fallback()
        if df is None or len(df) == 0:
            logger.warning("No real data available — using synthetic sample data.")
            df = self._synthetic_data()

        if self.config.subset_size and len(df) > self.config.subset_size:
            df = df.sample(n=self.config.subset_size, random_state=self.config.seed).reset_index(drop=True)
            logger.info(f"Subset to {self.config.subset_size} rows")

        logger.info(f"Loaded {len(df)} rows total")
        return df

    def _try_load_primary(self) -> Optional[pd.DataFrame]:
        try:
            logger.info(f"Loading primary dataset: {self.config.dataset_name}")
            ds = load_dataset(
                self.config.dataset_name,
                split="train",
                cache_dir=self.config.cache_dir,
                trust_remote_code=True,
            )
            df = ds.to_pandas()
            return self._normalise_chatdoctor(df)
        except Exception as exc:
            logger.warning(f"Primary dataset failed: {exc}")
            return None

    def _try_load_fallback(self) -> Optional[pd.DataFrame]:
        try:
            logger.info(f"Loading fallback dataset: {self.config.fallback_dataset}")
            ds = load_dataset(
                self.config.fallback_dataset,
                split="train",
                cache_dir=self.config.cache_dir,
                trust_remote_code=True,
            )
            df = ds.to_pandas()
            return self._normalise_medalpaca(df)
        except Exception as exc:
            logger.warning(f"Fallback dataset failed: {exc}")
            return None

    # ── Column normalisers ────────────────────────────────────────────────────

    @staticmethod
    def _normalise_chatdoctor(df: pd.DataFrame) -> pd.DataFrame:
        """ChatDoctor schema: input / output (or instruction / output)."""
        col_map: Dict[str, str] = {}
        if "input" in df.columns:
            col_map["input"] = "instruction"
        if "output" in df.columns:
            col_map["output"] = "response"
        if "instruction" in df.columns and "instruction" not in col_map.values():
            col_map["instruction"] = "instruction"
        df = df.rename(columns=col_map)
        df["context"] = df.get("context", pd.Series([""] * len(df))).fillna("")
        return df[["instruction", "context", "response"]].copy()

    @staticmethod
    def _normalise_medalpaca(df: pd.DataFrame) -> pd.DataFrame:
        """MedAlpaca schema: instruction / input / output."""
        df = df.rename(columns={"input": "context", "output": "response"}, errors="ignore")
        if "instruction" not in df.columns:
            df["instruction"] = df.get("question", "").fillna("")
        df["context"] = df.get("context", "").fillna("")
        df["response"] = df.get("response", df.get("answer", "")).fillna("")
        return df[["instruction", "context", "response"]].copy()

    @staticmethod
    def _synthetic_data() -> pd.DataFrame:
        """Minimal synthetic records so the pipeline can be tested end-to-end."""
        rows = [
            ("What are the common symptoms of Type 2 diabetes?", "",
             "Common symptoms of Type 2 diabetes include increased thirst (polydipsia), frequent urination (polyuria), fatigue, blurred vision, slow-healing sores, and frequent infections. Some people also experience tingling or numbness in the hands or feet."),
            ("What is hypertension and how is it treated?", "",
             "Hypertension (high blood pressure) is a chronic condition where blood pressure in the arteries is persistently elevated (≥130/80 mmHg). Treatment combines lifestyle changes (reduced sodium intake, regular exercise, weight loss) and medications such as ACE inhibitors, ARBs, calcium channel blockers, or diuretics."),
            ("Explain the mechanism of action of metformin.", "",
             "Metformin primarily reduces hepatic glucose production by activating AMP-activated protein kinase (AMPK), which inhibits gluconeogenesis. It also improves insulin sensitivity in peripheral tissues and slightly reduces intestinal glucose absorption, resulting in lower fasting blood glucose levels."),
            ("What are the first-line antibiotics for community-acquired pneumonia?", "",
             "For non-severe community-acquired pneumonia in otherwise healthy adults, amoxicillin (or doxycycline as an alternative) is first-line. Macrolides such as azithromycin are used when atypical pathogens are suspected. Fluoroquinolones are reserved for patients with comorbidities or when beta-lactams are contraindicated."),
            ("Describe the pathophysiology of myocardial infarction.", "",
             "Myocardial infarction (MI) occurs when a coronary artery is blocked, most commonly by rupture of an atherosclerotic plaque followed by thrombus formation. The resulting ischaemia leads to irreversible cardiomyocyte necrosis within minutes to hours, releasing biomarkers (troponin, CK-MB) into the bloodstream."),
        ]
        return pd.DataFrame(rows, columns=["instruction", "context", "response"])


# ── Cleaner ───────────────────────────────────────────────────────────────────

class DataCleaner:
    """Deduplication, length filters, and text normalisation."""

    def __init__(self, config: PreprocessConfig):
        self.config = config

    def clean(self, df: pd.DataFrame) -> pd.DataFrame:
        df = self._normalise_columns(df)
        df = self._length_filter(df)
        if self.config.remove_duplicates:
            df = self._deduplicate(df)
        logger.info(f"After cleaning: {len(df)} rows remain")
        return df.reset_index(drop=True)

    @staticmethod
    def _normalise_columns(df: pd.DataFrame) -> pd.DataFrame:
        df["instruction"] = df["instruction"].apply(_clean_text)
        df["context"] = df["context"].apply(_clean_text)
        df["response"] = df["response"].apply(_clean_text)
        return df

    def _length_filter(self, df: pd.DataFrame) -> pd.DataFrame:
        before = len(df)
        mask = (
            df["instruction"].str.len().ge(self.config.min_instruction_len)
            & df["response"].str.len().ge(self.config.min_response_len)
        )
        df = df[mask]
        logger.info(f"Length filter removed {before - len(df)} rows")
        return df

    @staticmethod
    def _deduplicate(df: pd.DataFrame) -> pd.DataFrame:
        before = len(df)
        df["_hash"] = df.apply(
            lambda r: _sha256(r["instruction"] + r["context"] + r["response"]),
            axis=1,
        )
        df = df.drop_duplicates(subset=["_hash"]).drop(columns=["_hash"])
        logger.info(f"Deduplication removed {before - len(df)} rows")
        return df


# ── Formatter ─────────────────────────────────────────────────────────────────

class InstructionFormatter:
    """Convert cleaned DataFrame → HuggingFace Dataset with instruction format."""

    def format(self, df: pd.DataFrame) -> Dataset:
        logger.info("Formatting into instruction-following template …")
        records: List[Dict[str, str]] = []
        for _, row in tqdm(df.iterrows(), total=len(df), desc="Formatting"):
            records.append(
                _format_instruction(row["instruction"], row["context"], row["response"])
            )
        return Dataset.from_list(records)


# ── Tokeniser ─────────────────────────────────────────────────────────────────

class MedicalTokenizer:
    """Wrap AutoTokenizer with label-masking for causal LM training."""

    def __init__(self, config: PreprocessConfig):
        self.config = config
        self.tokenizer = self._load_tokenizer()

    def _load_tokenizer(self) -> AutoTokenizer:
        logger.info(f"Loading tokenizer: {self.config.model_name}")
        tok = AutoTokenizer.from_pretrained(
            self.config.model_name,
            trust_remote_code=True,
        )
        if tok.pad_token is None:
            tok.pad_token = tok.eos_token
        return tok

    def tokenize_dataset(self, dataset: Dataset) -> Dataset:
        logger.info("Tokenising dataset …")
        return dataset.map(
            self._tokenize_fn,
            batched=True,
            remove_columns=dataset.column_names,
            desc="Tokenising",
        )

    def _tokenize_fn(self, batch: Dict[str, List]) -> Dict[str, List]:
        full_texts = batch["text"]
        prompts = batch["prompt"]

        enc = self.tokenizer(
            full_texts,
            truncation=True,
            max_length=self.config.max_seq_length,
            padding="max_length",
        )

        labels = []
        for ids, prompt in zip(enc["input_ids"], prompts):
            # Find how many tokens the prompt occupies
            prompt_ids = self.tokenizer(
                prompt,
                truncation=True,
                max_length=self.config.max_seq_length,
                add_special_tokens=False,
            )["input_ids"]
            prompt_len = len(prompt_ids)

            lbl = list(ids)
            # Mask prompt tokens so loss is only computed on the response
            for i in range(min(prompt_len, len(lbl))):
                lbl[i] = -100
            # Mask padding tokens
            pad_id = self.tokenizer.pad_token_id
            lbl = [-100 if tok_id == pad_id and i >= prompt_len else lbl[i]
                   for i, tok_id in enumerate(ids)]
            labels.append(lbl)

        enc["labels"] = labels
        return enc


# ── Pipeline ──────────────────────────────────────────────────────────────────

class MedicalPreprocessPipeline:
    """Orchestrate the full preprocessing pipeline."""

    def __init__(self, config: PreprocessConfig):
        self.config = config
        self.loader = MedicalDataLoader(config)
        self.cleaner = DataCleaner(config)
        self.formatter = InstructionFormatter()
        self.tokenizer = MedicalTokenizer(config)

    def run(self) -> DatasetDict:
        """Execute the full pipeline and return train / val / test splits."""
        # 1. Load
        df = self.loader.load()

        # 2. Clean
        df = self.cleaner.clean(df)

        # 3. Format
        dataset = self.formatter.format(df)

        # 4. Split  (train | val | test)
        assert abs(self.config.train_split + self.config.val_split + self.config.test_split - 1.0) < 1e-6, \
            "Split fractions must sum to 1.0"

        val_test_ratio = self.config.val_split + self.config.test_split
        val_ratio_of_remainder = self.config.val_split / val_test_ratio

        train_val_test = dataset.train_test_split(
            test_size=val_test_ratio, seed=self.config.seed
        )
        val_test = train_val_test["test"].train_test_split(
            test_size=1 - val_ratio_of_remainder, seed=self.config.seed
        )

        split_dataset = DatasetDict({
            "train": train_val_test["train"],
            "validation": val_test["train"],
            "test": val_test["test"],
        })

        logger.info(
            f"Splits — train: {len(split_dataset['train'])}, "
            f"val: {len(split_dataset['validation'])}, "
            f"test: {len(split_dataset['test'])}"
        )

        # 5. Tokenise
        tokenised = DatasetDict({
            split: self.tokenizer.tokenize_dataset(ds)
            for split, ds in split_dataset.items()
        })

        # 6. Save
        out_path = Path(self.config.processed_dir)
        out_path.mkdir(parents=True, exist_ok=True)
        tokenised.save_to_disk(str(out_path))
        logger.info(f"Saved tokenised dataset → {out_path}")

        # Also save raw formatted (for evaluation / inspection)
        split_dataset.save_to_disk(str(out_path / "formatted"))
        return tokenised


# ── CLI entry-point ───────────────────────────────────────────────────────────

def main() -> None:
    config = PreprocessConfig(
        raw_data_dir="data/raw",
        processed_dir="data/processed",
        model_name="microsoft/BioGPT-Large",
        subset_size=5000,
        max_seq_length=512,
        seed=42,
    )
    pipeline = MedicalPreprocessPipeline(config)
    splits = pipeline.run()
    logger.info("Preprocessing complete.")
    logger.info(f"  train      : {len(splits['train'])} samples")
    logger.info(f"  validation : {len(splits['validation'])} samples")
    logger.info(f"  test       : {len(splits['test'])} samples")


if __name__ == "__main__":
    main()
