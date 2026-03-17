"""
Comprehensive Fine-tuning Implementation Exercise

This exercise implements a complete fine-tuning pipeline that works
across different platforms: Unsloth, HuggingFace, Azure ML, AWS SageMaker, and GCP Vertex AI.
"""

# Required packages:
# pip install transformers datasets peft accelerate bitsandbytes torch azure-ai-ml sagemaker google-cloud-aiplatform


import os
import json
from typing import Dict, Any, Optional, List
from dataclasses import dataclass, field


# ============================================================
# Configuration Classes
# ============================================================


@dataclass
class ModelConfig:
    """Configuration for the base model."""

    model_name: str = "meta-llama/Meta-Llama-3-8B-Instruct"
    max_seq_length: int = 2048
    load_in_4bit: bool = True
    dtype: Optional[str] = None  # "float16", "bfloat16", or None for auto


@dataclass
class LoRAConfig:
    """Configuration for LoRA fine-tuning."""

    r: int = 16  # Rank
    lora_alpha: int = 32  # LoRA scaling
    lora_dropout: float = 0.05  # Dropout
    target_modules: List[str] = field(
        default_factory=lambda: [
            "q_proj",
            "k_proj",
            "v_proj",
            "o_proj",
            "gate_proj",
            "up_proj",
            "down_proj",
        ]
    )
    bias: str = "none"  # "none", "all", or "lora_only"
    use_gradient_checkpointing: bool = True


@dataclass
class TrainingConfig:
    """Configuration for training."""

    num_train_epochs: int = 3
    per_device_train_batch_size: int = 4
    per_device_eval_batch_size: int = 4
    gradient_accumulation_steps: int = 4
    learning_rate: float = 2e-4
    weight_decay: float = 0.01
    warmup_ratio: float = 0.1
    fp16: bool = True
    bf16: bool = False
    logging_steps: int = 10
    eval_strategy: str = "epoch"
    save_strategy: str = "epoch"
    save_total_limit: int = 2
    load_best_model_at_end: bool = True


@dataclass
class PlatformConfig:
    """Configuration for different platforms."""

    platform: str = "local"  # "local", "unsloth", "azure", "aws", "gcp"
    compute_type: str = "gpu"  # "cpu", "gpu", "tpu"


# ============================================================
# Data Preparation
# ============================================================


def load_training_data(file_path: str) -> List[Dict[str, str]]:
    """
    Load training data from JSONL file.

    Args:
        file_path: Path to JSONL file

    Returns:
        List of dictionaries with instruction, input, output
    """
    data = []
    with open(file_path, "r") as f:
        for line in f:
            data.append(json.loads(line))
    return data


def format_instruction_data(examples: Dict, tokenizer: Any) -> Dict:
    """
    Format instruction data for training.

    Args:
        examples: Dictionary with instruction, input, output
        tokenizer: Tokenizer instance

    Returns:
        Tokenized examples
    """
    # Combine instruction, input, and output
    texts = []
    for instruction, input_text, output in zip(
        examples["instruction"], examples["input"], examples["output"]
    ):
        text = f"""Below is an instruction that describes a task, paired with an input that provides further context. Write a response that appropriately completes the request.

### Instruction:
{instruction}

### Input:
{input_text}

### Response:
{output}"""
        texts.append(text)

    # Tokenize
    return tokenizer(texts, padding="max_length", truncation=True, max_length=2048)


# ============================================================
# Model Loading Functions
# ============================================================


