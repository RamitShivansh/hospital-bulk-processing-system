import pytest

from app.utils.converter import BatchDtoConverter
from app.constants import (
    KEY_TOTAL_HOSPITALS,
    KEY_PROCESSED_COUNT,
    KEY_FAILED_COUNT,
    KEY_HOSPITALS,
)


def test_build_initial_batch_basic():
    hospitals = [
        (1, {"name": "A", "address": "addrA", "phone": "1234567890"}),
        (2, {"name": "B", "address": "addrB"}), 
    ]

    batch_id = "b-123"
    batch = BatchDtoConverter.build_initial_batch(batch_id, hospitals)

    assert batch["id"] == batch_id
    assert batch["total_hospitals"] == 2
    assert batch["processed_hospitals"] == 0
    assert batch["failed_hospitals"] == 0
    assert batch["batch_activated"] is False

    assert set(batch["hospitals"].keys()) == {"1", "2"}
    h1 = batch["hospitals"]["1"]
    h2 = batch["hospitals"]["2"]

    assert h1["id"] == "1"
    assert h1["status"] == "pending"
    assert h1["name"] == "A" and h1["address"] == "addrA"
    assert h1["phone"] == "1234567890"

    assert h2["id"] == "2"
    assert h2["status"] == "pending"
    assert h2["name"] == "B" and h2["address"] == "addrB"
    assert "phone" not in h2  


def test_to_status_dto_counts_and_sorting():
    batch = {
        "id": "b1",
        "total_hospitals": 3,
        "hospitals": {
            "2": {"id": "2", "name": "B", "status": "failed", "error": "x"},
            "10": {"id": "10", "name": "C", "status": "created", "hospital_id": "api-10"},
            "1": {"id": "1", "name": "A", "status": "pending"},
        },
    }

    dto = BatchDtoConverter.to_status_dto(batch)

    assert dto[KEY_TOTAL_HOSPITALS] == 3
    assert dto[KEY_PROCESSED_COUNT] == 1 
    assert dto[KEY_FAILED_COUNT] == 1  

    hospitals = dto[KEY_HOSPITALS]
    assert [h["row"] for h in hospitals] == [1, 2, 10]

    h2 = next(h for h in hospitals if h["row"] == 2)
    assert h2.get("error") == "x"
    h10 = next(h for h in hospitals if h["row"] == 10)
    assert h10.get("hospital_id") == "api-10"


