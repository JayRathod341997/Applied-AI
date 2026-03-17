"""
Exercise: Fine-tuning Technique Selector
"""

from typing import Dict, List
from dataclasses import dataclass


@dataclass
class HardwareSpec:
    """Hardware specifications."""

    gpu_memory_gb: int
    num_gpus: int = 1
    gpu_type: str = "consumer"


@dataclass
class ProjectRequirements:
    """Project requirements."""

    model_size_b: int  # in billions
    goal: str
    timeline_weeks: int
    preserve_capabilities: bool = False


class FineTuningSelector:
    """Select appropriate fine-tuning technique."""

    TECHNIQUES = {
        "QLoRA": {
            "memory_efficient": True,
            "max_model_size": 70,
            "quality": "high",
            "speed": "fast",
        },
        "LoRA": {
            "memory_efficient": True,
            "max_model_size": 70,
            "quality": "very_high",
            "speed": "fast",
        },
        "Full": {
            "memory_efficient": False,
            "max_model_size": 13,
            "quality": "best",
            "speed": "slow",
        },
    }

    def estimate_memory(self, model_size: int, technique: str) -> int:
        """Estimate required GPU memory in GB."""
        if technique == "Full":
            return model_size * 2  # 2GB per parameter
        elif technique == "LoRA":
            return model_size * 1 + 4  # ~1GB + overhead
        elif technique == "QLoRA":
            return model_size * 0.5 + 2  # ~0.5GB + overhead
        return 0

    def can_use_technique(
        self, hw: HardwareSpec, req: ProjectRequirements, technique: str
    ) -> bool:
        """Check if technique can be used."""
        total_memory = hw.gpu_memory_gb * hw.num_gpus
        required = self.estimate_memory(req.model_size_b, technique)

        return total_memory >= required

    def recommend(self, hw: HardwareSpec, req: ProjectRequirements) -> str:
        """Recommend best technique."""
        candidates = []

        for technique in self.TECHNIQUES:
            if self.can_use_technique(hw, req, technique):
                candidates.append(technique)

        # Apply preferences
        if req.preserve_capabilities and "LoRA" in candidates:
            return "LoRA"  # Best for preserving capabilities

        if candidates:
            return candidates[0]  # Return first viable option

        return "Cannot recommend - insufficient resources"


# Test cases
SCENARIOS = [
    (HardwareSpec(gpu_memory_gb=24), ProjectRequirements(7, "chatbot", 2)),
    (HardwareSpec(gpu_memory_gb=80, num_gpus=8), ProjectRequirements(70, "legal", 4)),
    (HardwareSpec(gpu_memory_gb=16), ProjectRequirements(7, "experiments", 1)),
]


def main():
    selector = FineTuningSelector()

    print("Fine-tuning Technique Recommendations")
    print("=" * 50)

    for hw, req in SCENARIOS:
        rec = selector.recommend(hw, req)
        print(f"\nModel: {req.model_size_b}B, Goal: {req.goal}")
        print(f"Hardware: {hw.gpu_memory_gb}GB x {hw.num_gpus}")
        print(f"Recommendation: {rec}")


if __name__ == "__main__":
    main()
