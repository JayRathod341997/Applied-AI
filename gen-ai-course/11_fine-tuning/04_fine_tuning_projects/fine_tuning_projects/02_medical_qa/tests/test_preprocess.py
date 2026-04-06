"""
Unit tests for src/preprocess.py

Run:
  cd fine_tuning_projects/02_medical_qa
  pytest tests/test_preprocess.py -v
"""
import sys
from pathlib import Path
import pytest
import pandas as pd

# Make src importable
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.preprocess import (
    PreprocessConfig,
    MedicalDataLoader,
    DataCleaner,
    InstructionFormatter,
    _clean_text,
    _sha256,
    _format_instruction,
)


# ── Helpers ───────────────────────────────────────────────────────────────────

def _make_df(rows=5) -> pd.DataFrame:
    return pd.DataFrame({
        "instruction": [f"What is condition {i}?" for i in range(rows)],
        "context": [""] * rows,
        "response": [f"Condition {i} causes symptom X and Y." for i in range(rows)],
    })


# ── _clean_text ───────────────────────────────────────────────────────────────

def test_clean_text_strips_whitespace():
    assert _clean_text("  hello  world  ") == "hello world"

def test_clean_text_non_string():
    assert _clean_text(None) == ""
    assert _clean_text(123) == ""

def test_clean_text_empty():
    assert _clean_text("") == ""


# ── _sha256 ───────────────────────────────────────────────────────────────────

def test_sha256_deterministic():
    assert _sha256("hello") == _sha256("hello")

def test_sha256_different_inputs():
    assert _sha256("hello") != _sha256("world")


# ── _format_instruction ───────────────────────────────────────────────────────

def test_format_instruction_no_context():
    result = _format_instruction("Q?", "", "Answer.")
    assert "### Question:\nQ?" in result["text"]
    assert "### Response:\nAnswer." in result["text"]
    assert "### Context:" not in result["text"]

def test_format_instruction_with_context():
    result = _format_instruction("Q?", "ctx", "Answer.")
    assert "### Context:\nctx" in result["text"]

def test_format_instruction_keys():
    result = _format_instruction("Q?", "", "A.")
    assert all(k in result for k in ("instruction", "context", "response", "prompt", "text"))

def test_format_instruction_prompt_ends_before_response():
    result = _format_instruction("Q?", "", "My answer here.")
    assert result["prompt"].endswith("### Response:\n")
    assert "My answer here." not in result["prompt"]


# ── DataCleaner ───────────────────────────────────────────────────────────────

class TestDataCleaner:
    def setup_method(self):
        self.cfg = PreprocessConfig(
            min_instruction_len=5,
            min_response_len=10,
            remove_duplicates=True,
        )
        self.cleaner = DataCleaner(self.cfg)

    def test_removes_short_instructions(self):
        df = pd.DataFrame({
            "instruction": ["Hi", "What is hypertension?"],
            "context": ["", ""],
            "response": ["Short but ok response.", "Hypertension is high blood pressure."],
        })
        cleaned = self.cleaner.clean(df)
        assert len(cleaned) == 1
        assert "hypertension" in cleaned.iloc[0]["instruction"].lower()

    def test_removes_short_responses(self):
        df = pd.DataFrame({
            "instruction": ["What is diabetes?", "What is flu?"],
            "context": ["", ""],
            "response": ["Too short.", "Flu is a viral respiratory illness caused by influenza."],
        })
        cleaned = self.cleaner.clean(df)
        assert len(cleaned) == 1

    def test_removes_duplicates(self):
        df = _make_df(3)
        df = pd.concat([df, df], ignore_index=True)
        cleaned = self.cleaner.clean(df)
        assert len(cleaned) == 3

    def test_no_duplicates_flag(self):
        cfg = PreprocessConfig(remove_duplicates=False)
        cleaner = DataCleaner(cfg)
        df = _make_df(2)
        df = pd.concat([df, df], ignore_index=True)
        cleaned = cleaner.clean(df)
        assert len(cleaned) == 4

    def test_normalises_whitespace(self):
        df = pd.DataFrame({
            "instruction": ["  What   is fever?  "],
            "context": [""],
            "response": ["Fever is   elevated   body temperature."],
        })
        cleaned = self.cleaner.clean(df)
        assert "  " not in cleaned.iloc[0]["instruction"]
        assert "  " not in cleaned.iloc[0]["response"]


# ── InstructionFormatter ──────────────────────────────────────────────────────

class TestInstructionFormatter:
    def setup_method(self):
        self.formatter = InstructionFormatter()

    def test_output_is_dataset(self):
        from datasets import Dataset
        df = _make_df(3)
        ds = self.formatter.format(df)
        assert isinstance(ds, Dataset)

    def test_all_required_columns_present(self):
        df = _make_df(3)
        ds = self.formatter.format(df)
        for col in ("instruction", "context", "response", "prompt", "text"):
            assert col in ds.column_names

    def test_row_count_preserved(self):
        df = _make_df(10)
        ds = self.formatter.format(df)
        assert len(ds) == 10


# ── MedicalDataLoader synthetic fallback ────────────────────────────────────

class TestMedicalDataLoaderSynthetic:
    def setup_method(self):
        cfg = PreprocessConfig(
            dataset_name="__nonexistent__/dataset",
            fallback_dataset="__nonexistent__/fallback",
            subset_size=None,
        )
        self.loader = MedicalDataLoader(cfg)

    def test_synthetic_fallback_has_required_columns(self):
        df = self.loader._synthetic_data()
        assert all(c in df.columns for c in ("instruction", "context", "response"))

    def test_synthetic_fallback_non_empty(self):
        df = self.loader._synthetic_data()
        assert len(df) > 0

    def test_subset_applied(self):
        cfg = PreprocessConfig(
            dataset_name="__nonexistent__",
            fallback_dataset="__nonexistent__",
            subset_size=3,
        )
        loader = MedicalDataLoader(cfg)
        df = loader.load()
        assert len(df) <= 3
