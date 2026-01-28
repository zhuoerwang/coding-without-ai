"""
Tests for Rate Limiter (Project 3)
Run: pytest test_ratelimiter.py -k "TestLevel1" -v
"""

import time
import pytest

from ratelimiter import RateLimiter


# ============================================================
# Level 1: Fixed Window Rate Limiter
# ============================================================

class TestLevel1:
    def test_allow_within_limit(self):
        rl = RateLimiter(max_requests=3, window_seconds=10)
        assert rl.allow("client1") is True
        assert rl.allow("client1") is True
        assert rl.allow("client1") is True

    def test_reject_over_limit(self):
        rl = RateLimiter(max_requests=2, window_seconds=10)
        assert rl.allow("client1") is True
        assert rl.allow("client1") is True
        assert rl.allow("client1") is False

    def test_separate_clients(self):
        rl = RateLimiter(max_requests=1, window_seconds=10)
        assert rl.allow("client1") is True
        assert rl.allow("client2") is True
        assert rl.allow("client1") is False
        assert rl.allow("client2") is False

    def test_window_reset(self):
        rl = RateLimiter(max_requests=1, window_seconds=1)
        assert rl.allow("client1") is True
        assert rl.allow("client1") is False
        time.sleep(1.1)
        assert rl.allow("client1") is True

    def test_single_request_limit(self):
        rl = RateLimiter(max_requests=1, window_seconds=10)
        assert rl.allow("x") is True
        assert rl.allow("x") is False

    def test_high_limit(self):
        rl = RateLimiter(max_requests=100, window_seconds=10)
        for _ in range(100):
            assert rl.allow("x") is True
        assert rl.allow("x") is False

    def test_multiple_clients_independent_windows(self):
        rl = RateLimiter(max_requests=2, window_seconds=1)
        assert rl.allow("a") is True
        assert rl.allow("a") is True
        time.sleep(1.1)
        # 'a' window resets, 'b' is fresh
        assert rl.allow("a") is True
        assert rl.allow("b") is True


# ============================================================
# Level 2: Sliding Window Log
# ============================================================

class TestLevel2:
    def test_sliding_window_basic(self):
        """Requests near boundary should carry over."""
        rl = RateLimiter(max_requests=2, window_seconds=1, strategy="sliding_log")
        assert rl.allow("c") is True
        assert rl.allow("c") is True
        assert rl.allow("c") is False

    def test_sliding_window_gradual_expiry(self):
        """Old requests expire one-by-one, not all at once."""
        rl = RateLimiter(max_requests=2, window_seconds=1, strategy="sliding_log")
        assert rl.allow("c") is True       # t=0.0
        time.sleep(0.5)
        assert rl.allow("c") is True       # t=0.5
        assert rl.allow("c") is False      # still 2 in window
        time.sleep(0.6)                     # t=1.1 — first request expired
        assert rl.allow("c") is True       # only 1 in window now

    def test_sliding_vs_fixed_boundary(self):
        """Sliding window doesn't have the fixed window boundary problem."""
        rl = RateLimiter(max_requests=2, window_seconds=1, strategy="sliding_log")
        time.sleep(0.8)                     # near end of a "fixed" window
        assert rl.allow("c") is True       # t=0.8
        assert rl.allow("c") is True       # t=0.8
        time.sleep(0.3)                     # t=1.1 — crosses fixed boundary
        # In fixed window, this would be allowed (new window).
        # In sliding window, both requests are still within 1s.
        assert rl.allow("c") is False

    def test_sliding_separate_clients(self):
        rl = RateLimiter(max_requests=1, window_seconds=1, strategy="sliding_log")
        assert rl.allow("a") is True
        assert rl.allow("b") is True
        assert rl.allow("a") is False

    def test_sliding_all_expire(self):
        rl = RateLimiter(max_requests=3, window_seconds=1, strategy="sliding_log")
        assert rl.allow("x") is True
        assert rl.allow("x") is True
        assert rl.allow("x") is True
        assert rl.allow("x") is False
        time.sleep(1.1)
        # All expired, full quota available
        assert rl.allow("x") is True
        assert rl.allow("x") is True
        assert rl.allow("x") is True

    def test_level1_still_works(self):
        """Default strategy should still work (fixed window)."""
        rl = RateLimiter(max_requests=2, window_seconds=10)
        assert rl.allow("c") is True
        assert rl.allow("c") is True
        assert rl.allow("c") is False


# ============================================================
# Level 3: Token Bucket
# ============================================================