def load_model_huggingface(model_config: ModelConfig, lora_config: LoRAConfig) -> tuple:
    """
    Load model using HuggingFace Transformers.

    Args:
        model_config: Model configuration
        lora_config: LoRA configuration

    Returns:
        Tuple of (model, tokenizer)
    """
    from transformers import AutoModelForCausalLM, AutoTokenizer, BitsAndBytesConfig
    import torch

    # Configure quantization
    bnb_config = None
    if model_config.load_in_4bit:
        bnb_config = BitsAndBytesConfig(
            load_in_4bit=True,
            bnb_4bit_quant_type="nf4",
            bnb_4bit_compute_dtype=(
                torch.float16
                if model_config.dtype is None
                else getattr(torch, model_config.dtype)
            ),
            bnb_4bit_use_double_quant=True,
        )

    # Load tokenizer
    tokenizer = AutoTokenizer.from_pretrained(model_config.model_name)
    tokenizer.pad_token = tokenizer.eos_token

    # Load model
    model = AutoModelForCausalLM.from_pretrained(
        model_config.model_name,
        quantization_config=bnb_config,
        device_map="auto",
        trust_remote_code=True,
    )

    # Apply LoRA
    from peft import LoraConfig as PEFTLoraConfig, get_peft_model, TaskType

    peft_lora_config = PEFTLoraConfig(
        r=lora_config.r,
        lora_alpha=lora_config.lora_alpha,
        lora_dropout=lora_config.lora_dropout,
        target_modules=lora_config.target_modules,
        bias=lora_config.bias,
        task_type=TaskType.CAUSAL_LM,
    )

    model = get_peft_model(model, peft_lora_config)

    if lora_config.use_gradient_checkpointing:
        model.gradient_checkpointing_enable()

    model.print_trainable_parameters()

    return model, tokenizer


def load_model_unsloth(model_config: ModelConfig, lora_config: LoRAConfig) -> tuple:
    """
    Load model using Unsloth for faster training.

    Args:
        model_config: Model configuration
        lora_config: LoRA configuration

    Returns:
        Tuple of (model, tokenizer)
    """
    from unsloth import FastLanguageModel
    import torch

    # Load model with Unsloth
    model, tokenizer = FastLanguageModel.from_pretrained(
        model_name=model_config.model_name,
        max_seq_length=model_config.max_seq_length,
        dtype=model_config.dtype,
        load_in_4bit=model_config.load_in_4bit,
    )

    # Add LoRA
    model = FastLanguageModel.get_peft_model(
        model,
        r=lora_config.r,
        lora_alpha=lora_config.lora_alpha,
        lora_dropout=lora_config.lora_dropout,
        target_modules=lora_config.target_modules,
        bias=lora_config.bias,
        use_gradient_checkpointing=lora_config.use_gradient_checkpointing,
        random_state=3407,
    )

    model.print_trainable_parameters()

    return model, tokenizer


# ============================================================
# Training Functions
# ============================================================


def create_training_arguments(
    training_config: TrainingConfig, output_dir: str
) -> "TrainingArguments":
    """
    Create HuggingFace TrainingArguments.

    Args:
        training_config: Training configuration
        output_dir: Output directory

    Returns:
        TrainingArguments object
    """
    from transformers import TrainingArguments
    import torch

    return TrainingArguments(
        output_dir=output_dir,
        num_train_epochs=training_config.num_train_epochs,
        per_device_train_batch_size=training_config.per_device_train_batch_size,
        per_device_eval_batch_size=training_config.per_device_eval_batch_size,
        gradient_accumulation_steps=training_config.gradient_accumulation_steps,
        learning_rate=training_config.learning_rate,
        weight_decay=training_config.weight_decay,
        warmup_ratio=training_config.warmup_ratio,
        fp16=training_config.fp16 and not torch.cuda.is_bf16_supported(),
        bf16=training_config.bf16 or torch.cuda.is_bf16_supported(),
        logging_steps=training_config.logging_steps,
        eval_strategy=training_config.eval_strategy,
        save_strategy=training_config.save_strategy,
        save_total_limit=training_config.save_total_limit,
        load_best_model_at_end=training_config.load_best_model_at_end,
        report_to="none",
    )


def train_with_huggingface(
    model: Any,
    tokenizer: Any,
    train_dataset: Any,
    eval_dataset: Any,
    training_config: TrainingConfig,
    output_dir: str = "./output",
) -> Any:
    """
    Train model using HuggingFace Trainer.

    Args:
        model: Model to train
        tokenizer: Tokenizer
        train_dataset: Training dataset
        eval_dataset: Evaluation dataset
        training_config: Training configuration
        output_dir: Output directory

    Returns:
        Trainer object
    """
    from transformers import Trainer, DataCollatorForLanguageModeling

    # Create training arguments
    training_args = create_training_arguments(training_config, output_dir)

    # Data collator
    data_collator = DataCollatorForLanguageModeling(
        tokenizer=tokenizer,
        mlm=False,  # Causal LM
    )

    # Create trainer
    trainer = Trainer(
        model=model,
        args=training_args,
        train_dataset=train_dataset,
        eval_dataset=eval_dataset,
        data_collator=data_collator,
    )

    # Train
    trainer.train()

    return trainer


