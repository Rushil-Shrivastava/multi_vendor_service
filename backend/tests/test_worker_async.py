"""
Simulate async vendor: worker triggers call, job remains 'processing',
then we hit the webhook and job becomes 'complete'.
"""
import pytest, asyncio
from backend import worker, main
from httpx import AsyncClient

@pytest.mark.asyncio
async def test_async_vendor_full_cycle(monkeypatch):
    req_id = "async-job-9"
    await main.jobs.insert_one({
        "_id": req_id,
        "status": "pending",
        "vendor": "async",
        "payload": {"foo": "bar"}
    })

    # --- patch the outgoing HTTP call to async vendor
    async def fake_post(url, json, timeout):
        # imitate 202 Accepted
        return type("Resp", (), {"status_code": 202})
    monkeypatch.setattr(worker.requests, "post", fake_post)

    # run worker (should leave job in 'processing')
    await worker.process_job({"request_id": req_id,
                              "vendor": "async",
                              "payload": {"foo": "bar"}})
    doc = await main.jobs.find_one({"_id": req_id})
    assert doc["status"] == "processing"

    # --- now simulate vendor webhook callback via API
    async with AsyncClient(app=main.app, base_url="http://test") as ac:
        resp = await ac.post("/vendor-webhook/async",
                             json={"request_id": req_id,
                                   "result": {"note": " done ", "phone": "123"}})
        assert resp.status_code == 200

    # job should now be complete & cleaned
    doc = await main.jobs.find_one({"_id": req_id})
    assert doc["status"] == "complete"
    assert doc["result"]["note"] == "done"
    assert doc["result"]["phone"] is None
