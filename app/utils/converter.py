from typing import Dict, Any, List, Tuple

import time
from ..constants import (
    STATUS_CREATED,
    STATUS_FAILED,
    STATUS_PROCESSING,
    STATUS_ACTIVATED,
    STATUS_CREATED_AND_ACTIVATED,
    KEY_STATUS,
    KEY_TOTAL_HOSPITALS,
    KEY_PROCESSED_COUNT,
    KEY_FAILED_COUNT,
    KEY_HOSPITALS,
    KEY_BATCH_ACTIVATED,
    KEY_PROCESSING_TIME_SECONDS,
)


class BatchDtoConverter:
    @staticmethod
    def build_initial_batch(batch_id: str, hospitals: List[Tuple[int, Dict[str, Any]]]) -> Dict[str, Any]:
        hospital_count = len(hospitals)
        hospitals_map: Dict[str, Dict[str, Any]] = {}
        for row_number, data in hospitals:
            hospital_id = str(row_number)
            hospital_entry: Dict[str, Any] = {
                "id": hospital_id,
                "status": "pending",
            }
            hospital_entry.update(data)
            hospitals_map[hospital_id] = hospital_entry

        now = time.time()
        return {
            "id": batch_id,
            "total_hospitals": hospital_count,
            "processed_hospitals": 0,
            "failed_hospitals": 0,
            "start_time": now,
            "end_time": 0.0,
            "batch_activated": False,
            "hospitals": hospitals_map,
        }

    @staticmethod
    def to_status_dto(batch: Dict[str, Any]) -> Dict[str, Any]:
        hospitals_dict: Dict[str, Dict[str, Any]] = batch.get("hospitals", {})
        total = batch.get("total_hospitals", len(hospitals_dict))
        processed = 0
        failed = 0

        hospitals_list: List[Dict[str, Any]] = []
        for hospital_id, hospital in hospitals_dict.items():
            status = hospital.get("status")
            if status == STATUS_CREATED:
                processed += 1
            elif status == STATUS_FAILED:
                failed += 1

            entry: Dict[str, Any] = {
                "row": int(hospital_id) if str(hospital_id).isdigit() else hospital_id,
                "name": hospital.get("name"),
                "status": STATUS_CREATED_AND_ACTIVATED if status == STATUS_ACTIVATED else status,
            }
            if hospital.get("hospital_id") is not None:
                entry["hospital_id"] = hospital.get("hospital_id")
            if hospital.get("error"):
                entry["error"] = hospital.get("error")
            hospitals_list.append(entry)

        try:
            hospitals_list.sort(key=lambda x: int(x["row"]))
        except Exception:
            hospitals_list.sort(key=lambda x: str(x["row"]))

        start_time = float(batch.get("start_time", 0.0) or 0.0)
        end_time = float(batch.get("end_time", 0.0) or 0.0)
        is_done = total > 0 and (processed + failed) >= total
        if start_time > 0.0:
            if is_done and end_time > start_time:
                processing_time_seconds = end_time - start_time
            else:
                processing_time_seconds = max(0.0, time.time() - start_time)
        else:
            processing_time_seconds = 0.0

        return {
            "batch_id": batch.get("id"),
            KEY_TOTAL_HOSPITALS: total,
            KEY_PROCESSED_COUNT: processed,
            KEY_FAILED_COUNT: failed,
            KEY_PROCESSING_TIME_SECONDS: processing_time_seconds,
            KEY_BATCH_ACTIVATED: bool(batch.get("batch_activated", False)),
            KEY_HOSPITALS: hospitals_list,
        }


