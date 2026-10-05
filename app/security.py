"""Auth, rate limiting and origin checks."""
import hmac
import threading
import time
from collections import defaultdict, deque

from fastapi import Header, HTTPException, Request

from app.config import get_settings
from app.models import Widget


def require_admin(x_admin_key: str = Header(default="")) -> None:
    """Dependency for /admin routes. Constant-time comparison."""
    expected = get_settings().admin_api_key.encode()
    if not hmac.compare_digest(x_admin_key.encode(), expected):
        raise HTTPException(status_code=401, detail="Invalid admin key")


def client_ip(request: Request) -> str:
    if get_settings().trust_proxy:
        forwarded = request.headers.get("x-forwarded-for")
        if forwarded:
            return forwarded.split(",")[0].strip()
    return request.client.host if request.client else "unknown"


def origin_allowed(widget: Widget, origin: str | None) -> bool:
    allowed = widget.allowed_origins or []
    if "*" in allowed:
        return True
    return origin is not None and origin.rstrip("/") in allowed


class RateLimiter:
    """Sliding-window limiter, in memory. Per process: swap for Redis if you run many workers."""

    def __init__(self, window_seconds: int = 60):
        self.window = window_seconds
        self.hits: dict[str, deque] = defaultdict(deque)
        self.lock = threading.Lock()

    def allow(self, key: str, limit: int) -> bool:
        now = time.monotonic()
        with self.lock:
            q = self.hits[key]
            while q and now - q[0] > self.window:
                q.popleft()
            if len(q) >= limit:
                return False
            q.append(now)
            return True


limiter = RateLimiter()
