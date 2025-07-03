# utils/rate_limit.py
import time

class RateLimiter:
    def __init__(self, rates):
        """
        rates: dict of vendor_name -> max calls per second
        """
        self.rates = rates
        self.last_called = {vendor: 0.0 for vendor in rates}

    def wait_for_slot(self, vendor):
        """Block until it's safe to call the given vendor (respect rate limit)."""
        if vendor not in self.rates:
            return  # no rate limit specified, no wait
        max_calls = self.rates[vendor]
        if max_calls <= 0:
            return
        interval = 1.0 / max_calls  # minimum interval between calls
        now = time.time()
        elapsed = now - self.last_called[vendor]
        if elapsed < interval:
            time.sleep(interval - elapsed)
        # update last_called time to current after waiting
        self.last_called[vendor] = time.time()
