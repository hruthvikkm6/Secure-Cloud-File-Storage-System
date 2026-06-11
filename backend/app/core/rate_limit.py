import time
from collections import defaultdict
from threading import Lock
from fastapi import Request, HTTPException, status

class RateLimiter:
    def __init__(self, requests_limit: int, window_seconds: int):
        self.requests_limit = requests_limit
        self.window_seconds = window_seconds
        self.records = defaultdict(list)
        self.lock = Lock()

    def check(self, key: str) -> bool:
        current_time = time.time()
        with self.lock:
            # Filter timestamps to keep only those within the sliding window
            self.records[key] = [t for t in self.records[key] if current_time - t < self.window_seconds]
            if len(self.records[key]) >= self.requests_limit:
                return False
            self.records[key].append(current_time)
            return True

# Max 5 auth attempts (login/register) per IP every 5 minutes
login_limiter = RateLimiter(requests_limit=5, window_seconds=300)

# Max 10 file decryption tickets per IP every 60 seconds (brute force protection on encrypted assets)
ticket_limiter = RateLimiter(requests_limit=10, window_seconds=60)


async def rate_limit_login(request: Request):
    """
    FastAPI dependency to rate limit authentication endpoints.
    """
    client_ip = request.client.host if request.client else "unknown"
    if not login_limiter.check(client_ip):
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Too many authentication attempts. Brute-force protection activated. Please try again in 5 minutes."
        )


async def rate_limit_tickets(request: Request):
    """
    FastAPI dependency to rate limit secure key ticket generation.
    """
    client_ip = request.client.host if request.client else "unknown"
    if not ticket_limiter.check(client_ip):
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Too many decryption attempts. Please wait 60 seconds before trying again."
        )