def train_with_unsloth(
    model: Any,
    tokenizer: Any,
    train_dataset: Any,
    training_config: TrainingConfig,
    output_dir: str = "./output",
) -> Any:
    """
    Train model using Unsloth Trainer.

    Args:
        model: Model to train
        tokenizer: Tokenizer
        train_dataset: Training dataset
        training_config: Training configuration
        output_dir: Output directory

    Returns:
        Trainer object
    """
    from unsloth import Trainer
    import torch

    # Create training arguments
    training_args = create_training_arguments(training_config, output_dir)

    # Create trainer
    trainer = Trainer(
        model=model,
        tokenizer=tokenizer,
        train_dataset=train_dataset,
        args=training_args,
    )

    # Train
    trainer.train()

    return trainer


# ============================================================
# Cloud Platform Functions
# ============================================================


def create_azure_job_config(
    model_config: ModelConfig,
    training_config: TrainingConfig,
    compute_name: str,
    data_path: str,
) -> Dict:
    """
    Create Azure ML job configuration.

    Args:
        model_config: Model configuration
        training_config: Training configuration
        compute_name: Compute target name
        data_path: Path to training data

    Returns:
        Dictionary with job configuration
    """
    from azure.ai.ml import command

    # Create command job
    job = command(
        code="./",
        command=f"python train.py --model_name {model_config.model_name}",
        environment="finetune-env:latest",
        compute=compute_name,
        instance_count=1,
    )

    return {
        "job": job,
        "compute": compute_name,
        "data": data_path,
    }


def create_aws_estimator_config(
    model_config: ModelConfig,
    training_config: TrainingConfig,
    role: str,
    instance_type: str = "ml.p3.2xlarge",
) -> Dict:
    """
    Create AWS SageMaker estimator configuration.

    Args:
        model_config: Model configuration
        training_config: Training configuration
        role: IAM role
        instance_type: Instance type

    Returns:
        Dictionary with estimator configuration
    """
    from sagemaker.huggingface import HuggingFace

    hyperparameters = {
        "MODEL_NAME": model_config.model_name,
        "num_train_epochs": training_config.num_train_epochs,
        "per_device_train_batch_size": training_config.per_device_train_batch_size,
        "learning_rate": training_config.learning_rate,
    }

    estimator = HuggingFace(
        entry_point="train.py",
        source_dir="./",
        instance_type=instance_type,
        instance_count=1,
        role=role,
        transformers_version="4.28.0",
        pytorch_version="2.0.0",
        py_version="py310",
        hyperparameters=hyperparameters,
    )

    return {"estimator": estimator}


def create_gcp_job_config(
    model_config: ModelConfig,
    training_config: TrainingConfig,
    machine_type: str = "a2-highgpu-1g",
    accelerator_type: str = "NVIDIA_TESLA_A100",
) -> Dict:
    """
    Create GCP Vertex AI job configuration.

    Args:
        model_config: Model configuration
        training_config: Training configuration
        machine_type: Machine type
        accelerator_type: Accelerator type

    Returns:
        Dictionary with job configuration
    """
    from google.cloud import aiplatform

    job = aiplatform.CustomTrainingJob(
        display_name="llama-finetuning-job",
        script_path="train.py",
        container_uri="gcr.io/project/trainer:latest",
        requirements=[
            "transformers>=4.28.0",
            "datasets>=2.14.0",
            "peft>=0.4.0",
        ],
        machine_type=machine_type,
        accelerator_type=accelerator_type,
        accelerator_count=1,
    )

    return {"job": job}


# ============================================================
# Main Pipeline Class
# ============================================================


