"""Small in-process inference telemetry for latency diagnosis.

The recorder is deliberately local and bounded. It gives the dashboard the
signals needed to distinguish a saturated scheduler from prompt prefill or
token decode pressure without sending enterprise prompt data elsewhere.
"""

from __future__ import annotations

from collections import deque
from dataclasses import asdict, dataclass
from statistics import median
from time import time
from typing import Deque


@dataclass(frozen=True)
class InferenceMetric:
    model: str
    task_type: str
    ttft_ms: float
    itl_ms: float
    tokens_per_second: float
    prompt_tokens: int
    output_tokens: int
    queue_wait_ms: float
    total_duration_ms: float
    prefix_key: str
    timestamp: float


class InferenceTelemetry:
    def __init__(self, max_records: int = 500) -> None:
        self._records: Deque[InferenceMetric] = deque(maxlen=max_records)

    def record(self, metric: InferenceMetric) -> None:
        self._records.append(metric)

    @staticmethod
    def _percentile(values: list[float], percentile: float) -> float:
        if not values:
            return 0.0
        ordered = sorted(values)
        index = round((len(ordered) - 1) * percentile)
        return round(ordered[index], 2)

    def snapshot(self) -> dict:
        records = list(self._records)
        ttft = [item.ttft_ms for item in records]
        itl = [item.itl_ms for item in records]
        tps = [item.tokens_per_second for item in records if item.tokens_per_second > 0]
        queues = [item.queue_wait_ms for item in records]
        return {
            "sample_count": len(records),
            "ttft_ms": {"p50": self._percentile(ttft, 0.50), "p95": self._percentile(ttft, 0.95), "p99": self._percentile(ttft, 0.99)},
            "itl_ms": {"p50": self._percentile(itl, 0.50), "p95": self._percentile(itl, 0.95), "p99": self._percentile(itl, 0.99)},
            "tokens_per_second": round(median(tps), 2) if tps else 0.0,
            "queue_wait_ms": {"p50": self._percentile(queues, 0.50), "p95": self._percentile(queues, 0.95)},
            "recent": [asdict(item) for item in records[-20:]],
        }

    def clear(self) -> None:
        self._records.clear()


def new_metric(**values: object) -> InferenceMetric:
    """Create a metric with a local timestamp while keeping call sites concise."""
    return InferenceMetric(timestamp=time(), **values)


inference_telemetry = InferenceTelemetry()
