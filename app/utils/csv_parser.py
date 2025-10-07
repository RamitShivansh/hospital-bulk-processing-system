import csv
import io
from typing import List, Tuple, Dict, Any


class CsvHospitalParser:
    """Parse hospitals from CSV text into a structured list.
    """

    def parse_hospitals(self, csv_text: str) -> List[Tuple[int, Dict[str, Any]]]:
        stream = io.StringIO(csv_text)
        reader = csv.reader(stream)

        try:
            next(reader)
        except StopIteration:
            return []

        hospitals: List[Tuple[int, Dict[str, Any]]] = []
        for row_index, row in enumerate(reader, start=1):
            if len(row) < 2:
                continue
            hospital: Dict[str, Any] = {
                "name": row[0],
                "address": row[1]
            }
            if len(row) > 2 and row[2]:
                hospital["phone"] = row[2]
            hospitals.append((row_index, hospital))

        return hospitals


