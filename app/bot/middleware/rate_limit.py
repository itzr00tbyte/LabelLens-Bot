import time
from typing import Dict, List
from app.config import settings


class RateLimiter:
    def __init__(self, limit: int = 5, window_seconds: int = 60):
        self.limit = limit
        self.window_seconds = window_seconds
        self._user_timestamps: Dict[int, List[float]] = {}

    def is_rate_limited(self, user_id: int) -> bool:
        if self.limit <= 0:
            return False
        now = time.time()
        timestamps = self._user_timestamps.get(user_id, [])
        # Filter out timestamps outside window
        valid_timestamps = [ts for ts in timestamps if now - ts < self.window_seconds]
        self._user_timestamps[user_id] = valid_timestamps

        if len(valid_timestamps) >= self.limit:
            return True

        valid_timestamps.append(now)
        return False


global_rate_limiter = RateLimiter(
    limit=settings.RATE_LIMIT_UPLOADS_PER_MINUTE, window_seconds=60
)
