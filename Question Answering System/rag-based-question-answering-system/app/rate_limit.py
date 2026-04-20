import time
from collections import defaultdict, deque
from fastapi import HTTPException, Request

from app.config import RATE_LIMIT_PER_MINUTE

_REQUEST_LOG = defaultdict(deque)


def check_rate_limit(request: Request):
    client_ip = request.client.host if request.client else "unknown"
    now = time.time()
    window_start = now - 60
    bucket = _REQUEST_LOG[client_ip]

    while bucket and bucket[0] < window_start:
        bucket.popleft()

    if len(bucket) >= RATE_LIMIT_PER_MINUTE:
        retry_after = int(max(1, 60 - (now - bucket[0])))
        raise HTTPException(
            status_code=429,
            detail=f"Rate limit exceeded. Try again in {retry_after} seconds."
        )

    bucket.append(now)