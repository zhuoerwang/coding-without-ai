import math
import time
from collections import defaultdict, deque

class RateLimiter:
    def __init__(self, max_requests: int, window_seconds: int, strategy: str = "fixed",
                 bucket_capacity: int | None = None, refill_rate: float | None = None):
        self._max_requests = max_requests
        self._window_seconds = window_seconds
        self._strategy = strategy
        self._bucket_capacity = bucket_capacity
        self._refill_rate = refill_rate
        self._fixed_window = None # for fixed window
        self._counter = defaultdict(int) # for fixed window
        self._logs = defaultdict(deque) # for sliding window
        self._buckets = {} # for token bucket
   
    def allow(self, client_id: str) -> bool:
        if self._strategy == "fixed":
            return self._allow_fixed(client_id)
        elif self._strategy == "sliding_log":
            return self._allow_sliding(client_id)
        else:
            return self._allow_bucket(client_id)
    
    def _allow_bucket(self, client_id: str) -> bool:
        now = time.time()
        if client_id not in self._buckets:
            self._buckets[client_id] = [self._bucket_capacity, now]
        token, last_refill = self._buckets[client_id]
        token += (now - last_refill) * self._refill_rate
        self._buckets[client_id] = [min(self._bucket_capacity, token), now]

        if self._buckets[client_id][0] < 1:
            return False
        
        self._buckets[client_id][0] -= 1
        return True
    
    def _allow_sliding(self, client_id: str) -> bool:
        now = time.time()
        cutoff = now - self._window_seconds
        log_queue = self._logs[client_id]
        
        # Prune all existing window
        while len(log_queue) > 0 and log_queue[0] < cutoff:
            log_queue.popleft()

        if len(log_queue) >= self._max_requests:
            return False
        
        log_queue.append(now)
        return True

    def _allow_fixed(self, client_id: str) -> bool:
        now = time.time()
        window = math.floor(now / self._window_seconds)
        if window != self._fixed_window:
            self._fixed_window = window
            self._counter = defaultdict(int)
        
        if self._counter[client_id] >= self._max_requests:
            return False
        
        self._counter[client_id] += 1
        return True