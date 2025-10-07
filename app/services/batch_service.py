import uuid
import threading
from typing import Dict, Any, Optional
import time
from flask import current_app


from ..constants import (
    KEY_TOTAL_HOSPITALS,
)
from ..repository import Batch
from ..constants import (
    KEY_STATUS,
    KEY_TOTAL_HOSPITALS,
    KEY_PROCESSED_COUNT,
    KEY_FAILED_COUNT,
    KEY_HOSPITALS,
)
from ..utils.converter import BatchDtoConverter


class BatchService:
    def __init__(self, *, validator, repository, processor) -> None:
        self._validator = validator
        self._repository = repository
        self._processor = processor

    def bulk_create_hospitals(self, csv_text: str, *, max_hospitals: Optional[int] = None) -> Dict[str, Any]:
        validation = self._validator.validate_and_parse(csv_text, max_hospitals=max_hospitals)
        if not validation.get("valid"):
            return {
                "ok": False,
                "status": 400,
                "body": {
                    "error": "CSV validation failed",
                    "errors": validation.get("errors", []),
                },
            }

        hospitals = validation.get("hospitals", [])
        hospital_count = len(hospitals)

        batch_id = str(uuid.uuid4())
        batch: Batch = BatchDtoConverter.build_initial_batch(batch_id, hospitals)

        self._repository.save(batch)
        batch["start_time"] = time.time()
        self._repository.save(batch)
        try:
            app = current_app._get_current_object()
        except Exception:
            app = None
        threading.Thread(target=self._processor.start_batch, args=(batch_id, app), daemon=True).start()

        return {
            "ok": True,
            "status": 202,
            "body": {
                "batch_id": batch_id,
                "total_hospitals": hospital_count,
                "processed_hospitals": 0,
                "failed_hospitals": 0,
                "processing_time_seconds": 0.0,
                "batch_activated": False,
                KEY_HOSPITALS: [
                    {"row": row, "name": data.get("name"), "status": "pending"}
                    for row, data in hospitals
                ],
            },
        }

    def get_batch_status(self, batch_id: str) -> Dict[str, Any]:
        try:
            batch: Batch = self._repository.find_by_batch_id(batch_id)
        except KeyError:
            return {"ok": False, "status": 404, "body": {"error": f"Batch {batch_id} not found"}}

        body = BatchDtoConverter.to_status_dto(batch)
        return {"ok": True, "status": 200, "body": body}

    def resume_batch(self, batch_id: str) -> Dict[str, Any]:
        try:
            batch: Batch = self._repository.find_by_batch_id(batch_id)
        except KeyError:
            return {"ok": False, "status": 404, "body": {"error": f"Batch {batch_id} not found"}}

        hospitals = batch.get("hospitals", {})
        total = batch.get("total_hospitals", len(hospitals))
        processed = sum(1 for h in hospitals.values() if h.get("status") in {"created", "activated"})
        if processed >= total:
            return {"ok": False, "status": 409, "body": {"error": "Batch is already completed; cannot resume"}}

        try:
            app = current_app._get_current_object()
        except Exception:
            app = None
        threading.Thread(target=self._processor.start_batch, args=(batch_id, app), daemon=True).start()
        return {"ok": True, "status": 202, "body": {"message": "Resume started", "scheduled": total - processed}}

    def validate_hospitals(self, csv_text: str, *, max_hospitals: Optional[int] = None) -> Dict[str, Any]:
        """Validate and parse the CSV, returning the same shape as the route previously returned."""
        result = self._validator.validate_and_parse(csv_text, max_hospitals=max_hospitals)
        return {
            "valid": result.get("valid", False),
            "errors": result.get("errors", []),
            "row_count": result.get("row_count", 0),
            "header": result.get("header"),
        }


