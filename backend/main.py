import uuid, os, json, asyncio
from datetime import datetime, timezone
from typing import Any, Dict, Optional

from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
from kafka import KafkaProducer
from motor.motor_asyncio import AsyncIOMotorClient 

MONGO_URI = os.getenv("MONGO_URI", "mongodb://mongo:27017/")
KAFKA_BOOTSTRAP = os.getenv("KAFKA_BOOTSTRAP_SERVERS", "kafka:9092")

app = FastAPI(title="Multi-Vendor Data Fetch API")
mongo = AsyncIOMotorClient(MONGO_URI)
db = mongo["multivendor"]
jobs = db["jobs"]
producer = KafkaProducer(bootstrap_servers=[KAFKA_BOOTSTRAP])

# ───────────────────────── Schemas ──────────────────────────
class JobIn(BaseModel):
    vendor: str = Field(..., pattern="^(sync|async)$")
    data: Optional[Dict[str, Any]] = None

class JobOut(BaseModel):
    request_id: str

class JobStatus(BaseModel):
    status: str
    result: Optional[Dict[str, Any]] = None

# ───────────────────────── Endpoints ─────────────────────────
@app.post("/jobs", response_model=JobOut, status_code=202)
async def create_job(payload: JobIn):
    request_id = str(uuid.uuid4())

    await jobs.insert_one({
        "_id": request_id,
        "status": "pending",
        "vendor": payload.vendor,
        "payload": payload.data or {},
        "created_at": datetime.now(timezone.utc)
    })

    producer.send("jobs", json.dumps({
        "request_id": request_id,
        "vendor": payload.vendor,
        "payload": payload.data or {}
    }).encode("utf-8"))
    producer.flush()

    return {"request_id": request_id}

@app.get("/jobs/{request_id}", response_model=JobStatus)
async def get_job(request_id: str):
    doc = await jobs.find_one({"_id": request_id})
    if not doc:
        raise HTTPException(404, "Job not found")
    if doc["status"] != "complete":
        return {"status": doc["status"]}
    return {"status": "complete", "result": doc["result"]}

@app.post("/vendor-webhook/{vendor}", status_code=200)
async def vendor_webhook(vendor: str, body: Dict[str, Any], bt: BackgroundTasks):
    req_id = body.get("request_id")
    result = body.get("result")
    if not req_id or result is None:
        raise HTTPException(400, "Invalid callback payload")

    # defer the cleaning (saves 1 RTT)
    from utils.cleaner import clean_data
    async def _clean_and_store():
        cleaned = clean_data(result)
        await jobs.update_one({"_id": req_id},
                              {"$set": {"status": "complete",
                                        "result": cleaned,
                                        "completed_at": datetime.now(timezone.utc)}})

    bt.add_task(_clean_and_store)
    return {"status": "received"}