class FineTuningPipeline:
    """
    Complete fine-tuning pipeline supporting multiple platforms.
    """

    def __init__(
        self,
        model_config: ModelConfig = None,
        lora_config: LoRAConfig = None,
        training_config: TrainingConfig = None,
        platform_config: PlatformConfig = None,
    ):
        self.model_config = model_config or ModelConfig()
        self.lora_config = lora_config or LoRAConfig()
        self.training_config = training_config or TrainingConfig()
        self.platform_config = platform_config or PlatformConfig()

        self.model = None
        self.tokenizer = None
        self.trainer = None

    def load_data(self, data_path: str) -> Any:
        """Load and prepare training data."""
        from datasets import Dataset, load_dataset

        # Load data
        dataset = load_dataset("json", data_files=data_path)

        # Format data
        # Note: In practice, apply format_instruction_data here

        return dataset

    def load_model(self):
        """Load model based on platform."""
        if self.platform_config.platform == "unsloth":
            self.model, self.tokenizer = load_model_unsloth(
                self.model_config, self.lora_config
            )
        else:
            self.model, self.tokenizer = load_model_huggingface(
                self.model_config, self.lora_config
            )

    def train(self, train_data: Any, eval_data: Any = None):
        """Train the model."""
        if self.platform_config.platform == "unsloth":
            self.trainer = train_with_unsloth(
                self.model,
                self.tokenizer,
                train_data,
                self.training_config,
            )
        else:
            self.trainer = train_with_huggingface(
                self.model,
                self.tokenizer,
                train_data,
                eval_data,
                self.training_config,
            )

    def save(self, output_path: str):
        """Save the fine-tuned model."""
        self.model.save_pretrained(output_path)
        self.tokenizer.save_pretrained(output_path)

    def run(self, data_path: str, output_path: str = "./model"):
        """Run the complete pipeline."""
        print("Loading data...")
        dataset = self.load_data(data_path)

        print("Loading model...")
        self.load_model()

        print("Training...")
        self.train(dataset["train"], dataset.get("test"))

        print(f"Saving to {output_path}...")
        self.save(output_path)

        print("Done!")


# ============================================================
# Example Usage
# ============================================================


def main():
    """Main function demonstrating usage."""

    # Example 1: Local training with HuggingFace
    print("=" * 50)
    print("Example 1: HuggingFace Local Training")
    print("=" * 50)

    # Create pipeline
    pipeline = FineTuningPipeline(
        model_config=ModelConfig(
            model_name="TinyLlama/TinyLlama-1.1B-Chat-v1.0",
            load_in_4bit=True,
        ),
        lora_config=LoRAConfig(r=8),
        training_config=TrainingConfig(
            num_train_epochs=1,
            per_device_train_batch_size=2,
        ),
        platform_config=PlatformConfig(platform="local"),
    )

    print(f"Model: {pipeline.model_config.model_name}")
    print(f"LoRA rank: {pipeline.lora_config.r}")
    print(f"Training epochs: {pipeline.training_config.num_train_epochs}")
    print(f"Platform: {pipeline.platform_config.platform}")

    # Example 2: Unsloth training
    print("\n" + "=" * 50)
    print("Example 2: Unsloth Training")
    print("=" * 50)

    unsloth_pipeline = FineTuningPipeline(
        model_config=ModelConfig(
            model_name="unsloth/llama-3-8b-bnb-4bit",
            load_in_4bit=True,
        ),
        lora_config=LoRAConfig(r=16),
        training_config=TrainingConfig(num_train_epochs=3),
        platform_config=PlatformConfig(platform="unsloth"),
    )

    print(f"Model: {unsloth_pipeline.model_config.model_name}")
    print(f"Platform: {unsloth_pipeline.platform_config.platform}")
    print(
        f"Use gradient checkpointing: {unsloth_pipeline.lora_config.use_gradient_checkpointing}"
    )

    # Example 3: Cloud configurations
    print("\n" + "=" * 50)
    print("Example 3: Cloud Platform Configurations")
    print("=" * 50)

    # Azure configuration
    azure_config = create_azure_job_config(
        model_config=ModelConfig(),
        training_config=TrainingConfig(),
        compute_name="gpu-cluster",
        data_path="azureml://data/train",
    )
    print(f"Azure compute: {azure_config['compute']}")

    # AWS configuration
    aws_config = create_aws_estimator_config(
        model_config=ModelConfig(),
        training_config=TrainingConfig(),
        role="arn:aws:iam::123456789:role/SageMakerRole",
        instance_type="ml.p3.2xlarge",
    )
    print(f"AWS instance: ml.p3.2xlarge")

    # GCP configuration
    gcp_config = create_gcp_job_config(
        model_config=ModelConfig(),
        training_config=TrainingConfig(),
        machine_type="a2-highgpu-1g",
    )
    print(f"GCP machine: a2-highgpu-1g")


if __name__ == "__main__":
    main()
