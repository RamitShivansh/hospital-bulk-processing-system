import json
from types import SimpleNamespace

from app.services.hospital_api_client import HospitalApiClient


class DummyResponse:
    def __init__(self, status_code=200, json_data=None, text=""):
        self.status_code = status_code
        self._json = json_data or {}
        self.text = text

    def json(self):
        return self._json


class DummySession:
    def __init__(self):
        self.last = SimpleNamespace(method=None, url=None, json=None)

    def post(self, url, json):
        self.last = SimpleNamespace(method="POST", url=url, json=json)
        return DummyResponse(200, {"id": "api-1"})

    def patch(self, url):
        self.last = SimpleNamespace(method="PATCH", url=url, json=None)
        return DummyResponse(200, {"activated_hospitals": ["x"]})

    def get(self, url):
        self.last = SimpleNamespace(method="GET", url=url, json=None)
        return DummyResponse(200, [{"id": "api-1"}])

    def delete(self, url):
        self.last = SimpleNamespace(method="DELETE", url=url, json=None)
        return DummyResponse(200, {"deleted_count": 1})


def test_create_hospital_success():
    client = HospitalApiClient(base_url="http://x", session=DummySession())
    resp = client.create_hospital({"name": "A", "address": "addr"}, "b1")
    assert resp["id"] == "api-1"


def test_activate_batch_success():
    client = HospitalApiClient(base_url="http://x", session=DummySession())
    resp = client.activate_batch("b1")
    assert "activated_hospitals" in resp


def test_get_hospitals_by_batch_success():
    client = HospitalApiClient(base_url="http://x", session=DummySession())
    resp = client.get_hospitals_by_batch("b1")
    assert isinstance(resp, list) and resp


def test_delete_batch_success():
    client = HospitalApiClient(base_url="http://x", session=DummySession())
    resp = client.delete_batch("b1")
    assert resp.get("deleted_count") == 1

