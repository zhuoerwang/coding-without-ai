import math
import time
from collections import defaultdict, deque

class RateLimiter:
    def __init__(self, max_requests: int, window_seconds: int, strategy: str = "fixed"):
        self._max_requests = max_requests
        self._window_seconds = window_seconds
        self._strategy = strategy
        self._fixed_window = None # for fixed window strategy
        self._counter = defaultdict(int) # for fixed window strategy
        self._logs = defaultdict(deque) # for sliding window strategy
   
    def allow(self, client_id: str) -> bool:
        if self._strategy == "fixed":
            return self._allow_fixed(client_id)
        else:
            return self._allow_sliding(client_id)
    
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
    