import logging
from typing import Callable, Any, Optional, Dict as TypingDict
from flask import current_app
from ..repository.hospital_batch_repository import HospitalBatchRepository
import time

class BatchProcessor:
    def __init__(self, *, client_factory: Callable[[], Any], repository: HospitalBatchRepository, logger: Optional[logging.Logger] = None):
        self._repository = repository
        self._client_factory = client_factory
        self.logger = logger or logging.getLogger(__name__)
        self._app = None

    def start_batch(self, batch_id: str, app: Optional[Any] = None) -> None:
        self.logger.info(f"Processing batch {batch_id}")
        if app is not None:
            self._app = app
        if self._app is None:
            self._app = current_app._get_current_object()

        with self._app.app_context():
            client = self._client_factory()
            batch = self._repository.find_by_batch_id(batch_id)
            hospitals = batch.get("hospitals", {})

            processed_count = 0
            for hospital_id, hospital in hospitals.items():
                processed_count += self._process_hospital(client, batch_id, hospital_id, hospital)

            failed_hospitals = 0
            if processed_count < len(hospitals):
                failed_hospitals = len(hospitals) - processed_count
                self.logger.info(f"Failed to create {failed_hospitals} hospitals")
                self.logger.info(f"Skipping activation of batch {batch_id}")
                batch_activated = False
            else:
                self._activate_batch(client, batch_id, hospitals)
                batch_activated = True

            self._repository.update_batch_processing_params(batch_id, processed_count, failed_hospitals, time.time(), batch_activated)

    def _activate_batch(self, client: Any, batch_id: str, hospitals: TypingDict[str, Any]) -> None:
        try:
            self.logger.info(f"Activating batch {batch_id}")
            client.activate_batch(batch_id)
            [self._repository.update_hospital_status(batch_id, hospital_id, "activated") for hospital_id in hospitals.keys()]
        except Exception as e:
            self.logger.error(f"Failed to activate batch {batch_id}: {e}")

    def _process_hospital(self, client: Any, batch_id: str, hospital_id: str, hospital: dict) -> int:
        name = hospital.get("name", hospital_id)
        # Skip hospitals already created/activated
        if hospital.get("status") in {"created", "activated"}:
            self.logger.info(f"Skipping already created hospital '{name}' (id: {hospital_id})")
            return 1
        try:
            self.logger.info(f"Creating hospital '{name}' (id: {hospital_id})")
            self._repository.update_hospital_status(batch_id, hospital_id, "processing")
            response = client.create_hospital(hospital, batch_id)
            hospital_api_id = response.get("id")
            self._repository.update_hospital_status(batch_id, hospital_id, "created")
            if hospital_api_id is not None:
                batch = self._repository.find_by_batch_id(batch_id)
                batch_hospital = batch["hospitals"].get(hospital_id, {})
                batch_hospital["hospital_id"] = hospital_api_id
                batch["hospitals"][hospital_id] = batch_hospital
                self._repository.save(batch)
            return 1
        except Exception as e:
            self.logger.error(f"Failed to create hospital '{name}': {e}")
            self._repository.update_hospital_status(batch_id, hospital_id, "failed")
            return 0

