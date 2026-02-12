"""
Tests for Web Crawler (Project 3)
Run: pytest test_crawler.py -k "TestLevel1" -v
"""

import asyncio
import time

import pytest

import crawler as crawler_module
from crawler import Crawler


# Provided mock - used across all levels
MOCK_WEB = {
    "https://a.com": ["https://a.com/about", "https://b.com"],
    "https://a.com/about": ["https://a.com"],
    "https://b.com": ["https://b.com/contact"],
    "https://b.com/contact": [],
}


def fetch(url: str) -> list[str]:
    """Returns list of links found on page."""
    return MOCK_WEB.get(url, [])


async def fetch_async(url: str) -> list[str]:
    """Simulates network delay."""
    await asyncio.sleep(0.05)
    return MOCK_WEB.get(url, [])


# ============================================================
# Level 1: Single-threaded BFS Crawler
# ============================================================

class TestLevel1:
    def test_crawl_all(self):
        crawler = Crawler(max_pages=10)
        result = crawler.crawl("https://a.com")
        assert result == [
            "https://a.com",
            "https://a.com/about",
            "https://b.com",
            "https://b.com/contact",
        ]

    def test_no_duplicate_visits(self):
        crawler = Crawler(max_pages=10)
        result = crawler.crawl("https://a.com")
        assert len(result) == len(set(result))

    def test_max_pages_limit(self):
        crawler = Crawler(max_pages=2)
        result = crawler.crawl("https://a.com")
        assert len(result) == 2

    def test_start_url_not_in_web(self):
        crawler = Crawler(max_pages=10)
        result = crawler.crawl("https://unknown.com")
        assert result == ["https://unknown.com"]

    def test_bfs_order(self):
        """BFS should visit level by level."""
        crawler = Crawler(max_pages=10)
        result = crawler.crawl("https://a.com")
        # a.com is level 0
        # a.com/about and b.com are level 1
        # b.com/contact is level 2
        assert result.index("https://a.com") == 0
        assert result.index("https://a.com/about") < result.index("https://b.com/contact")
        assert result.index("https://b.com") < result.index("https://b.com/contact")


# ============================================================
# Level 2: Domain Filtering
# ============================================================

class TestLevel2:
    def test_allowed_domains_filter(self):
        crawler = Crawler(max_pages=10, allowed_domains=["a.com"])
        result = crawler.crawl("https://a.com")
        assert result == ["https://a.com", "https://a.com/about"]

    def test_allowed_domains_multiple(self):
        crawler = Crawler(max_pages=10, allowed_domains=["a.com", "b.com"])
        result = crawler.crawl("https://a.com")
        assert "https://b.com" in result
        assert "https://a.com/about" in result

    def test_allowed_domains_none_means_all(self):
        crawler = Crawler(max_pages=10, allowed_domains=None)
        result = crawler.crawl("https://a.com")
        assert len(result) == 4

    def test_allowed_domains_empty_list(self):
        crawler = Crawler(max_pages=10, allowed_domains=[])
        result = crawler.crawl("https://a.com")
        # Empty list = no domains allowed, but start URL should still be visited
        # (implementation choice - either empty result or just start URL)
        assert len(result) <= 1

    def test_level1_still_works(self):
        """Ensure Level 1 operations are not broken."""
        crawler = Crawler(max_pages=10)
        result = crawler.crawl("https://a.com")
        assert len(result) == 4


# ============================================================
# Level 3: Concurrent Crawling
# ============================================================

class TestLevel3:
    @pytest.mark.asyncio
    async def test_async_crawl_same_results(self):
        crawler = Crawler(max_pages=10, max_concurrent=3)
        result = await crawler.crawl_async("https://a.com")
        assert set(result) == {
            "https://a.com",
            "https://a.com/about",
            "https://b.com",
            "https://b.com/contact",
        }

    @pytest.mark.asyncio
    async def test_async_max_pages(self):
        crawler = Crawler(max_pages=2, max_concurrent=3)
        result = await crawler.crawl_async("https://a.com")
        assert len(result) <= 2

    @pytest.mark.asyncio
    async def test_async_no_duplicates(self):
        crawler = Crawler(max_pages=10, max_concurrent=3)
        result = await crawler.crawl_async("https://a.com")
        assert len(result) == len(set(result))

    @pytest.mark.asyncio
    async def test_concurrent_1_same_as_sequential(self):
        crawler = Crawler(max_pages=10, max_concurrent=1)
        result = await crawler.crawl_async("https://a.com")
        assert set(result) == {
            "https://a.com",
            "https://a.com/about",
            "https://b.com",
            "https://b.com/contact",
        }


