import json
import time

import pytest
from flask import Flask

from app.services.batch_service import BatchService
from app.repository.hospital_batch_repository import HospitalBatchRepository
from app.services.batch_processor import BatchProcessor
from app.services.validation_service import HospitalCsvValidator
from app.services.hospital_api_client import HospitalApiClient
from app.constants import EXT_BATCH_PROCESSOR, EXT_BATCH_REPOSITORY, EXT_CSV_VALIDATOR, EXT_BATCH_SERVICE, KEY_TOTAL_HOSPITALS


class DummyClient(HospitalApiClient):
    def __init__(self):
        pass

    def create_hospital(self, hospital_data, batch_id):
        return {"id": f"api-{hospital_data.get('name','x')}"}

    def activate_batch(self, batch_id):
        return {"activated_hospitals": []}


def make_app():
    app = Flask(__name__)
    repo = HospitalBatchRepository()
    processor = BatchProcessor(client_factory=lambda: DummyClient(), repository=repo)
    validator = HospitalCsvValidator()
    service = BatchService(validator=validator, repository=repo, processor=processor)

    app.extensions = {}
    app.extensions[EXT_BATCH_REPOSITORY] = repo
    app.extensions[EXT_BATCH_PROCESSOR] = processor
    app.extensions[EXT_CSV_VALIDATOR] = validator
    app.extensions[EXT_BATCH_SERVICE] = service
    return app


def test_bulk_create_hospitals_success():
    app = make_app()
    csv_text = "name,address,phone\nA,addr,1234567890\nB,addr,\n"
    with app.app_context():
        result = app.extensions[EXT_BATCH_SERVICE].bulk_create_hospitals(csv_text)
        assert result["ok"] is True
        assert result["status"] == 202
        body = result["body"]
        assert "batch_id" in body
        assert body["total_hospitals"] == 2
        assert body["processed_hospitals"] == 0
        assert body["failed_hospitals"] == 0
        assert isinstance(body.get("hospitals"), list)


def test_bulk_create_hospitals_validation_error():
    app = make_app()
    csv_text = "bad,header\nA\n"
    with app.app_context():
        result = app.extensions[EXT_BATCH_SERVICE].bulk_create_hospitals(csv_text)
        assert result["ok"] is False
        assert result["status"] == 400
        assert "errors" in result["body"]

def test_get_batch_status_success():
    app = make_app()
    repo: HospitalBatchRepository = app.extensions[EXT_BATCH_REPOSITORY]
    batch = {
        "id": "b1",
        "total_hospitals": 2,
        "processed_hospitals": 0,
        "failed_hospitals": 0,
        "start_time": 0.0,
        "end_time": 0.0,
        "batch_activated": False,
        "hospitals": {
            "1": {"id": "1", "name": "A", "address": "addr", "status": "created"},
            "2": {"id": "2", "name": "B", "address": "addr", "status": "failed"},
        },
    }
    with app.app_context():
        repo.save(batch)
        result = app.extensions[EXT_BATCH_SERVICE].get_batch_status("b1")
        assert result["ok"] is True
        body = result["body"]
        assert body[KEY_TOTAL_HOSPITALS] == 2
        assert body["processed_hospitals"] == 1
        assert body["failed_hospitals"] == 1

def test_get_batch_status_not_found():
    app = make_app()
    with app.app_context():
        result = app.extensions[EXT_BATCH_SERVICE].get_batch_status("missing")
        assert result["ok"] is False
        assert result["status"] == 404


def test_resume_batch_completed_conflict():
    app = make_app()
    repo: HospitalBatchRepository = app.extensions[EXT_BATCH_REPOSITORY]
    batch = {
        "id": "b1",
        "total_hospitals": 2,
        "hospitals": {
            "1": {"id": "1", "name": "A", "status": "created"},
            "2": {"id": "2", "name": "B", "status": "activated"},
        },
    }
    with app.app_context():
        repo.save(batch)
        result = app.extensions[EXT_BATCH_SERVICE].resume_batch("b1")
        assert result["ok"] is False
        assert result["status"] == 409


def test_resume_batch_schedules_processing():
    app = make_app()
    repo: HospitalBatchRepository = app.extensions[EXT_BATCH_REPOSITORY]
    batch = {
        "id": "b1",
        "total_hospitals": 3,
        "hospitals": {
            "1": {"id": "1", "name": "A", "status": "created"},
            "2": {"id": "2", "name": "B", "status": "failed"},
            "3": {"id": "3", "name": "C", "status": "pending"},
        },
    }
    with app.app_context():
        repo.save(batch)
        result = app.extensions[EXT_BATCH_SERVICE].resume_batch("b1")
        assert result["ok"] is True
        assert result["status"] == 202
        assert result["body"]["scheduled"] == 2  


