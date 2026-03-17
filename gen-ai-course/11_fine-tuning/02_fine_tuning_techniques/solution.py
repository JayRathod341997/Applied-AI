"""
Solution: Advanced Fine-tuning Technique Comparison
"""

# Sample solution demonstrating LoRA configuration
LORA_CONFIG = {
    "r": 8,
    "lora_alpha": 16,
    "target_modules": ["q_proj", "v_proj", "k_proj", "o_proj"],
    "lora_dropout": 0.05,
    "bias": "none",
    "task_type": "CAUSAL_LM"
}

# QLoRA configuration
QLORA_CONFIG = {
    "load_in_4bit": True,
    "bnb_4bit_compute_dtype": "float16",
    "bnb_4bit_use_double_quant": True,
    "bnb_4bit_quant_type": "nf4"
}


def recommend_technique(gpu_memory_gb, model_size_b, preserve_capabilities=False):
    """Recommend technique based on hardware and requirements."""
    
    required_full = model_size_b * 2
    required_lora = model_size_b * 1 + 4
    required_qlora = model_size_b * 0.5 + 2
    
    if gpu_memory_gb >= required_full:
        if preserve_capabilities:
            return "Full Fine-tuning + Regularization"
        return "Full Fine-tuning"
    elif gpu_memory_gb >= required_lora:
        return "LoRA"
    elif gpu_memory_gb >= required_qlora:
        return "QLoRA"
    else:
        return "Not enough memory for this model size"


if __name__ == "__main__":
    # Test scenarios
    scenarios = [
        (24, 7),  # 24GB GPU, 7B model
        (80, 70),  # 80GB GPU, 70B model
        (16, 7),  # 16GB GPU, 7B model
    ]
    
    print("Technique Recommendations")
    print("=" * 40)
    
    for gpu, model in scenarios:
        result = recommend_technique(gpu, model)
        print(f"GPU: {gpu}GB, Model: {model}B -> {result}")
