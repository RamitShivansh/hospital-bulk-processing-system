import io

from app import create_app


def test_validate_success():
    app = create_app()
    client = app.test_client()

    data = {
        'file': (io.BytesIO(b"name,address,phone\nA,addr,1234567890\nB,addr,\n"), 'h.csv')
    }
    resp = client.post('/api/v1/hospitals/validate', data=data, content_type='multipart/form-data')
    assert resp.status_code == 200
    body = resp.get_json()
    assert body['valid'] is True
    assert body['row_count'] == 2


def test_validate_bad_header():
    app = create_app()
    client = app.test_client()

    data = {
        'file': (io.BytesIO(b"bad,header\nA\n"), 'h.csv')
    }
    resp = client.post('/api/v1/hospitals/validate', data=data, content_type='multipart/form-data')
    assert resp.status_code == 200
    body = resp.get_json()
    assert body['valid'] is False
    assert 'errors' in body or 'error' in body


def test_validate_zero_rows():
    app = create_app()
    client = app.test_client()

    data = {
        'file': (io.BytesIO(b"name,address,phone\n"), 'h.csv')
    }
    resp = client.post('/api/v1/hospitals/validate', data=data, content_type='multipart/form-data')
    assert resp.status_code == 200
    body = resp.get_json()
    assert body['valid'] is False
    assert 'errors' in body or 'error' in body

