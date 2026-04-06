"""
Medical Q&A - Inference Module

Provides:
  MedicalQAInference  – single class for loading model and answering questions
  Used by FastAPI deployment (deploy/app.py) and standalone scripts.

Usage:
  from src.inference import MedicalQAInference
  engine = MedicalQAInference("models/medical_qa_lora/final")
  print(engine.answer("What are symptoms of Type 2 diabetes?"))
"""
from __future__ import annotations

import logging
from functools import lru_cache
from typing import List, Optional

import torch
from peft import PeftModel
from transformers import AutoModelForCausalLM, AutoTokenizer, GenerationConfig

logger = logging.getLogger(__name__)


class MedicalQAInference:
    """
    Production-grade inference engine for Medical Q&A.

    Supports:
      - Standalone fine-tuned model (full weights saved)
      - LoRA adapter (base_model + adapter)
      - Batched generation
      - Configurable generation parameters
    """

    def __init__(
        self,
        model_path: str,
        base_model: Optional[str] = None,
        max_new_tokens: int = 512,
        temperature: float = 0.7,
        top_p: float = 0.9,
        repetition_penalty: float = 1.1,
        device: Optional[str] = None,
    ):
        self.model_path = model_path
        self.max_new_tokens = max_new_tokens
        self.device = device or ("cuda" if torch.cuda.is_available() else "cpu")

        logger.info(f"Initialising MedicalQAInference | device={self.device}")
        self._load_model(model_path, base_model)

        self.generation_config = GenerationConfig(
            max_new_tokens=max_new_tokens,
            temperature=temperature,
            top_p=top_p,
            repetition_penalty=repetition_penalty,
            do_sample=True,
            pad_token_id=self.tokenizer.pad_token_id,
            eos_token_id=self.tokenizer.eos_token_id,
        )

    def _load_model(self, model_path: str, base_model: Optional[str]) -> None:
        self.tokenizer = AutoTokenizer.from_pretrained(model_path, trust_remote_code=True)
        if self.tokenizer.pad_token is None:
            self.tokenizer.pad_token = self.tokenizer.eos_token

        dtype = torch.float16 if self.device == "cuda" else torch.float32
        dmap = "auto" if self.device == "cuda" else None

        if base_model:
            logger.info(f"Loading base model '{base_model}' + LoRA adapter '{model_path}'")
            base = AutoModelForCausalLM.from_pretrained(
                base_model, torch_dtype=dtype, device_map=dmap, trust_remote_code=True)
            self.model = PeftModel.from_pretrained(base, model_path)
        else:
            logger.info(f"Loading merged model from '{model_path}'")
            self.model = AutoModelForCausalLM.from_pretrained(
                model_path, torch_dtype=dtype, device_map=dmap, trust_remote_code=True)

        self.model.eval()
        logger.info("Model loaded and ready.")

    def _build_prompt(self, question: str, context: str = "") -> str:
        if context.strip():
            return (
                "Below is a medical question with additional context. "
                "Provide a clear, accurate, and helpful answer.\n\n"
                f"### Question:\n{question}\n\n"
                f"### Context:\n{context}\n\n"
                "### Response:\n"
            )
        return (
            "Below is a medical question. "
            "Provide a clear, accurate, and helpful answer.\n\n"
            f"### Question:\n{question}\n\n"
            "### Response:\n"
        )

    @torch.inference_mode()
    def answer(self, question: str, context: str = "") -> str:
        """Generate an answer for a single medical question."""
        prompt = self._build_prompt(question, context)
        inputs = self.tokenizer(
            prompt, return_tensors="pt", truncation=True, max_length=512
        ).to(self.device)

        output_ids = self.model.generate(**inputs, generation_config=self.generation_config)
        new_ids = output_ids[0][inputs["input_ids"].shape[1]:]
        return self.tokenizer.decode(new_ids, skip_special_tokens=True).strip()

    @torch.inference_mode()
    def answer_batch(self, questions: List[str], contexts: Optional[List[str]] = None) -> List[str]:
        """Generate answers for a batch of questions."""
        if contexts is None:
            contexts = [""] * len(questions)

        prompts = [self._build_prompt(q, c) for q, c in zip(questions, contexts)]
        inputs = self.tokenizer(
            prompts, return_tensors="pt", truncation=True,
            max_length=512, padding=True
        ).to(self.device)

        output_ids = self.model.generate(**inputs, generation_config=self.generation_config)
        results = []
        for i, ids in enumerate(output_ids):
            new_ids = ids[inputs["input_ids"].shape[1]:]
            results.append(self.tokenizer.decode(new_ids, skip_special_tokens=True).strip())
        return results


@lru_cache(maxsize=1)
def get_engine(model_path: str, base_model: Optional[str] = None) -> MedicalQAInference:
    """Singleton factory — safe for FastAPI startup."""
    return MedicalQAInference(model_path=model_path, base_model=base_model)


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--model_path", default="models/medical_qa_lora/final")
    parser.add_argument("--base_model", default=None)
    parser.add_argument("--question", default="What are the symptoms of hypertension?")
    args = parser.parse_args()

    engine = MedicalQAInference(args.model_path, args.base_model)
    print("\nAnswer:\n", engine.answer(args.question))
