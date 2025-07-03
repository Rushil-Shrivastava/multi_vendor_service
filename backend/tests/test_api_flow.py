"""
Happy-path API test (sync vendor).  We don't run the real worker here;
we only assert that /jobs inserts a pending doc and returns 202.
"""
import pytest, uuid, json, asyncio
from backend import main

@pytest.mark.asyncio
async def test_create_job_returns_uuid_and_persists(client):
    payload = {"vendor": "sync", "data": {"foo": "bar"}}
    resp = await client.post("/jobs", json=payload)

    assert resp.status_code == 202
    body = resp.json()
    assert "request_id" in body

    # UUID sanity check
    uuid.UUID(body["request_id"])

    # Document exists in Mongo and is pending
    doc = await main.jobs.find_one({"_id": body["request_id"]})
    assert doc is not None
    assert doc["status"] == "pending"

@pytest.mark.asyncio
async def test_get_unknown_job(client):
    resp = await client.get("/jobs/does-not-exist")
    assert resp.status_code == 404
