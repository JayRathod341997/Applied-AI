"""
Legal/Finance Corpus Data Preprocessing

Handles:
1. Loading custom corpus (PDF, DOCX, TXT)
2. spaCy-based NER for legal entities
3. Clause extraction and hierarchical numbering
4. Train/val/test split (80/10/10)
5. Domain-adaptive pretraining format

Environment: Python 3.10, PyTorch 2.4, spaCy 3.6
"""

import os
import re
import json
import hashlib
import logging
from dataclasses import dataclass, field
from typing import Optional, List, Dict, Any, Tuple
from pathlib import Path
from datetime import datetime

import pandas as pd
import numpy as np
from datasets import Dataset, DatasetDict, DatasetInfo, load_dataset
from transformers import AutoTokenizer

try:
    import spacy
    from spacy.tokens import Doc

    SPACY_AVAILABLE = True
except ImportError:
    SPACY_AVAILABLE = False
    logging.warning("spaCy not available, NER disabled")

try:
    import torch
except ImportError:
    torch = None

try:
    import fitz  # PyMuPDF

    PDF_AVAILABLE = True
except ImportError:
    PDF_AVAILABLE = False
    logging.warning("PyMuPDF not available, PDF parsing disabled")

try:
    from docx import Document

    DOCX_AVAILABLE = True
except ImportError:
    DOCX_AVAILABLE = False
    logging.warning("python-docx not available, DOCX parsing disabled")

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler("logs/preprocessing.log"),
        logging.StreamHandler(),
    ],
)
logger = logging.getLogger(__name__)


@dataclass
class CorpusConfig:
    """Configuration for legal-finance corpus preprocessing."""

    # Paths
    raw_data_dir: str = "data/raw"
    processed_dir: str = "data/processed"
    output_dir: str = "experiments"

    # Model
    base_model: str = "microsoft/finbert-tone"
    max_seq_length: int = 512

    # spaCy model
    spacy_model: str = "en_core_web_trf"

    # Dataset splits
    train_ratio: float = 0.80
    val_ratio: float = 0.10
    test_ratio: float = 0.10

    # Seed
    seed: int = 42

    # Custom entities for legal/finance
    legal_entities: List[str] = field(
        default_factory=lambda: [
            "LEGAL_REGULATION",
            "LAW",
            "COURT_CASE",
            "STATUTE",
            "COMPANY",
            "ORGANIZATION",
            "MONEY",
            "DATE",
            "PERCENTAGE",
            "CONTRACT_CLAUSE",
            "SECTION_NUMBER",
            "ARTICLE",
        ]
    )

    # Cleaning
    min_document_length: int = 100
    max_document_length: int = 50000
    remove_duplicates: bool = True


class PDFParser:
    """Parse PDF documents and extract text with structure."""

    def __init__(self):
        if not PDF_AVAILABLE:
            raise ImportError("PyMuPDF required for PDF parsing")
        self.document = None

    def load(self, filepath: str) -> str:
        """Load and parse PDF file."""
        doc = fitz.open(filepath)
        text_parts = []

        for page_num, page in enumerate(doc):
            text = page.get_text()
            text_parts.append(text)

        doc.close()
        return "\n\n".join(text_parts)

    def extract_clauses(self, text: str) -> List[Dict[str, Any]]:
        """Extract numbered clauses and sections."""
        clauses = []

        clause_patterns = [
            r"(\d+\.\d+(?:\.\d+)*)\s+([A-Z][^.]{10,})",
            r"(Article\s+\d+)\s+([A-Z][^.]{10,})",
            r"(Section\s+\d+)\s+([A-Z][^.]{10,})",
            r"(\([a-z]\))\s+([A-Z][^.]{10,})",
        ]

        for pattern in clause_patterns:
            matches = re.finditer(pattern, text, re.MULTILINE)
            for match in matches:
                clauses.append(
                    {
                        "number": match.group(1),
                        "heading": match.group(2).strip(),
                        "text": match.group(0),
                    }
                )

        return clauses


