"""Model and tokenizer setup for LoRA fine-tuning and inference."""

from __future__ import annotations

import logging
from typing import Any

import torch
from peft import LoraConfig, PeftModel, TaskType, get_peft_model, prepare_model_for_kbit_training
from transformers import AutoModelForCausalLM, AutoTokenizer, BitsAndBytesConfig

from .config import AppConfig

LOGGER = logging.getLogger(__name__)


def _torch_dtype(dtype_name: str) -> torch.dtype:
    lookup: dict[str, torch.dtype] = {
        "float16": torch.float16,
        "bfloat16": torch.bfloat16,
        "float32": torch.float32,
    }
    if dtype_name not in lookup:
        raise ValueError(f"Unsupported torch dtype: {dtype_name}")
    return lookup[dtype_name]


def load_tokenizer(config: AppConfig):
    tokenizer = AutoTokenizer.from_pretrained(config.model.base_model_name, use_fast=True)
    if tokenizer.pad_token is None:
        tokenizer.pad_token = tokenizer.eos_token
    tokenizer.padding_side = "right"
    return tokenizer


def _build_quantization_config(config: AppConfig) -> BitsAndBytesConfig | None:
    if not config.model.load_in_4bit:
        return None
    compute_dtype = _torch_dtype(config.model.torch_dtype)
    return BitsAndBytesConfig(
        load_in_4bit=True,
        bnb_4bit_use_double_quant=True,
        bnb_4bit_quant_type="nf4",
        bnb_4bit_compute_dtype=compute_dtype,
    )


def load_model_for_training(config: AppConfig):
    quantization_config = _build_quantization_config(config)
    kwargs: dict[str, Any] = {
        "trust_remote_code": True,
        "torch_dtype": _torch_dtype(config.model.torch_dtype),
    }
    if quantization_config is not None:
        kwargs["quantization_config"] = quantization_config
        kwargs["device_map"] = "auto"

    model = AutoModelForCausalLM.from_pretrained(config.model.base_model_name, **kwargs)
    model.config.use_cache = False

    if config.training.gradient_checkpointing:
        model.gradient_checkpointing_enable(gradient_checkpointing_kwargs={"use_reentrant": False})

    if quantization_config is not None:
        model = prepare_model_for_kbit_training(model)

    lora_config = LoraConfig(
        r=config.model.lora_r,
        lora_alpha=config.model.lora_alpha,
        lora_dropout=config.model.lora_dropout,
        target_modules=config.model.target_modules,
        task_type=TaskType.CAUSAL_LM,
        bias="none",
    )
    model = get_peft_model(model, lora_config)
    model.print_trainable_parameters()
    return model


def load_model_for_inference(config: AppConfig, adapter_dir: str):
    quantization_config = _build_quantization_config(config)
    kwargs: dict[str, Any] = {
        "trust_remote_code": True,
        "torch_dtype": _torch_dtype(config.model.torch_dtype),
    }
    if quantization_config is not None:
        kwargs["quantization_config"] = quantization_config
        kwargs["device_map"] = "auto"

    base_model = AutoModelForCausalLM.from_pretrained(config.model.base_model_name, **kwargs)
    model = PeftModel.from_pretrained(base_model, adapter_dir)
    model.eval()
    return model

