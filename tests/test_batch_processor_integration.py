import time
from flask import Flask

from app.services.batch_processor import BatchProcessor
from app.repository.hospital_batch_repository import HospitalBatchRepository
from app.services.hospital_api_client import HospitalApiClient


class DummyClient(HospitalApiClient):
    def __init__(self):
        pass

    def create_hospital(self, hospital_data, batch_id):
        return {"id": f"api-{hospital_data.get('name','x')}"}

    def activate_batch(self, batch_id):
        return {"activated_hospitals": ["h1", "h2"]}


def test_processor_processes_each_hospital():
    app = Flask(__name__)
    repo = HospitalBatchRepository()
    processor = BatchProcessor(client_factory=lambda: DummyClient(), repository=repo)

    batch = {
        "id": "b1",
        "total_hospitals": 2,
        "processed_hospitals": 0,
        "failed_hospitals": 0,
        "start_time": 0.0,
        "end_time": 0.0,
        "batch_activated": False,
        "hospitals": {
            "h1": {"id": "h1", "name": "A", "address": "addr", "status": "pending"},
            "h2": {"id": "h2", "name": "B", "address": "addr", "status": "pending"},
        },
    }
    with app.app_context():
        repo.save(batch)
        processor.start_batch("b1")

        fetched = repo.find_by_batch_id("b1")
        assert fetched["hospitals"]["h1"]["status"] in {"processing", "created", "failed", "activated"}
        assert fetched["hospitals"]["h2"]["status"] in {"processing", "created", "failed", "activated"}