class DOCXParser:
    """Parse DOCX documents and extract text."""

    def __init__(self):
        if not DOCX_AVAILABLE:
            raise ImportError("python-docx required for DOCX parsing")

    def load(self, filepath: str) -> str:
        """Load and parse DOCX file."""
        doc = Document(filepath)
        text_parts = []

        for para in doc.paragraphs:
            if para.text.strip():
                text_parts.append(para.text)

        return "\n\n".join(text_parts)


class LegalFinanceNER:
    """Named Entity Recognition for legal-finance documents."""

    def __init__(self, model_name: str = "en_core_web_trf"):
        self.model_name = model_name
        self.nlp = None

        if SPACY_AVAILABLE:
            try:
                self.nlp = spacy.load(model_name)
            except OSError:
                logger.warning(f"spaCy model {model_name} not found. Downloading...")
                import subprocess

                subprocess.run(["python", "-m", "spacy", "download", model_name])
                self.nlp = spacy.load(model_name)

    def extract_entities(self, text: str) -> List[Dict[str, Any]]:
        """Extract named entities from text."""
        if self.nlp is None:
            return self._regex_extract_entities(text)

        doc = self.nlp(text[:100000])  # Limit for performance

        entities = []
        for ent in doc.ents:
            entity_type = self._map_entity_label(ent.label_)
            if entity_type:
                entities.append(
                    {
                        "text": ent.text,
                        "type": entity_type,
                        "start": ent.start_char,
                        "end": ent.end_char,
                    }
                )

        return entities

    def _map_entity_label(self, label: str) -> Optional[str]:
        """Map spaCy labels to custom legal/finance labels."""
        mapping = {
            "ORG": "COMPANY",
            "GPE": "ORGANIZATION",
            "DATE": "DATE",
            "MONEY": "MONEY",
            "PERCENT": "PERCENTAGE",
            "LAW": "LEGAL_REGULATION",
            "NORP": "LAW",
            "FAC": "COURT_CASE",
            "WORK_OF_ART": "STATUTE",
        }
        return mapping.get(label)

    def _regex_extract_entities(self, text: str) -> List[Dict[str, Any]]:
        """Fallback regex-based entity extraction."""
        entities = []

        # Extract money amounts
        money_pattern = r"\$\d+(?:,\d{3})*(?:\.\d{2})?"
        for match in re.finditer(money_pattern, text):
            entities.append(
                {
                    "text": match.group(),
                    "type": "MONEY",
                    "start": match.start(),
                    "end": match.end(),
                }
            )

        # Extract dates
        date_pattern = r"\b\d{1,2}[/-]\d{1,2}[/-]\d{2,4}\b"
        for match in re.finditer(date_pattern, text):
            entities.append(
                {
                    "text": match.group(),
                    "type": "DATE",
                    "start": match.start(),
                    "end": match.end(),
                }
            )

        # Extract percentages
        pct_pattern = r"\d+(?:\.\d+)?%"
        for match in re.finditer(pct_pattern, text):
            entities.append(
                {
                    "text": match.group(),
                    "type": "PERCENTAGE",
                    "start": match.start(),
                    "end": match.end(),
                }
            )

        # Extract regulations (common patterns)
        reg_patterns = [
            r"\bSEC\s+(?:Rule\s+)?\d+[A-Z]*\b",
            r"\bDodd[-\s]?Frank\b",
            r"\bGDPR\b",
            r"\bBasel\s+(?:I|II|III)\b",
            r"\bSOX\b",
            r"\bHIPAA\b",
        ]

        for pattern in reg_patterns:
            for match in re.finditer(pattern, text, re.IGNORECASE):
                entities.append(
                    {
                        "text": match.group(),
                        "type": "LEGAL_REGULATION",
                        "start": match.start(),
                        "end": match.end(),
                    }
                )

        return entities


