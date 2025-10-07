from app.services.validation_service import HospitalCsvValidator


def test_validate_and_parse_success_with_optional_phone():
    v = HospitalCsvValidator()
    csv_text = "name,address,phone\nA,addr,1234567890\nB,addr,\n"
    result = v.validate_and_parse(csv_text)
    assert result["valid"] is True
    assert result["row_count"] == 2
    hospitals = result.get("hospitals", [])
    assert len(hospitals) == 2
    row1, h1 = hospitals[0]
    assert row1 == 1 and h1["name"] == "A" and h1["phone"] == "1234567890"
    row2, h2 = hospitals[1]
    assert row2 == 2 and h2["name"] == "B" and "phone" not in h2


def test_validate_and_parse_header_error():
    v = HospitalCsvValidator()
    csv_text = "bad,header\nA\n"
    result = v.validate_and_parse(csv_text)
    assert result["valid"] is False
    assert result.get("errors")


def test_validate_rows_phone_format():
    v = HospitalCsvValidator()
    csv_text = "name,address,phone\nA,addr,123\n"
    result = v.validate_and_parse(csv_text)
    assert result["valid"] is True

