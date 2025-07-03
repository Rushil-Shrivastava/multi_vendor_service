import time, json, requests, sys, os, logging
from kafka import KafkaConsumer
from pymongo import MongoClient
from datetime import datetime, timezone
from utils.cleaner import clean_data
from utils.rate_limit import RateLimiter

# ---------- NEW: logging config ----------
logging.basicConfig(
    level=logging.INFO,
    stream=sys.stdout,          # send to container stdout
    force=True,                 # override any default config
    format="%(asctime)s | %(levelname)s | %(message)s",
)
log = logging.getLogger(__name__)
# -----------------------------------------

# Initialize Mongo and Kafka consumer
mongo_client = MongoClient("mongodb://mongo:27017/")
db = mongo_client["multivendor"]
jobs_coll = db["jobs"]

consumer = KafkaConsumer(
    "jobs",
    bootstrap_servers=["kafka:9092"],
    group_id="job-workers",
    auto_offset_reset="earliest"
)

rate_limiter = RateLimiter(rates={"sync": 5, "async": 2})

for message in consumer:
    try:
        job = json.loads(message.value.decode())
        req_id  = job["request_id"]
        vendor  = job["vendor"]
        payload = job.get("payload", {})

        # --- log start ---
        log.info(f"processing {req_id}  vendor={vendor}")

        jobs_coll.update_one(
            {"_id": req_id},
            {"$set": {"status": "processing",
                      "started_at": datetime.now(timezone.utc)}}
        )

        rate_limiter.wait_for_slot(vendor)

        if vendor == "sync":
            resp = requests.post(
                "http://vendor_sync:5000/data",
                json={"request_id": req_id, "payload": payload},
                timeout=5
            )
            if resp.status_code == 200:
                cleaned = clean_data(resp.json().get("result"))
                jobs_coll.update_one(
                    {"_id": req_id},
                    {"$set": {"status": "complete",
                              "result": cleaned,
                              "completed_at": datetime.now(timezone.utc)}}
                )
                log.info(f"complete    {req_id}")
            else:
                jobs_coll.update_one(
                    {"_id": req_id},
                    {"$set": {"status": "failed",
                              "error": f"Vendor error {resp.status_code}"}}
                )
                log.warning(f"failed      {req_id}  status={resp.status_code}")

        elif vendor == "async":
            requests.post(
                "http://vendor_async:5000/data",
                json={"request_id": req_id, "payload": payload},
                timeout=5
            )
            log.info(f"awaiting_cb  {req_id}")   # wait for webhook

        else:
            jobs_coll.update_one(
                {"_id": req_id},
                {"$set": {"status": "failed",
                          "error": "Unknown vendor"}}
            )
            log.warning(f"failed      {req_id}  unknown vendor")

    except Exception as e:
        jobs_coll.update_one(
            {"_id": req_id},
            {"$set": {"status": "failed", "error": str(e)}}
        )
        log.exception(f"failed      {req_id}  exception")