class DocumentProcessor:
    """Process and structure legal-finance documents."""

    def __init__(self, config: CorpusConfig):
        self.config = config
        self.ner = LegalFinanceNER(config.spacy_model)

    def process_file(self, filepath: str) -> Optional[Dict[str, Any]]:
        """Process a single document."""
        extension = Path(filepath).suffix.lower()

        try:
            if extension == ".pdf":
                parser = PDFParser()
                text = parser.load(filepath)
            elif extension == ".docx":
                parser = DOCXParser()
                text = parser.load(filepath)
            elif extension == ".txt":
                with open(filepath, "r", encoding="utf-8") as f:
                    text = f.read()
            else:
                logger.warning(f"Unsupported file type: {extension}")
                return None

            # Basic cleaning
            text = self._clean_text(text)

            # Skip if too short
            if len(text) < self.config.min_document_length:
                logger.warning(f"Document too short: {filepath}")
                return None

            # Extract entities
            entities = self.ner.extract_entities(text)

            # Extract clauses
            if extension == ".pdf":
                parser = PDFParser()
                clauses = parser.extract_clauses(text)
            else:
                clauses = []

            return {
                "filepath": str(filepath),
                "text": text[: self.config.max_document_length],
                "entities": entities,
                "clauses": clauses,
                "num_tokens": len(text.split()),
                "processed_at": datetime.now().isoformat(),
            }

        except Exception as e:
            logger.error(f"Error processing {filepath}: {e}")
            return None

    def _clean_text(self, text: str) -> str:
        """Clean and normalize text."""
        # Remove excessive whitespace
        text = re.sub(r"\s+", " ", text)

        # Remove page numbers
        text = re.sub(r"\n\d+\n", "\n", text)

        # Normalize quotes
        text = text.replace('"', '"').replace('"', '"')
        text = text.replace(""", "'").replace(""", "'")

        return text.strip()