class TestLevel3:
    def test_token_bucket_basic(self):
        rl = RateLimiter(
            max_requests=5,
            window_seconds=1,
            strategy="token_bucket",
            bucket_capacity=5,
            refill_rate=5,  # 5 tokens per second
        )
        # Burst: use all 5 tokens
        for _ in range(5):
            assert rl.allow("c") is True
        assert rl.allow("c") is False

    def test_token_bucket_refill(self):
        rl = RateLimiter(
            max_requests=5,
            window_seconds=1,
            strategy="token_bucket",
            bucket_capacity=5,
            refill_rate=5,
        )
        # Use all tokens
        for _ in range(5):
            rl.allow("c")
        assert rl.allow("c") is False
        # Wait for refill (1 token per 0.2s at rate=5/s)
        time.sleep(0.5)
        # Should have ~2 tokens now
        assert rl.allow("c") is True

    def test_token_bucket_capacity_cap(self):
        """Tokens should not exceed bucket capacity even after long wait."""
        rl = RateLimiter(
            max_requests=3,
            window_seconds=1,
            strategy="token_bucket",
            bucket_capacity=3,
            refill_rate=10,
        )
        time.sleep(2)  # way more than enough to fill
        # Should only have 3 tokens (capacity), not 20+
        for _ in range(3):
            assert rl.allow("c") is True
        assert rl.allow("c") is False

    def test_token_bucket_separate_clients(self):
        rl = RateLimiter(
            max_requests=1,
            window_seconds=1,
            strategy="token_bucket",
            bucket_capacity=1,
            refill_rate=1,
        )
        assert rl.allow("a") is True
        assert rl.allow("b") is True
        assert rl.allow("a") is False
        assert rl.allow("b") is False

    def test_token_bucket_continuous_refill(self):
        """Tokens refill continuously, not in discrete intervals."""
        rl = RateLimiter(
            max_requests=10,
            window_seconds=1,
            strategy="token_bucket",
            bucket_capacity=10,
            refill_rate=10,
        )
        # Use all tokens
        for _ in range(10):
            rl.allow("c")
        # Wait 0.15s -> should have ~1 token
        time.sleep(0.15)
        assert rl.allow("c") is True
        assert rl.allow("c") is False

    def test_previous_strategies_still_work(self):
        """Fixed window and sliding log should still work."""
        rl1 = RateLimiter(max_requests=1, window_seconds=10)
        assert rl1.allow("x") is True
        assert rl1.allow("x") is False

        rl2 = RateLimiter(max_requests=1, window_seconds=10, strategy="sliding_log")
        assert rl2.allow("x") is True
        assert rl2.allow("x") is False


# ============================================================
# Level 4: Introspection + Callbacks
# ============================================================

class TestLevel4:
    def test_remaining_requests(self):
        rl = RateLimiter(max_requests=3, window_seconds=10)
        assert rl.remaining("client1") == 3
        rl.allow("client1")
        assert rl.remaining("client1") == 2
        rl.allow("client1")
        assert rl.remaining("client1") == 1
        rl.allow("client1")
        assert rl.remaining("client1") == 0

    def test_remaining_unknown_client(self):
        rl = RateLimiter(max_requests=5, window_seconds=10)
        assert rl.remaining("nobody") == 5

    def test_retry_after(self):
        """When rate limited, return seconds until next allowed request."""
        rl = RateLimiter(max_requests=1, window_seconds=2)
        rl.allow("c")
        retry = rl.retry_after("c")
        assert retry is not None
        assert 0 < retry <= 2.0

    def test_retry_after_not_limited(self):
        rl = RateLimiter(max_requests=5, window_seconds=10)
        assert rl.retry_after("c") is None

    def test_on_reject_callback(self):
        rejected = []
        rl = RateLimiter(max_requests=1, window_seconds=10)
        rl.on_reject(lambda client_id: rejected.append(client_id))
        rl.allow("c")
        rl.allow("c")  # rejected
        assert "c" in rejected

    def test_on_reject_not_called_when_allowed(self):
        rejected = []
        rl = RateLimiter(max_requests=5, window_seconds=10)
        rl.on_reject(lambda client_id: rejected.append(client_id))
        rl.allow("c")
        assert rejected == []

    def test_remaining_with_sliding_log(self):
        rl = RateLimiter(max_requests=3, window_seconds=1, strategy="sliding_log")
        rl.allow("c")
        rl.allow("c")
        assert rl.remaining("c") == 1
        time.sleep(1.1)
        assert rl.remaining("c") == 3  # all expired

    def test_remaining_with_token_bucket(self):
        rl = RateLimiter(
            max_requests=5,
            window_seconds=1,
            strategy="token_bucket",
            bucket_capacity=5,
            refill_rate=5,
        )
        rl.allow("c")
        rl.allow("c")
        rem = rl.remaining("c")
        assert rem == 3

    def test_retry_after_sliding_log(self):
        rl = RateLimiter(max_requests=1, window_seconds=1, strategy="sliding_log")
        rl.allow("c")
        retry = rl.retry_after("c")
        assert retry is not None
        assert 0 < retry <= 1.0

    def test_multiple_rejections_callback(self):
        rejected = []
        rl = RateLimiter(max_requests=1, window_seconds=10)
        rl.on_reject(lambda client_id: rejected.append(client_id))
        rl.allow("a")
        rl.allow("b")
        rl.allow("a")  # rejected
        rl.allow("a")  # rejected again
        rl.allow("b")  # rejected
        assert rejected == ["a", "a", "b"]
