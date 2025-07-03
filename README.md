# Multi-Vendor Data Fetch Service

A tiny demo platform that hides vendor quirks (sync vs async, rate-limits) behind one clean API.

---

## Quick start (90 s)

```bash
git clone <your-repo>.git
cd multi_vendor_service
docker compose up --build -d           # API @ :5000, Swagger @ /docs
# smoke test
curl -X POST localhost:5000/jobs -H 'Content-Type: application/json' \
     -d '{"vendor":"sync","data":{"foo":"bar"}}'