class CorpusPreprocessor:
    """Main preprocessing pipeline for legal-finance corpus."""

    def __init__(self, config: CorpusConfig):
        self.config = config
        self.doc_processor = DocumentProcessor(config)
        self.tokenizer = None

    def load_corpus(self) -> List[Dict[str, Any]]:
        """Load all documents from raw data directory."""
        logger.info(f"Loading corpus from {self.config.raw_data_dir}")

        raw_path = Path(self.config.raw_data_dir)
        documents = []

        if not raw_path.exists():
            logger.warning(f"Raw data directory not found: {self.config.raw_data_dir}")
            logger.info("Creating sample corpus data...")
            return self._create_sample_corpus()

        # Find all supported files
        extensions = ["*.pdf", "*.docx", "*.txt"]
        for ext in extensions:
            for filepath in raw_path.rglob(ext):
                doc = self.doc_processor.process_file(str(filepath))
                if doc:
                    documents.append(doc)

        logger.info(f"Loaded {len(documents)} documents")
        return documents

    def _create_sample_corpus(self) -> List[Dict[str, Any]]:
        """Create sample legal-finance documents for testing."""
        sample_docs = [
            {
                "text": """SEC Rule 10b-5 is a rule promulgated by the Securities and Exchange Commission under the Securities Exchange Act of 1934. 
This rule prohibits fraud in connection with the purchase or sale of securities. The rule makes it unlawful for any person to 
employ any device, scheme, or artifice to defraud, to make any untrue statement of a material fact, or to omit to state a material 
fact necessary in order to make the statements made, in light of the circumstances under which they are made, not misleading.

The Dodd-Frank Wall Street Reform and Consumer Protection Act, enacted in 2010, significantly amended the securities laws. 
Section 954 of Dodd-Frank established the whistleblower program, which provides monetary awards to individuals who provide 
original information about securities violations that lead to successful enforcement actions resulting in penalties exceeding $1 million.""",
                "entities": [
                    {"text": "SEC Rule 10b-5", "type": "LEGAL_REGULATION"},
                    {"text": "Securities Exchange Act of 1934", "type": "STATUTE"},
                    {"text": "Dodd-Frank", "type": "LEGAL_REGULATION"},
                    {"text": "2010", "type": "DATE"},
                    {"text": "$1 million", "type": "MONEY"},
                ],
            },
            {
                "text": """Article I of the United States Constitution establishes the legislative branch of the federal government, 
the United States Congress. Section 1 of Article I creates the Congress and establishes the bicameral legislature 
consisting of the House of Representatives and the Senate.

Section 8 of Article I enumerates the powers of Congress, including the power to levy taxes, regulate commerce, 
declare war, and raise and support armies. These enumerated powers define the boundaries of federal legislative authority.""",
                "entities": [
                    {"text": "Article I", "type": "LEGAL_REGULATION"},
                    {"text": "United States Constitution", "type": "STATUTE"},
                    {"text": "Congress", "type": "ORGANIZATION"},
                    {"text": "Section 8", "type": "SECTION_NUMBER"},
                ],
            },
            {
                "text": """BASEL III is an internationally agreed set of measures developed by the Basel Committee on Banking Supervision. 
The framework was introduced in response to the financial crisis of 2007-2009 and includes requirements for bank capital, 
leverage ratios, and liquidity requirements.

Under BASEL III, banks must maintain a Common Equity Tier 1 (CET1) ratio of at least 4.5% of risk-weighted assets. 
Additionally, a capital conservation buffer of 2.5% is required, bringing the total minimum requirement to 7%.""",
                "entities": [
                    {"text": "BASEL III", "type": "LEGAL_REGULATION"},
                    {
                        "text": "Basel Committee on Banking Supervision",
                        "type": "ORGANIZATION",
                    },
                    {"text": "2007-2009", "type": "DATE"},
                    {"text": "4.5%", "type": "PERCENTAGE"},
                    {"text": "2.5%", "type": "PERCENTAGE"},
                    {"text": "7%", "type": "PERCENTAGE"},
                ],
            },
        ]

        for doc in sample_docs:
            doc["filepath"] = "sample"
            doc["clauses"] = []
            doc["num_tokens"] = len(doc["text"].split())
            doc["processed_at"] = datetime.now().isoformat()

        return sample_docs

    def remove_duplicates(
        self, documents: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """Remove duplicate documents based on content hash."""
        if not self.config.remove_duplicates:
            return documents

        seen_hashes = set()
        unique_docs = []

        for doc in documents:
            doc_hash = hashlib.sha256(doc["text"].encode()).hexdigest()
            if doc_hash not in seen_hashes:
                seen_hashes.add(doc_hash)
                unique_docs.append(doc)

        logger.info(f"Removed {len(documents) - len(unique_docs)} duplicate documents")
        return unique_docs

    def format_for_pretraining(self, documents: List[Dict[str, Any]]) -> Dataset:
        """Format documents for domain-specific pretraining (MLM)."""
        logger.info("Formatting for domain-specific pretraining...")

        formatted = []
        for doc in documents:
            # Masked language modeling format
            formatted.append(
                {
                    "text": doc["text"],
                    "entities": json.dumps(doc["entities"]),
                    "document_id": doc.get("filepath", "unknown"),
                }
            )

        return Dataset.from_list(formatted)

    def format_for_sft(self, documents: List[Dict[str, Any]]) -> Dataset:
        """Format documents for supervised fine-tuning (summaries, Q&A)."""
        logger.info("Formatting for supervised fine-tuning...")

        formatted = []
        for doc in documents:
            # Extract or generate summary
            summary = self._extract_summary(doc)

            formatted.append(
                {
                    "instruction": f"Analyze the following legal document and provide a summary: {doc['text'][:500]}...",
                    "input": "",
                    "output": summary,
                    "text": self._format_instruction(
                        f"Analyze the following legal document and provide a summary.",
                        doc["text"][:1000],
                        summary,
                    ),
                }
            )

        return Dataset.from_list(formatted)

    def _extract_summary(self, doc: Dict[str, Any]) -> str:
        """Extract or generate document summary."""
        # Use entities and first paragraph as summary basis
        entities = doc.get("entities", [])
        reg_entities = [e for e in entities if e.get("type") == "LEGAL_REGULATION"]

        if reg_entities:
            regs = ", ".join([e["text"] for e in reg_entities[:3]])
            return f"This document references: {regs}. Key aspects include legal regulations and financial requirements."

        # Fallback: first 200 chars
        return doc["text"][:200] + "..."

    def _format_instruction(
        self, instruction: str, input_text: str, output: str
    ) -> str:
        """Format as instruction-following example."""
        return f"""Below is an instruction describing a task, paired with an input providing more context. Write a response that appropriately completes the request.

### Instruction:
{instruction}

### Input:
{input_text}

### Response:
{output}"""

    def split_dataset(self, dataset: Dataset) -> DatasetDict:
        """Split dataset into train/val/test."""
        assert (
            abs(
                self.config.train_ratio
                + self.config.val_ratio
                + self.config.test_ratio
                - 1.0
            )
            < 1e-6
        ), "Split ratios must sum to 1.0"

        train_val_ratio = self.config.val_ratio + self.config.test_ratio
        val_ratio_of_remainder = self.config.val_ratio / train_val_ratio

        train_val = dataset.train_test_split(
            test_size=train_val_ratio, seed=self.config.seed
        )

        val_test = train_val["test"].train_test_split(
            test_size=1 - val_ratio_of_remainder, seed=self.config.seed
        )

        splits = DatasetDict(
            {
                "train": train_val["train"],
                "validation": val_test["train"],
                "test": val_test["test"],
            }
        )

        logger.info(
            f"Splits: train={len(splits['train'])}, "
            f"validation={len(splits['validation'])}, "
            f"test={len(splits['test'])}"
        )

        return splits

    def save_outputs(self, documents: List[Dict[str, Any]], output_dir: str):
        """Save processed corpus."""
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)

        # Save full documents with entities
        with open(output_path / "corpus_with_entities.json", "w") as f:
            json.dump(documents, f, indent=2)

        # Save entity-only version
        entity_docs = []
        for doc in documents:
            entity_docs.append(
                {
                    "document_id": doc.get("filepath", "unknown"),
                    "entities": doc.get("entities", []),
                }
            )

        with open(output_path / "entities_only.json", "w") as f:
            json.dump(entity_docs, f, indent=2)

        logger.info(f"Saved processed corpus to {output_path}")

    def preprocess(
        self, output_format: str = "both"
    ) -> Tuple[DatasetDict, DatasetDict]:
        """Run full preprocessing pipeline."""
        logger.info("Starting corpus preprocessing...")

        # Load documents
        documents = self.load_corpus()

        # Remove duplicates
        documents = self.remove_duplicates(documents)

        logger.info(f"Final corpus size: {len(documents)} documents")

        # Save intermediate outputs
        self.save_outputs(documents, self.config.processed_dir)

        # Create datasets based on format
        if output_format in ["pretrain", "both"]:
            pretrain_ds = self.format_for_pretraining(documents)
            pretrain_splits = self.split_dataset(pretrain_ds)

        if output_format in ["sft", "both"]:
            sft_ds = self.format_for_sft(documents)
            sft_splits = self.split_dataset(sft_ds)

        # Save datasets
        if output_format == "pretrain":
            pretrain_splits.save_to_disk(
                Path(self.config.processed_dir) / "pretrain_dataset"
            )
            return pretrain_splits
        elif output_format == "sft":
            sft_splits.save_to_disk(Path(self.config.processed_dir) / "sft_dataset")
            return sft_splits
        else:
            pretrain_splits.save_to_disk(
                Path(self.config.processed_dir) / "pretrain_dataset"
            )
            sft_splits.save_to_disk(Path(self.config.processed_dir) / "sft_dataset")
            return pretrain_splits, sft_splits


def main():
    """Main execution."""
    config = CorpusConfig(
        raw_data_dir="data/raw",
        processed_dir="data/processed",
        output_dir="experiments",
        base_model="microsoft/finbert-tone",
        max_seq_length=512,
        seed=42,
    )

    preprocessor = CorpusPreprocessor(config)

    pretrain_ds, sft_ds = preprocessor.preprocess("both")

    logger.info("Preprocessing complete!")
    logger.info(f"Pretrain dataset: {len(pretrain_ds['train'])} train samples")
    logger.info(f"SFT dataset: {len(sft_ds['train'])} train samples")


if __name__ == "__main__":
    main()
