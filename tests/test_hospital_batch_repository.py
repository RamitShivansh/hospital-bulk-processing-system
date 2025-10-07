import threading
from typing import Dict

import pytest

from app.repository.hospital_batch_repository import HospitalBatchRepository


def _make_batch(num_hospitals: int) -> Dict:
    hospitals: Dict[str, Dict] = {}
    for i in range(num_hospitals):
        hid = f"h{i+1}"
        hospitals[hid] = {
            "id": hid,
            "name": f"Hospital {i+1}",
            "address": f"{i+1} Main St",
            "phone": f"555-000{i+1}",
            "status": "pending",
        }
    return {
        "total_hospitals": num_hospitals,
        "processed_hospitals": 0,
        "failed_hospitals": 0,
        "start_time": 0.0,
        "end_time": 0.0,
        "batch_activated": False,
        "hospitals": hospitals,
    }


def test_save_and_find_by_id_roundtrip():
    repo = HospitalBatchRepository()
    batch = _make_batch(3)

    saved = repo.save(batch)
    assert "id" in saved and saved["id"], "save should assign an id"

    fetched = repo.find_by_batch_id(saved["id"])
    assert fetched == repo.find_by_batch_id(saved["id"]) 
    assert fetched["total_hospitals"] == 3
    assert set(fetched["hospitals"].keys()) == {"h1", "h2", "h3"}


def test_update_hospital_status_single_thread():
    repo = HospitalBatchRepository()
    batch = repo.save(_make_batch(1))
    batch_id = batch["id"]

    repo.update_hospital_status(batch_id, "h1", "processing")
    assert repo.find_by_batch_id(batch_id)["hospitals"]["h1"]["status"] == "processing"

    repo.update_hospital_status(batch_id, "h1", "done")
    assert repo.find_by_batch_id(batch_id)["hospitals"]["h1"]["status"] == "done"


def test_concurrent_updates_different_hospitals():
    repo = HospitalBatchRepository()
    batch = repo.save(_make_batch(10))
    batch_id = batch["id"]

    n_threads = 10
    barrier = threading.Barrier(n_threads)
    threads = []

    def worker(idx: int):
        hid = f"h{idx+1}"
        status = f"processing-{idx+1}"
        barrier.wait()
        repo.update_hospital_status(batch_id, hid, status)

    for i in range(n_threads):
        t = threading.Thread(target=worker, args=(i,))
        t.start()
        threads.append(t)

    for t in threads:
        t.join()

    fetched = repo.find_by_batch_id(batch_id)
    for i in range(n_threads):
        hid = f"h{ i+1 }"
        assert fetched["hospitals"][hid]["status"] == f"processing-{i+1}"


def test_concurrent_updates_same_hospital_race():
    repo = HospitalBatchRepository()
    batch = repo.save(_make_batch(1))
    batch_id = batch["id"]

    statuses = [f"s{i}" for i in range(50)]
    barrier = threading.Barrier(len(statuses))
    threads = []

    def worker(status: str):
        barrier.wait()
        repo.update_hospital_status(batch_id, "h1", status)

    for s in statuses:
        t = threading.Thread(target=worker, args=(s,))
        t.start()
        threads.append(t)

    for t in threads:
        t.join()

    final_status = repo.find_by_batch_id(batch_id)["hospitals"]["h1"]["status"]
    assert final_status in set(statuses)



