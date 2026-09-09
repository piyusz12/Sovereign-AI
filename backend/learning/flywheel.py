"""
Sovereign AI: Continuous Fine-Tuning Data Flywheel
Aggregates telemetry traces, user corrections, and evaluations into privacy-sanitized
LoRA and Direct Preference Optimization (DPO) datasets for sovereign model adaptation.
"""

import os
import re
import json
import time
import logging
from typing import Dict, Any, List, Optional
from dataclasses import dataclass, field, asdict

logger = logging.getLogger(__name__)

@dataclass
class FlywheelSample:
    sample_id: str
    timestamp: float
    task_type: str
    prompt: str
    chosen_response: str
    rejected_response: Optional[str] = None
    rating: int = 5  # 1 to 5 scale
    user_role: str = "software_engineer"
    curated: bool = True

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


class ContinuousFineTuningFlywheel:
    """
    Manages self-hosted continuous learning datasets with PII sanitization.
    """

    def __init__(self, data_dir: Optional[str] = None):
        self.data_dir = data_dir or os.path.join(os.path.dirname(__file__), "datasets")
        os.makedirs(self.data_dir, exist_ok=True)
        self.samples: List[FlywheelSample] = []
        self._load_existing_samples()

    def _sanitize_pii(self, text: str) -> str:
        """
        Redacts common secrets, tokens, IPv4 addresses, and email patterns.
        """
        # API keys / Bearer tokens
        sanitized = re.sub(r"(Bearer\s+)[A-Za-z0-9_\-\.]{15,}", r"\1[REDACTED_TOKEN]", text, flags=re.IGNORECASE)
        sanitized = re.sub(r"(ak-[a-zA-Z0-9]{20,})", "[REDACTED_API_KEY]", sanitized)
        # Emails
        sanitized = re.sub(r"[\w\.-]+@[\w\.-]+\.\w+", "[REDACTED_EMAIL]", sanitized)
        # IPv4 addresses
        sanitized = re.sub(r"\b(?:\d{1,3}\.){3}\d{1,3}\b", "[REDACTED_IP]", sanitized)
        return sanitized

    def _load_existing_samples(self):
        lora_file = os.path.join(self.data_dir, "lora_dataset.jsonl")
        if os.path.exists(lora_file):
            try:
                with open(lora_file, "r", encoding="utf-8") as f:
                    for line in f:
                        if line.strip():
                            data = json.loads(line)
                            self.samples.append(FlywheelSample(
                                sample_id=data.get("sample_id", f"s-{len(self.samples)}"),
                                timestamp=data.get("timestamp", time.time()),
                                task_type=data.get("task_type", "general"),
                                prompt=data.get("instruction", ""),
                                chosen_response=data.get("output", ""),
                                rating=5
                            ))
            except Exception as e:
                logger.warning(f"Failed to load existing flywheel samples: {e}")

    def record_interaction(
        self,
        prompt: str,
        chosen_response: str,
        rejected_response: Optional[str] = None,
        rating: int = 5,
        task_type: str = "coding",
        user_role: str = "software_engineer"
    ) -> FlywheelSample:
        """
        Records, sanitizes, and indexes a high-value interaction for fine-tuning.
        """
        sanitized_prompt = self._sanitize_pii(prompt)
        sanitized_chosen = self._sanitize_pii(chosen_response)
        sanitized_rejected = self._sanitize_pii(rejected_response) if rejected_response else None

        sample_id = f"FLY-{int(time.time() * 1000)}-{len(self.samples) + 1}"
        sample = FlywheelSample(
            sample_id=sample_id,
            timestamp=time.time(),
            task_type=task_type,
            prompt=sanitized_prompt,
            chosen_response=sanitized_chosen,
            rejected_response=sanitized_rejected,
            rating=rating,
            user_role=user_role
        )

        self.samples.append(sample)
        self._append_to_disk(sample)
        return sample

    def _append_to_disk(self, sample: FlywheelSample):
        """
        Persists sample to disk in LoRA and DPO format.
        """
        # 1. LoRA format
        lora_path = os.path.join(self.data_dir, "lora_dataset.jsonl")
        lora_entry = {
            "sample_id": sample.sample_id,
            "timestamp": sample.timestamp,
            "task_type": sample.task_type,
            "instruction": sample.prompt,
            "input": "",
            "output": sample.chosen_response
        }
        with open(lora_path, "a", encoding="utf-8") as f:
            f.write(json.dumps(lora_entry, ensure_ascii=False) + "\n")

        # 2. DPO format (if rejected response present)
        if sample.rejected_response:
            dpo_path = os.path.join(self.data_dir, "dpo_dataset.jsonl")
            dpo_entry = {
                "sample_id": sample.sample_id,
                "timestamp": sample.timestamp,
                "prompt": sample.prompt,
                "chosen": sample.chosen_response,
                "rejected": sample.rejected_response,
                "rating_diff": sample.rating - 1
            }
            with open(dpo_path, "a", encoding="utf-8") as f:
                f.write(json.dumps(dpo_entry, ensure_ascii=False) + "\n")

    def get_stats(self) -> Dict[str, Any]:
        """Returns statistics on the continuous fine-tuning pipeline."""
        dpo_count = sum(1 for s in self.samples if s.rejected_response)
        return {
            "total_curated_samples": len(self.samples),
            "lora_pairs": len(self.samples),
            "dpo_preference_pairs": dpo_count,
            "storage_path": self.data_dir,
            "pii_sanitization_active": True,
            "ready_for_export": len(self.samples) >= 1
        }


flywheel_engine = ContinuousFineTuningFlywheel()
