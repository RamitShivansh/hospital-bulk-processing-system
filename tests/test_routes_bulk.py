import io
import json

import pytest

from app import create_app
from app.constants import EXT_BATCH_REPOSITORY, EXT_BATCH_SERVICE, KEY_TOTAL_HOSPITALS


def test_post_bulk_success(monkeypatch):
    app = create_app()
    client = app.test_client()

    data = {
        'file': (io.BytesIO(b"name,address,phone\nA,addr,1234567890\nB,addr,\n"), 'h.csv')
    }

    resp = client.post('/api/v1/hospitals/bulk', data=data, content_type='multipart/form-data')
    assert resp.status_code == 202
    body = resp.get_json()
    assert 'batch_id' in body
    assert body['total_hospitals'] == 2
    assert 'processed_hospitals' in body and body['processed_hospitals'] == 0
    assert 'failed_hospitals' in body and body['failed_hospitals'] == 0
    assert 'processing_time_seconds' in body
    assert 'batch_activated' in body
    assert 'hospitals' in body and isinstance(body['hospitals'], list)


def test_post_bulk_bad_file(monkeypatch):
    app = create_app()
    client = app.test_client()

    data = {
        'file': (io.BytesIO(b"bad,header\nA\n"), 'h.csv')
    }
    resp = client.post('/api/v1/hospitals/bulk', data=data, content_type='multipart/form-data')
    assert resp.status_code == 400
    body = resp.get_json()
    assert 'errors' in body or 'error' in body


def test_post_bulk_zero_rows_returns_400():
    app = create_app()
    client = app.test_client()

    # Valid header, but no data rows
    data = {
        'file': (io.BytesIO(b"name,address,phone\n"), 'h.csv')
    }
    resp = client.post('/api/v1/hospitals/bulk', data=data, content_type='multipart/form-data')
    assert resp.status_code == 400
    body = resp.get_json()
    assert 'errors' in body or 'error' in body


def test_get_status_success():
    app = create_app()
    client = app.test_client()

    data = {
        'file': (io.BytesIO(b"name,address\nA,addr\nB,addr\n"), 'h.csv')
    }
    resp = client.post('/api/v1/hospitals/bulk', data=data, content_type='multipart/form-data')
    assert resp.status_code == 202
    batch_id = resp.get_json()['batch_id']

    status_resp = client.get(f'/api/v1/hospitals/batch/{batch_id}/status')
    assert status_resp.status_code == 200
    body = status_resp.get_json()
    assert KEY_TOTAL_HOSPITALS in body
    assert 'processed_hospitals' in body
    assert 'failed_hospitals' in body
    assert 'hospitals' in body


def test_get_status_not_found():
    app = create_app()
    client = app.test_client()

    status_resp = client.get('/api/v1/hospitals/batch/missing/status')
    assert status_resp.status_code == 404


def test_post_resume_completed_conflict(monkeypatch):
    app = create_app()
    client = app.test_client()

    with app.app_context():
        repo = app.extensions[EXT_BATCH_REPOSITORY]
        batch = {
            "id": "b9",
            "total_hospitals": 2,
            "hospitals": {
                "1": {"id": "1", "name": "A", "status": "created"},
                "2": {"id": "2", "name": "B", "status": "activated"},
            },
        }
        repo.save(batch)

    resp = client.patch('/api/v1/hospitals/batch/b9/resume')
    assert resp.status_code == 409



