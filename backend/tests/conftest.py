"""
Shared pytest fixtures.

• Wraps FastAPI in httpx.AsyncClient for async tests
• Clears Mongo collection before / after each test
• Replaces the real Kafka producer with a no-op stub
"""
import asyncio
import os
import pytest
from httpx import AsyncClient
from types import SimpleNamespace

from backend import main  # <-- FastAPI service lives here

# ------------------------------------------------------------------ #
# Async event-loop fixture (needed by pytest-asyncio < 0.21 on Py ≤3.12)
# ------------------------------------------------------------------ #
@pytest.fixture(scope="session")
def event_loop():
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()

# ------------------------------------------------------------------ #
# Async FastAPI client
# ------------------------------------------------------------------ #
@pytest.fixture()
async def client():
    async with AsyncClient(app=main.app, base_url="http://test") as ac:
        yield ac

# ------------------------------------------------------------------ #
# Clean the jobs collection between tests
# ------------------------------------------------------------------ #
@pytest.fixture(autouse=True)
async def clear_jobs():
    await main.jobs.delete_many({})
    yield
    await main.jobs.delete_many({})

# ------------------------------------------------------------------ #
# Monkey-patch Kafka producer so tests don't need a broker
# ------------------------------------------------------------------ #
@pytest.fixture(autouse=True)
def stub_kafka(monkeypatch):
    stub = SimpleNamespace(send=lambda *a, **kw: None, flush=lambda: None)
    monkeypatch.setattr(main, "producer", stub)
