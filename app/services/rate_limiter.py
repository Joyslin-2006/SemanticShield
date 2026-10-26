
from collections import defaultdict, deque
from threading import Lock
from time import monotonic


class RateLimiter:
    def __init__(self, rate_limit: int = 5, time_window: int = 60):
        if rate_limit < 1 or time_window < 1:
            raise ValueError("Limits must be positive")

        self.rate_limit = rate_limit
        self.time_window = time_window
        self.requests = defaultdict(deque)
        self.lock = Lock()

    def is_allowed(self, client_ip: str) -> tuple[bool, int]:
        current_time = monotonic()

        with self.lock:
            timestamps = self.requests[client_ip]

            while (
                timestamps
                and current_time - timestamps[0] >= self.time_window
            ):
                timestamps.popleft()

            if len(timestamps) >= self.rate_limit:
                retry_after = max(
                    1,
                    int(self.time_window - (current_time - timestamps[0])) + 1,
                )
                return False, retry_after

            timestamps.append(current_time)
            return True, 0
