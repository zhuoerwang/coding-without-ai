# Project 3: Rate Limiter

## Level 1: Fixed Window Rate Limiter

**Implement a class `RateLimiter` with:**

```
__init__(max_requests: int, window_seconds: int)
allow(client_id: str) -> bool  # returns True if request is allowed
```

**Requirements:**
- Track requests per client in fixed time windows
- O(1) per call
- Each client has an independent counter
- Counter resets when the window expires
- Window = `floor(current_time / window_seconds)`

**Key concepts:**
- If window changed since last request, reset counter
- Compare counter against max_requests

**Test Cases:**
```python
rl = RateLimiter(max_requests=3, window_seconds=10)
rl.allow("client1")  # True
rl.allow("client1")  # True
rl.allow("client1")  # True
rl.allow("client1")  # False — limit reached

rl.allow("client2")  # True — separate client
```

---

## Level 2: Sliding Window Log

**Modify constructor:**

```
__init__(max_requests: int, window_seconds: int, strategy: str = "fixed")
# strategy: "fixed" | "sliding_log"
```

**Requirements:**
- Keep a log of timestamps for each client
- Count requests within `[now - window_seconds, now]`
- Clean up old timestamps on each call
- Fixes the "boundary burst" problem of fixed windows
- All Level 1 tests still pass (default strategy is "fixed")

**Key concepts:**
- Store deque/list of timestamps per client
- On each `allow()`, prune timestamps older than `now - window`
- Count remaining timestamps
- More accurate than fixed window, but uses more memory

**Test Cases:**
```python
rl = RateLimiter(max_requests=2, window_seconds=1, strategy="sliding_log")
rl.allow("c")   # True  (t=0.0)
time.sleep(0.5)
rl.allow("c")   # True  (t=0.5)
rl.allow("c")   # False (2 requests in last 1s)
time.sleep(0.6) # t=1.1 — first request expires
rl.allow("c")   # True  (only 1 in window now)
```

---

## Level 3: Token Bucket

**Modify constructor:**

```
__init__(max_requests: int, window_seconds: int, strategy: str = "fixed",
         bucket_capacity: int | None = None, refill_rate: float | None = None)
# strategy: "fixed" | "sliding_log" | "token_bucket"
# bucket_capacity: max tokens in bucket
# refill_rate: tokens added per second
```

**Requirements:**
- Each client has a bucket with `capacity` tokens
- Tokens refill at `refill_rate` per second continuously
- Each request consumes 1 token
- Bucket never exceeds capacity
- Allows bursts up to capacity
- All Level 1 + Level 2 tests still pass

**Key concepts:**
- Track `tokens` and `last_refill_time` per client
- On each call: `tokens += (now - last_refill) * refill_rate`
- Cap at capacity: `tokens = min(tokens, capacity)`
- If tokens >= 1: consume and allow; else: reject

**Test Cases:**
```python
rl = RateLimiter(
    max_requests=5, window_seconds=1,
    strategy="token_bucket",
    bucket_capacity=5, refill_rate=5
)
# Burst: 5 requests immediately
for _ in range(5):
    rl.allow("c")  # True
rl.allow("c")      # False — bucket empty
time.sleep(0.5)    # ~2.5 tokens refilled
rl.allow("c")      # True
```

---

## Level 4: Introspection + Callbacks

**Add methods:**

```
remaining(client_id: str) -> int        # how many requests left in current window/bucket
retry_after(client_id: str) -> float | None  # seconds until next request allowed (None if not limited)
on_reject(callback: Callable[[str], None]) -> None  # called with client_id when rejected
```

**Requirements:**
- `remaining()` works for all three strategies
- `retry_after()` returns None if client is not rate limited
- `on_reject()` fires every time `allow()` returns False
- All Level 1-3 strategies still work

**Test Cases:**
```python
rl = RateLimiter(max_requests=3, window_seconds=10)
rl.remaining("client1")  # 3
rl.allow("client1")
rl.remaining("client1")  # 2

rejected = []
rl.on_reject(lambda cid: rejected.append(cid))
rl.allow("client1")  # True
rl.allow("client1")  # True
rl.allow("client1")  # False — callback fires
assert "client1" in rejected
```
