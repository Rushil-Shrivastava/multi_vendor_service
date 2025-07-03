from fastapi import FastAPI
from pydantic import BaseModel
from typing import Dict, Any

app = FastAPI()

class VendorReq(BaseModel):
    request_id: str
    payload: Dict[str, Any]

@app.post("/data")
def get_data(body: VendorReq):
    return {"result": {
        "original_payload": body.payload,
        "vendor_msg": "Hello from FastAPI SyncVendor"
    }}
