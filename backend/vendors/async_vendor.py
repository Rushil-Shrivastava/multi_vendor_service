import asyncio, httpx, os
from fastapi import FastAPI
from pydantic import BaseModel
from typing import Dict, Any

API_URL = os.getenv("API_URL", "http://api:5000")  # service name 'api'

app = FastAPI()

class VendorReq(BaseModel):
    request_id: str
    payload: Dict[str, Any]

@app.post("/data", status_code=202)
async def submit(body: VendorReq):
    asyncio.create_task(process(body))
    return {"status": "accepted", "request_id": body.request_id}

async def process(body: VendorReq):
    await asyncio.sleep(2)                     # simulate work
    async with httpx.AsyncClient() as client:
        await client.post(f"{API_URL}/vendor-webhook/async",
                          json={"request_id": body.request_id,
                                "result": {
                                    "original_payload": body.payload,
                                    "vendor_msg": "Hello from FastAPI AsyncVendor"
                                }})
