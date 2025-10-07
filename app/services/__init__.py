# Services package
from typing import Protocol, runtime_checkable, Dict, Any, List, Tuple, Optional


@runtime_checkable
class HospitalApiClientProtocol(Protocol):
    def create_hospital(self, hospital_data: Dict[str, Any], batch_id: str) -> Dict[str, Any]:
        ...

    def activate_batch(self, batch_id: str) -> Dict[str, Any]:
        ...

    def get_hospitals_by_batch(self, batch_id: str) -> List[Dict[str, Any]]:
        ...

    def delete_batch(self, batch_id: str) -> Dict[str, Any]:
        ...


class CsvParserProtocol(Protocol):
    def parse_hospitals(self, csv_text: str) -> List[Tuple[int, Dict[str, Any]]]:
        ...


 

