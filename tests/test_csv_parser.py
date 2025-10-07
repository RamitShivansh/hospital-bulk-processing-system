from app.utils.csv_parser import CsvHospitalParser


def test_csv_parser_basic_and_optional_phone():
    parser = CsvHospitalParser()
    csv_text = "name,address,phone\nA,addr,1234567890\nB,addr,\n"
    hospitals = parser.parse_hospitals(csv_text)
    assert len(hospitals) == 2
    row1, h1 = hospitals[0]
    assert row1 == 1 and h1["name"] == "A" and h1["phone"] == "1234567890"
    row2, h2 = hospitals[1]
    assert row2 == 2 and h2["name"] == "B" and "phone" not in h2


def test_csv_parser_ignores_rows_with_few_columns():
    parser = CsvHospitalParser()
    csv_text = "name,address\nonlyname\nA,addr\n"
    hospitals = parser.parse_hospitals(csv_text)
    assert len(hospitals) == 1
    assert hospitals[0][1]["name"] == "A"

