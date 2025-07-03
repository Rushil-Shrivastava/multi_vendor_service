import time
from backend.utils.rate_limit import RateLimiter

def test_rate_limiter_respects_interval():
    rl = RateLimiter(rates={"sync": 2})   # 2 calls / sec  → 0.5 s interval

    # first call – should not block
    start = time.time()
    rl.wait_for_slot("sync")

    # second back-to-back call – must sleep ≥ 0.5 s
    rl.wait_for_slot("sync")
    elapsed = time.time() - start

    assert elapsed >= 0.5
