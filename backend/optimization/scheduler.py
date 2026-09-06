import asyncio
import logging
import uuid
from typing import Callable, Any, Coroutine
from pydantic import BaseModel

logger = logging.getLogger(__name__)

class InferenceJob(BaseModel):
    id: str
    task_type: str
    priority: int # 1 = high (interactive), 5 = low (background)
    
class GPUScheduler:
    """
    Serializes heavy GPU inference tasks to prevent concurrent overload on 8GB VRAM.
    """
    def __init__(self):
        # We only allow 1 heavy concurrent task at a time for RTX 4060
        self.semaphore = asyncio.Semaphore(1)
        self.queue_depth = 0
        
    async def schedule(self, task_type: str, priority: int, coro: Coroutine) -> Any:
        job = InferenceJob(id=str(uuid.uuid4()), task_type=task_type, priority=priority)
        
        # In a more advanced implementation we would use PriorityQueue. 
        # For SIH, a Semaphore is sufficient to prevent OOMs by serializing.
        self.queue_depth += 1
        logger.info(f"Queued GPU Job {job.id} ({task_type}) [Queue Depth: {self.queue_depth}]")
        
        try:
            async with self.semaphore:
                logger.info(f"Executing GPU Job {job.id} ({task_type})")
                return await coro
        finally:
            self.queue_depth -= 1
            logger.info(f"Finished GPU Job {job.id} [Queue Depth: {self.queue_depth}]")

gpu_scheduler = GPUScheduler()
