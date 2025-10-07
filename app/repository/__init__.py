from typing import runtime_checkable, Protocol, List, Tuple, Dict, Any, Optional, TypedDict

__all__ = ["HospitalBatchRepository"]



class Hospital(TypedDict):
    id: str
    name: str
    address: str
    phone: str
    status: str

class Batch(TypedDict):
    id: str
    total_hospitals: int
    processed_hospitals: int
    failed_hospitals: int
    start_time: float
    end_time: float
    batch_activated: bool
    hospitals: Dict[str, Hospital]