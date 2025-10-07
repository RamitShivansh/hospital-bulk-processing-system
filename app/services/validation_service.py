import csv
import io
from typing import Dict, Any, List, Tuple, Optional
from ..constants import (
    ERROR_NAME_REQUIRED,
    ERROR_ADDRESS_REQUIRED,
    ERROR_PHONE_INVALID,
    ERROR_ROW_FEW_COLUMNS,
    ERROR_MISSING_REQUIRED_COLUMNS,
    ERROR_CSV_MIN_COLUMNS,
    ERROR_EXPECTED_COLUMN_TEMPLATE,
    ERROR_CSV_EMPTY_HEADER,
    ERROR_CSV_INVALID_FORMAT_TEMPLATE,
    ERROR_CSV_INVALID_GENERIC,
    ERROR_MAX_HOSPITALS_EXCEEDED_TEMPLATE,
    ERROR_NO_HOSPITAL_ROWS,
)


class HospitalCsvValidator:
    """Validate hospital CSV structure and provide diagnostics.
    """

    REQUIRED_COLUMNS = ["name", "address"]
    OPTIONAL_COLUMNS = ["phone"]


    def _read_header(self, csv_text: str) -> Tuple[List[str], csv.reader]:
        """Read and return header and a reader positioned at first data row."""
        stream = io.StringIO(csv_text)
        reader = csv.reader(stream)
        header = next(reader)
        return header, reader

    def validate_header(self, csv_text: str) -> Dict[str, Any]:
        """Validate the CSV header for required/optional columns in order.

        Returns { valid, error?, header? }.
        """
        try:
            header, _ = self._read_header(csv_text)

            if len(header) < len(self.REQUIRED_COLUMNS):
                return {
                    "valid": False,
                    "error": ERROR_CSV_MIN_COLUMNS,
                }

            expected = self.REQUIRED_COLUMNS + self.OPTIONAL_COLUMNS
            for index, column in enumerate(header[: len(expected)]):
                if column.lower() != expected[index].lower():
                    return {
                        "valid": False,
                        "error": ERROR_EXPECTED_COLUMN_TEMPLATE.format(index=index+1, expected=expected[index], actual=column),
                    }

            return {
                "valid": True,
                "header": header,
            }
        except StopIteration:
            return {"valid": False, "error": ERROR_CSV_EMPTY_HEADER}
        except Exception as e:
            return {"valid": False, "error": ERROR_CSV_INVALID_FORMAT_TEMPLATE.format(error=str(e))}

    def validate_rows(self, csv_text: str) -> Dict[str, Any]:
        """Validate data rows for required fields and phone format.

        - name and address must be present and non-empty
        - phone (if provided) must be exactly 10 digits

        Returns { valid, errors: [ { row, error } ], row_count }.
        """
        try:
            header, reader = self._read_header(csv_text)
            errors: List[Dict[str, Any]] = []

            lower_header = [h.lower() for h in header]
            try:
                name_idx = lower_header.index("name")
                address_idx = lower_header.index("address")
            except ValueError:
                return {
                    "valid": False,
                    "errors": [{"row": 0, "error": ERROR_MISSING_REQUIRED_COLUMNS}],
                    "row_count": 0,
                }
            phone_idx: Optional[int] = lower_header.index("phone") if "phone" in lower_header else None

            row_count = 0
            for row_number, row in enumerate(reader, start=1):
                row_count += 1
                row_errors: List[str] = []

                if len(row) <= address_idx:
                    row_errors.append(ERROR_ROW_FEW_COLUMNS)
                else:
                    name_error = self.validate_name(row[name_idx])
                    if name_error:
                        row_errors.append(name_error)

                    address_error = self.validate_address(row[address_idx])
                    if address_error:
                        row_errors.append(address_error)

                if row_errors:
                    errors.append({"row": row_number, "error": "; ".join(row_errors)})

            is_valid = len(errors) == 0 and row_count > 0
            if row_count == 0:
                errors.append({"row": 0, "error": ERROR_NO_HOSPITAL_ROWS})
            return {
                "valid": is_valid,
                "errors": errors,
                "row_count": row_count,
            }
        except StopIteration:
            return {"valid": True, "errors": [], "row_count": 0}
        except Exception as e:
            return {"valid": False, "errors": [{"row": 0, "error": str(e)}]}

    def validate_all(self, csv_text: str, max_hospitals: Optional[int] = None) -> Dict[str, Any]:
        """Run both header and row validations and combine results."""
        header_result = self.validate_header(csv_text)
        if not header_result.get("valid"):
            return {
                "valid": False,
                "errors": [{"row": 0, "error": header_result.get("error", "Invalid header")}],
                "header": header_result.get("header"),
                "row_count": 0,
            }

        rows_result = self.validate_rows(csv_text)
        combined = {
            "valid": rows_result.get("valid", False),
            "errors": rows_result.get("errors", []),
            "header": header_result.get("header"),
            "row_count": rows_result.get("row_count", 0),
        }
        if combined["valid"] and combined.get("row_count", 0) == 0:
            combined["valid"] = False
            combined.setdefault("errors", []).append({"row": 0, "error": ERROR_NO_HOSPITAL_ROWS})
        if combined["valid"] and max_hospitals is not None:
            count = combined.get("row_count", 0)
            if count > max_hospitals:
                combined["valid"] = False
                combined.setdefault("errors", []).append({
                    "row": 0,
                    "error": ERROR_MAX_HOSPITALS_EXCEEDED_TEMPLATE.format(count=count, max_allowed=max_hospitals),
                })
        return combined

    def validate_and_parse(self, csv_text: str, max_hospitals: Optional[int] = None) -> Dict[str, Any]:
        """Single-pass validation that also parses hospitals on success.

        Returns { valid, errors, row_count, header, hospitals? }.
        When valid is True, 'hospitals' is a list of (row_number, hospital_dict).
        """
        try:
            header, reader = self._read_header(csv_text)
        except StopIteration:
            return {"valid": False, "errors": [{"row": 0, "error": ERROR_CSV_EMPTY_HEADER}], "row_count": 0}
        except Exception as e:
            return {"valid": False, "errors": [{"row": 0, "error": ERROR_CSV_INVALID_FORMAT_TEMPLATE.format(error=str(e))}], "row_count": 0}

        header_check = self.validate_header(csv_text)
        if not header_check.get("valid"):
            return {
                "valid": False,
                "errors": [{"row": 0, "error": header_check.get("error")}],
                "row_count": 0,
                "header": header_check.get("header"),
            }

        lower_header = [h.lower() for h in header]
        try:
            name_idx = lower_header.index("name")
            address_idx = lower_header.index("address")
        except ValueError:
            return {
                "valid": False,
                "errors": [{"row": 0, "error": ERROR_MISSING_REQUIRED_COLUMNS}],
                "row_count": 0,
                "header": header,
            }
        phone_idx: Optional[int] = lower_header.index("phone") if "phone" in lower_header else None

        errors: List[Dict[str, Any]] = []
        hospitals: List[Tuple[int, Dict[str, Any]]] = []
        row_count = 0
        for row_number, row in enumerate(reader, start=1):
            row_count += 1
            row_errors: List[str] = []

            if len(row) <= address_idx:
                row_errors.append(ERROR_ROW_FEW_COLUMNS)
            else:
                name_error = self.validate_name(row[name_idx])
                if name_error:
                    row_errors.append(name_error)

                address_error = self.validate_address(row[address_idx])
                if address_error:
                    row_errors.append(address_error)

            if row_errors:
                errors.append({"row": row_number, "error": "; ".join(row_errors)})
            else:
                hospital: Dict[str, Any] = {
                    "name": row[name_idx].strip(),
                    "address": row[address_idx].strip(),
                }
                if phone_idx is not None and len(row) > phone_idx and row[phone_idx].strip():
                    hospital["phone"] = row[phone_idx].strip()
                hospitals.append((row_number, hospital))

        result: Dict[str, Any] = {
            "valid": len(errors) == 0 and row_count > 0,
            "errors": errors,
            "row_count": row_count,
            "header": header,
        }
        if row_count == 0:
            result.setdefault("errors", []).append({"row": 0, "error": ERROR_NO_HOSPITAL_ROWS})

        if result["valid"] and max_hospitals is not None and row_count > max_hospitals:
            result["valid"] = False
            result.setdefault("errors", []).append({
                "row": 0,
                "error": ERROR_MAX_HOSPITALS_EXCEEDED_TEMPLATE.format(count=row_count, max_allowed=max_hospitals),
            })

        if result["valid"]:
            result["hospitals"] = hospitals

        return result

    def validate_text(self, csv_text: str) -> Dict[str, Any]:
        result = self.validate_all(csv_text)
        if result.get("valid"):
            return {
                "valid": True,
                "row_count": result.get("row_count", 0),
                "header": result.get("header"),
            }
        errors = result.get("errors", [])
        top_error = errors[0]["error"] if errors else ERROR_CSV_INVALID_GENERIC
        return {"valid": False, "error": top_error}

    def validate_name(self, name_value: str) -> Optional[str]:
        value = name_value.strip() if name_value is not None else ""
        if not value:
            return ERROR_NAME_REQUIRED
        return None

    def validate_address(self, address_value: str) -> Optional[str]:
        value = address_value.strip() if address_value is not None else ""
        if not value:
            return ERROR_ADDRESS_REQUIRED
        return None

