"""
Legal/Finance Inference Module

Provides functions for:
- generate_summary: Summarize legal/finance documents
- extract_entities: Extract structured entities from text

Environment: PyTorch 2.4, Transformers 4.46, FastAPI
"""

import os
import re
import json
import logging
from dataclasses import dataclass
from typing import List, Dict, Any, Optional

import torch
from transformers import (
    AutoModelForCausalLM,
    AutoTokenizer,
    GenerationConfig,
    pipeline,
)
from peft import PeftModel

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


@dataclass
class InferenceConfig:
    """Configuration for inference."""

    model_path: str = "experiments/fine_tuned_model"
    base_model: str = "microsoft/finbert-tone"
    max_length: int = 512
    max_new_tokens: int = 150
    temperature: float = 0.7
    top_p: float = 0.9
    top_k: int = 50
    num_beams: int = 4
    length_penalty: float = 1.2
    device: str = "cuda"


class LegalFinanceInference:
    """Inference wrapper for legal-finance model."""

    def __init__(self, config: InferenceConfig):
        self.config = config
        self.tokenizer = None
        self.model = None
        self._loaded = False

    def load(self):
        """Load model and tokenizer."""
        if self._loaded:
            return

        logger.info(f"Loading model from: {self.config.model_path}")

        # Load tokenizer
        self.tokenizer = AutoTokenizer.from_pretrained(
            self.config.base_model,
            trust_remote_code=True,
        )

        if self.tokenizer.pad_token is None:
            self.tokenizer.pad_token = self.tokenizer.eos_token

        # Load base model
        device = self.config.device if torch.cuda.is_available() else "cpu"

        base_model = AutoModelForCausalLM.from_pretrained(
            self.config.base_model,
            torch_dtype=torch.float16 if device == "cuda" else torch.float32,
            device_map="auto" if device == "cuda" else None,
            trust_remote_code=True,
        )

        # Load PEFT adapters if available
        if os.path.exists(self.config.model_path):
            try:
                self.model = PeftModel.from_pretrained(
                    base_model,
                    self.config.model_path,
                    is_trainable=False,
                )
                logger.info("Loaded PEFT adapters")
            except Exception as e:
                logger.warning(f"Could not load PEFT: {e}, using base model")
                self.model = base_model
        else:
            logger.warning(
                f"Model path not found: {self.config.model_path}, using base model"
            )
            self.model = base_model

        self.model.eval()
        self._loaded = True
        logger.info("Model loaded successfully")

    def generate_summary(
        self,
        document: str,
        max_length: int = None,
        max_new_tokens: int = None,
    ) -> str:
        """
        Generate a summary of a legal/finance document.

        Args:
            document: Raw document text
            max_length: Maximum input sequence length
            max_new_tokens: Maximum tokens to generate

        Returns:
            Generated summary text
        """
        if not self._loaded:
            self.load()

        max_length = max_length or self.config.max_length
        max_new_tokens = max_new_tokens or self.config.max_new_tokens

        # Truncate document if too long
        doc_tokens = self.tokenizer.encode(document)
        if len(doc_tokens) > max_length - max_new_tokens:
            document = self.tokenizer.decode(
                doc_tokens[: max_length - max_new_tokens], skip_special_tokens=True
            )

        # Format prompt
        prompt = self._format_summary_prompt(document)

        # Tokenize
        inputs = self.tokenizer(
            prompt,
            return_tensors="pt",
            truncation=True,
            max_length=max_length,
            padding=True,
        )

        if torch.cuda.is_available():
            inputs = {k: v.to(self.model.device) for k, v in inputs.items()}

        # Generate
        generation_config = GenerationConfig(
            max_new_tokens=max_new_tokens,
            temperature=self.config.temperature,
            top_p=self.config.top_p,
            top_k=self.config.top_k,
            num_beams=self.config.num_beams,
            length_penalty=self.config.length_penalty,
            do_sample=True,
            pad_token_id=self.tokenizer.pad_token_id,
            eos_token_id=self.tokenizer.eos_token_id,
            no_repeat_ngram_size=3,
        )

        with torch.no_grad():
            outputs = self.model.generate(
                **inputs,
                generation_config=generation_config,
            )

        # Extract generated text
        input_length = inputs["input_ids"].shape[1]
        generated_tokens = outputs[0][input_length:]

        summary = self.tokenizer.decode(
            generated_tokens, skip_special_tokens=True
        ).strip()

        return summary

    def _format_summary_prompt(self, document: str) -> str:
        """Format document for summarization."""
        # Truncate document for prompt
        doc_preview = document[:1500] + "..." if len(document) > 1500 else document

        prompt = f"""Below is a legal or financial document. Provide a concise, accurate summary that captures the key points, regulations, and obligations mentioned.

### Document:
{doc_preview}

### Summary:
"""
        return prompt

    def extract_entities(
        self,
        text: str,
        entity_types: Optional[List[str]] = None,
    ) -> List[Dict[str, Any]]:
        """
        Extract named entities from legal/finance text.

        Args:
            text: Input text
            entity_types: Optional list of specific entity types to extract

        Returns:
            List of extracted entities with type and position
        """
        if entity_types is None:
            entity_types = [
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

        entities = []

        # Extract money amounts
        if "MONEY" in entity_types:
            money_pattern = (
                r"\$\d+(?:,\d{3})*(?:\.\d{2})?(?:\s*(?:million|billion|trillion))?"
            )
            for match in re.finditer(money_pattern, text, re.IGNORECASE):
                entities.append(
                    {
                        "text": match.group(),
                        "type": "MONEY",
                        "start": match.start(),
                        "end": match.end(),
                    }
                )

        # Extract dates
        if "DATE" in entity_types:
            date_patterns = [
                r"\b\d{1,2}[/-]\d{1,2}[/-]\d{2,4}\b",
                r"\b(?:January|February|March|April|May|June|July|August|September|October|November|December)\s+\d{1,2},?\s+\d{4}\b",
                r"\b\d{4}\b",
            ]
            for pattern in date_patterns:
                for match in re.finditer(pattern, text):
                    entities.append(
                        {
                            "text": match.group(),
                            "type": "DATE",
                            "start": match.start(),
                            "end": match.end(),
                        }
                    )

        # Extract percentages
        if "PERCENTAGE" in entity_types:
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

        # Extract regulations
        if "LEGAL_REGULATION" in entity_types:
            reg_patterns = [
                (r"\bSEC\s+(?:Rule\s+)?\d+[A-Z]*\b", "SEC Rule"),
                (r"\bDodd[-\s]?Frank\b", "Dodd-Frank Act"),
                (r"\bGDPR\b", "GDPR"),
                (r"\bBasel\s+(?:I|II|III)\b", "Basel Accord"),
                (r"\bSOX\b", "Sarbanes-Oxley Act"),
                (r"\bHIPAA\b", "HIPAA"),
                (r"\bFINRA\s+\d+\b", "FINRA Rule"),
                (r"\bFCPA\b", "FCPA"),
                (r"\bAML\b", "Anti-Money Laundering"),
                (r"\bKYC\b", "Know Your Customer"),
            ]

            for pattern, label in reg_patterns:
                for match in re.finditer(pattern, text, re.IGNORECASE):
                    entities.append(
                        {
                            "text": match.group(),
                            "type": "LEGAL_REGULATION",
                            "label": label,
                            "start": match.start(),
                            "end": match.end(),
                        }
                    )

        # Extract sections/articles
        if "SECTION_NUMBER" in entity_types or "ARTICLE" in entity_types:
            section_patterns = [
                (r"(?:Section|Article|Rule|Exhibit)\s+\d+(?:\.\d+)*", "SECTION_NUMBER"),
                (r"\(\d+\)", "SECTION_NUMBER"),
            ]

            for pattern, etype in section_patterns:
                for match in re.finditer(pattern, text):
                    entities.append(
                        {
                            "text": match.group(),
                            "type": etype,
                            "start": match.start(),
                            "end": match.end(),
                        }
                    )

        # Extract companies/organizations
        if "COMPANY" in entity_types or "ORGANIZATION" in entity_types:
            # Common legal entity suffixes
            org_pattern = r"\b[A-Z][A-Za-z0-9]*(?:\s+[A-Z][A-Za-z0-9]+)*(?:Inc\.|LLC|Corp\.|Ltd\.|Co\.|PLC|SA|NV|AG)\b"
            for match in re.finditer(org_pattern, text):
                entities.append(
                    {
                        "text": match.group(),
                        "type": "COMPANY",
                        "start": match.start(),
                        "end": match.end(),
                    }
                )

        # Deduplicate by position
        seen_positions = set()
        unique_entities = []
        for ent in entities:
            pos = (ent["start"], ent["end"])
            if pos not in seen_positions:
                seen_positions.add(pos)
                unique_entities.append(ent)

        return unique_entities

    def extract_structured_data(self, text: str) -> Dict[str, Any]:
        """Extract all structured data from document."""
        entities = self.extract_entities(text)

        # Group by type
        structured = {
            "regulations": [],
            "monetary_amounts": [],
            "dates": [],
            "percentages": [],
            "organizations": [],
            "clauses": [],
        }

        for ent in entities:
            if ent["type"] == "LEGAL_REGULATION":
                structured["regulations"].append(
                    {
                        "text": ent["text"],
                        "label": ent.get("label", ent["text"]),
                    }
                )
            elif ent["type"] == "MONEY":
                structured["monetary_amounts"].append(ent["text"])
            elif ent["type"] == "DATE":
                structured["dates"].append(ent["text"])
            elif ent["type"] == "PERCENTAGE":
                structured["percentages"].append(ent["text"])
            elif ent["type"] in ["COMPANY", "ORGANIZATION"]:
                structured["organizations"].append(ent["text"])
            elif ent["type"] in ["SECTION_NUMBER", "ARTICLE"]:
                structured["clauses"].append(ent["text"])

        return structured

    def answer_question(
        self,
        question: str,
        context: str = None,
    ) -> str:
        """Answer a question about the document."""
        if not self._loaded:
            self.load()

        if context:
            prompt = f"""Based on the following context, answer the question.

### Context:
{context[:2000]}

### Question:
{question}

### Answer:
"""
        else:
            prompt = f"""Answer the following legal/finance question.

### Question:
{question}

### Answer:
"""

        inputs = self.tokenizer(
            prompt,
            return_tensors="pt",
            truncation=True,
            max_length=self.config.max_length,
        )

        if torch.cuda.is_available():
            inputs = {k: v.to(self.model.device) for k, v in inputs.items()}

        generation_config = GenerationConfig(
            max_new_tokens=self.config.max_new_tokens,
            temperature=self.config.temperature,
            top_p=self.config.top_p,
            do_sample=True,
            pad_token_id=self.tokenizer.pad_token_id,
        )

        with torch.no_grad():
            outputs = self.model.generate(
                **inputs,
                generation_config=generation_config,
            )

        input_length = inputs["input_ids"].shape[1]
        generated_tokens = outputs[0][input_length:]

        answer = self.tokenizer.decode(
            generated_tokens, skip_special_tokens=True
        ).strip()

        return answer


# Convenience functions
def generate_summary(
    document: str,
    model_path: str = "experiments/fine_tuned_model",
    max_new_tokens: int = 150,
) -> str:
    """Generate summary for a document."""
    config = InferenceConfig(model_path=model_path, max_new_tokens=max_new_tokens)
    inference = LegalFinanceInference(config)
    return inference.generate_summary(document)


def extract_entities(
    text: str,
    model_path: str = "experiments/fine_tuned_model",
) -> List[Dict[str, Any]]:
    """Extract entities from text."""
    config = InferenceConfig(model_path=model_path)
    inference = LegalFinanceInference(config)
    return inference.extract_entities(text)


if __name__ == "__main__":
    # Test inference
    config = InferenceConfig()
    inference = LegalFinanceInference(config)
    inference.load()

    test_doc = """SEC Rule 10b-5 is a rule promulgated by the Securities and Exchange Commission 
under the Securities Exchange Act of 1934. This rule prohibits fraud in connection with the 
purchase or sale of securities. The Dodd-Frank Act of 2010 significantly amended these provisions."""

    print("=== Test Document ===")
    print(test_doc[:500])
    print()

    print("=== Generated Summary ===")
    summary = inference.generate_summary(test_doc, max_new_tokens=100)
    print(summary)
    print()

    print("=== Extracted Entities ===")
    entities = inference.extract_entities(test_doc)
    for ent in entities:
        print(f"  {ent['type']}: {ent['text']}")
