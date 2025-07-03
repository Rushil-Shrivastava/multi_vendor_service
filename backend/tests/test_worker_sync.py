"""
Unit-test the worker processing a sync vendor job.
Vendor HTTP call is monkey-patched to avoid real network traffic.
"""
import pytest, asyncio
from types import SimpleNamespace
from backend import worker, main
from backend.utils.cleaner import clean_data

class DummyResp:
    def __init__(self, data, status=200):
        self._data = data
        self.status_code = status
    def json(self):
        return self._data

@pytest.mark.asyncio
async def test_worker_processes_sync(monkeypatch):
    req_id = "test-sync-42"
    await main.jobs.insert_one({
        "_id": req_id,
        "status": "pending",
        "vendor": "sync",
        "payload": {"x": 1}
    })

    # ── stub requests.post so no real HTTP call happens ── #
    def fake_post(url, json, timeout):
        assert "vendor_sync" in url
        return DummyResp({"result": {"greeting": "hi", "email": "user@test"}})

    monkeypatch.setattr(worker.requests, "post", fake_post)

    # process the job
    await worker.process_job({
        "request_id": req_id,
        "vendor": "sync",
        "payload": {"x": 1}
    })

    # verify DB state
    doc = await main.jobs.find_one({"_id": req_id})
    assert doc["status"] == "complete"
    assert doc["result"] == clean_data({"greeting": "hi", "email": "user@test"})