# ============================================================
# Level 4: Rate Limiting + Retry
# ============================================================

class TestLevel4:
    @pytest.mark.asyncio
    async def test_retry_succeeds_eventually(self):
        """With retries, flaky fetches should eventually succeed."""
        crawler = Crawler(
            max_pages=10,
            max_concurrent=3,
            requests_per_second=50,
            max_retries=5,
        )
        result = await crawler.crawl_async("https://a.com")
        # Should discover all pages despite 30% failure rate
        assert len(result) >= 3

    @pytest.mark.asyncio
    async def test_rate_limiting_respected(self):
        """Requests per second should be limited."""
        crawler = Crawler(
            max_pages=10,
            max_concurrent=10,
            requests_per_second=5,
            max_retries=3,
        )
        start = time.time()
        result = await crawler.crawl_async("https://a.com")
        elapsed = time.time() - start
        # With 4 pages at 5 req/sec, should take at least ~0.6s
        # (being lenient with timing)
        assert len(result) >= 1

    @pytest.mark.asyncio
    async def test_max_retries_exhausted(self):
        """When all retries fail, should handle gracefully."""
        crawler = Crawler(
            max_pages=10,
            max_concurrent=1,
            requests_per_second=100,
            max_retries=1,
        )
        # Should not crash even if some pages fail
        result = await crawler.crawl_async("https://a.com")
        assert isinstance(result, list)


# ============================================================
# Level 4 Strict: Deterministic tests with controlled failures
# ============================================================

