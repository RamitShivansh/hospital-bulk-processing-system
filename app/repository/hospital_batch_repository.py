import threading
import uuid
from typing import Dict
import copy
from . import Batch
from .decorators import synchronized

class HospitalBatchRepository:
    def __init__(self) -> None:
        self._batches: Dict[str, Batch] = {}
        self._lock = threading.RLock()

    @synchronized
    def save(self, batch: Batch) -> Batch:
        batch_id = batch.get("id") or str(uuid.uuid4())
        batch["id"] = batch_id
        self._batches[batch_id] = batch
        return copy.deepcopy(batch)

    @synchronized
    def update_hospital_status(self, batch_id: str, hospital_id: str, status: str) -> None:
        batch = self._batches[batch_id]
        batch["hospitals"][hospital_id]["status"] = status

    @synchronized
    def find_by_batch_id(self, batch_id: str) -> Batch:
        return copy.deepcopy(self._batches[batch_id])

    @synchronized
    def update_batch_processing_params(self, batch_id: str, processed_hospitals: int, failed_hospitals: int, end_time: float, batch_activated: bool) -> None:
        batch = self._batches[batch_id]
        batch["processed_hospitals"] = processed_hospitals
        batch["failed_hospitals"] = failed_hospitals
        batch["end_time"] = end_time
        batch["batch_activated"] = batch_activated
        self._batches[batch_id] = batch