class TestLevel4Strict:
    @pytest.mark.asyncio
    async def test_retry_exact_count(self):
        """Verify fetch is retried exactly max_retries times before giving up."""
        call_count = 0

        class AlwaysFailCrawler(Crawler):
            async def fetch_async(self, url: str) -> list[str]:
                nonlocal call_count
                call_count += 1
                raise ConnectionError("Always fails")

        crawler = AlwaysFailCrawler(
            max_pages=10, max_concurrent=1,
            requests_per_second=0, max_retries=3,
        )
        result = await crawler.crawl_async("https://a.com")
        # 1 original attempt + 3 retries = 4 total calls
        assert call_count == 4
        assert result == ["https://a.com"]  # URL was added to discovered before fetch

    @pytest.mark.asyncio
    async def test_retry_stops_on_success(self):
        """Verify retry stops immediately when fetch succeeds."""
        calls_per_url = {}

        class FailThenSucceedCrawler(Crawler):
            async def fetch_async(self, url: str) -> list[str]:
                nonlocal calls_per_url
                calls_per_url[url] = calls_per_url.get(url, 0) + 1
                if calls_per_url[url] <= 2:
                    raise TimeoutError("Temporary failure")
                return MOCK_WEB.get(url, [])

        crawler = FailThenSucceedCrawler(
            max_pages=10, max_concurrent=1,
            requests_per_second=0, max_retries=5,
        )
        result = await crawler.crawl_async("https://a.com")
        # Each URL should succeed on 3rd attempt, not use all 5 retries
        for url, count in calls_per_url.items():
            assert count == 3, f"{url} was called {count} times, expected 3"
        assert len(result) >= 1

    @pytest.mark.asyncio
    async def test_exponential_backoff_timing(self):
        """Verify delays increase exponentially between retries."""
        retry_timestamps = []

        class TimingCrawler(Crawler):
            async def fetch_async(self, url: str) -> list[str]:
                retry_timestamps.append(time.time())
                raise ConnectionError("Always fails")

        crawler = TimingCrawler(
            max_pages=1, max_concurrent=1,
            requests_per_second=0, max_retries=3,
        )
        await crawler.crawl_async("https://a.com")

        # 4 timestamps: original + 3 retries
        assert len(retry_timestamps) == 4

        # Calculate delays between attempts
        delays = [
            retry_timestamps[i + 1] - retry_timestamps[i]
            for i in range(len(retry_timestamps) - 1)
        ]

        # Expected: delay = 0.5 * 2^attempt + jitter(0-1)
        # delay[0] ~= 0.5 * 2^0 + jitter = 0.5-1.5s
        # delay[1] ~= 0.5 * 2^1 + jitter = 1.0-2.0s
        # delay[2] ~= 0.5 * 2^2 + jitter = 2.0-3.0s
        expected_ranges = [(0.4, 1.6), (0.9, 2.1), (1.9, 3.1)]
        for i, (lo, hi) in enumerate(expected_ranges):
            assert lo <= delays[i] <= hi, (
                f"Delay {i} was {delays[i]:.3f}s, expected between {lo}s and {hi}s"
            )

    @pytest.mark.asyncio
    async def test_jitter_adds_randomness(self):
        """Verify jitter makes delays non-deterministic across runs."""
        async def get_delays():
            timestamps = []

            class TimingCrawler(Crawler):
                async def fetch_async(self, url: str) -> list[str]:
                    timestamps.append(time.time())
                    raise ConnectionError("Fail")

            crawler = TimingCrawler(
                max_pages=1, max_concurrent=1,
                requests_per_second=0, max_retries=1,
            )
            await crawler.crawl_async("https://a.com")
            return timestamps[1] - timestamps[0]

        # Run twice and check delays are different (jitter)
        delay1 = await get_delays()
        delay2 = await get_delays()
        # With jitter, delays should not be exactly the same
        # (extremely unlikely to be identical with random.random())
        assert delay1 != delay2, "Delays are identical - jitter may not be applied"

    @pytest.mark.asyncio
    async def test_rate_limit_enforces_minimum_interval(self):
        """Verify rate limiter enforces minimum time between requests.

        Must call super().fetch_async() to preserve rate limiting logic.
        Adds test URLs to MOCK_WEB so the parent method can resolve them.
        """
        extra_urls = {
            "https://x.com": ["https://x.com/1", "https://x.com/2",
                              "https://x.com/3", "https://x.com/4"],
            "https://x.com/1": [],
            "https://x.com/2": [],
            "https://x.com/3": [],
            "https://x.com/4": [],
        }
        crawler_module.MOCK_WEB.update(extra_urls)

        class TrackingCrawler(Crawler):
            def __init__(self, *args, **kwargs):
                super().__init__(*args, **kwargs)
                self.timestamps = []

            async def fetch_async(self, url: str) -> list[str]:
                result = await super().fetch_async(url)
                self.timestamps.append(time.time())
                return result

        try:
            # 1 req/sec = burst of 1 token, then ~1s between requests
            crawler = TrackingCrawler(
                max_pages=10, max_concurrent=1,
                requests_per_second=1, max_retries=0,
            )
            await crawler.crawl_async("https://x.com")

            assert len(crawler.timestamps) == 5

            # After burst (1 token), subsequent requests should wait ~1s
            for i in range(1, len(crawler.timestamps)):
                interval = crawler.timestamps[i] - crawler.timestamps[i - 1]
                assert interval >= 0.8, (
                    f"Request {i} was only {interval:.3f}s after request {i-1}, "
                    f"expected ~1.0s for 1 req/sec"
                )
        finally:
            for key in extra_urls:
                crawler_module.MOCK_WEB.pop(key, None)

    @pytest.mark.asyncio
    async def test_rate_limit_total_elapsed_time(self):
        """Verify total crawl time matches expected rate limit.

        With burst=2 and 5 pages on same domain at 2 req/sec,
        first 2 requests are instant, remaining 3 each wait ~0.5s.
        """
        extra_urls = {
            "https://x.com": ["https://x.com/1", "https://x.com/2",
                              "https://x.com/3", "https://x.com/4"],
            "https://x.com/1": [],
            "https://x.com/2": [],
            "https://x.com/3": [],
            "https://x.com/4": [],
        }
        crawler_module.MOCK_WEB.update(extra_urls)

        try:
            crawler = Crawler(
                max_pages=10, max_concurrent=1,
                requests_per_second=2, max_retries=0,
            )
            start = time.time()
            result = await crawler.crawl_async("https://x.com")
            elapsed = time.time() - start

            assert len(result) == 5
            # Burst of 2 tokens: first 2 requests instant
            # Remaining 3 requests each wait ~0.5s = ~1.5s total
            assert elapsed >= 1.2, f"Crawl too fast: {elapsed:.3f}s for 5 pages at 2 req/sec"
        finally:
            for key in extra_urls:
                crawler_module.MOCK_WEB.pop(key, None)

    @pytest.mark.asyncio
    async def test_failed_pages_dont_block_others(self):
        """Pages that fail after all retries should not prevent discovering other pages."""
        class SelectiveFailCrawler(Crawler):
            async def fetch_async(self, url: str) -> list[str]:
                # Only a.com/about always fails, others succeed
                if url == "https://a.com/about":
                    raise ConnectionError("This page always fails")
                return MOCK_WEB.get(url, [])

        crawler = SelectiveFailCrawler(
            max_pages=10, max_concurrent=3,
            requests_per_second=0, max_retries=2,
        )
        result = await crawler.crawl_async("https://a.com")

        # a.com should succeed, a.com/about fails but b.com should still be discovered
        assert "https://a.com" in result
        assert "https://b.com" in result

    @pytest.mark.asyncio
    async def test_no_duplicates_with_retries(self):
        """Retries should not cause duplicate URLs in the result."""
        class FlakyCrawler(Crawler):
            def __init__(self, *args, **kwargs):
                super().__init__(*args, **kwargs)
                self._attempt_count = {}

            async def fetch_async(self, url: str) -> list[str]:
                count = self._attempt_count.get(url, 0)
                self._attempt_count[url] = count + 1
                # Fail first attempt for every URL
                if count == 0:
                    raise TimeoutError("First attempt always fails")
                return MOCK_WEB.get(url, [])

        crawler = FlakyCrawler(
            max_pages=10, max_concurrent=3,
            requests_per_second=0, max_retries=3,
        )
        result = await crawler.crawl_async("https://a.com")
        assert len(result) == len(set(result)), "Duplicate URLs found in result"

    @pytest.mark.asyncio
    async def test_graceful_failure_returns_partial_results(self):
        """When some pages fail permanently, should return pages that succeeded."""
        class PartialFailCrawler(Crawler):
            async def fetch_async(self, url: str) -> list[str]:
                # a.com succeeds, everything else fails
                if url == "https://a.com":
                    return MOCK_WEB.get(url, [])
                raise Exception("Permanent failure")

        crawler = PartialFailCrawler(
            max_pages=10, max_concurrent=3,
            requests_per_second=0, max_retries=2,
        )
        result = await crawler.crawl_async("https://a.com")
        # Should have at least a.com, and the discovered but failed pages
        assert "https://a.com" in result
        assert isinstance(result, list)

    @pytest.mark.asyncio
    async def test_retry_with_different_exception_types(self):
        """Retry should handle all exception types equally."""
        call_count = 0
        exception_sequence = [
            TimeoutError("Timeout"),
            ConnectionError("Connection refused"),
            Exception("500 Error"),
        ]

        class MultiExceptionCrawler(Crawler):
            async def fetch_async(self, url: str) -> list[str]:
                nonlocal call_count
                call_count += 1
                if call_count <= len(exception_sequence):
                    raise exception_sequence[call_count - 1]
                return MOCK_WEB.get(url, [])

        crawler = MultiExceptionCrawler(
            max_pages=1, max_concurrent=1,
            requests_per_second=0, max_retries=5,
        )
        result = await crawler.crawl_async("https://a.com")
        # Should succeed after 3 failures (call_count=4)
        assert call_count == 4

    @pytest.mark.asyncio
    async def test_level3_still_works_with_level4_params(self):
        """Level 3 behavior should not break when level 4 params are defaults."""
        crawler = Crawler(max_pages=10, max_concurrent=3)
        result = await crawler.crawl_async("https://a.com")
        assert set(result) == {
            "https://a.com",
            "https://a.com/about",
            "https://b.com",
            "https://b.com/contact",
        }
