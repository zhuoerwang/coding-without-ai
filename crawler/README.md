# Project 4: Web Crawler

## Level 1: Single-threaded BFS Crawler

**Implement a class `Crawler` with:**

```
__init__(max_pages: int)
crawl(start_url: str) -> list[str]  # returns list of discovered URLs in BFS order
```

**You will be given a `fetch` function:**

```python
def fetch(url: str) -> list[str]:
    """Returns list of links found on page."""
    return MOCK_WEB.get(url, [])
```

**Requirements:**
- BFS traversal (level by level)
- Don't visit the same URL twice
- Stop when `max_pages` reached
- Return URLs in visit order
- Start URL counts as the first page

**Key concepts:**
- `deque` for BFS queue
- `set` for visited tracking
- Process neighbors in order they appear

**Test Cases:**
```python
crawler = Crawler(max_pages=10)
result = crawler.crawl("https://a.com")
# ["https://a.com", "https://a.com/about", "https://b.com", "https://b.com/contact"]

crawler = Crawler(max_pages=2)
result = crawler.crawl("https://a.com")
# ["https://a.com", "https://a.com/about"]
```

---

## Level 2: Domain Filtering

**Modify constructor:**

```
__init__(max_pages: int, allowed_domains: list[str] | None = None)
```

**Requirements:**
- If `allowed_domains` is set, only crawl URLs matching those domains
- Domain = hostname (e.g., `"a.com"` from `"https://a.com/path"`)
- `None` means all domains allowed (Level 1 behavior)
- Use `urllib.parse.urlparse` for hostname extraction
- All Level 1 tests still pass

**Key concepts:**
- Parse URL to extract hostname
- Check against allowed set before adding to queue

**Test Cases:**
```python
crawler = Crawler(max_pages=10, allowed_domains=["a.com"])
result = crawler.crawl("https://a.com")
# ["https://a.com", "https://a.com/about"]  — b.com filtered out
```

---

## Level 3: Concurrent Crawling

**Modify constructor and add async method:**

```
__init__(max_pages: int, allowed_domains: list[str] | None = None, max_concurrent: int = 1)
crawl_async(start_url: str) -> list[str]  # async version
```

**You will be given an async `fetch_async` function:**

```python
async def fetch_async(url: str) -> list[str]:
    await asyncio.sleep(0.05)  # simulates network delay
    return MOCK_WEB.get(url, [])
```

**Requirements:**
- Use `asyncio` for concurrency
- Limit concurrent requests to `max_concurrent` using `asyncio.Semaphore`
- No duplicate visits (thread-safe visited set)
- Still respects `max_pages` and `allowed_domains`
- Sync `crawl()` from Level 1-2 still works

**Key concepts:**
- `asyncio.Semaphore` to limit concurrency
- `asyncio.gather` or `asyncio.create_task` to run fetches in parallel
- Need to be careful: multiple tasks may discover the same URL concurrently

**Test Cases:**
```python
crawler = Crawler(max_pages=10, max_concurrent=3)
result = await crawler.crawl_async("https://a.com")
assert set(result) == {"https://a.com", "https://a.com/about", "https://b.com", "https://b.com/contact"}
```

---

## Level 4: Rate Limiting + Retry

**Modify constructor:**

```
__init__(max_pages: int, allowed_domains: list[str] | None = None,
         max_concurrent: int = 1, requests_per_second: float = 10, max_retries: int = 3)
```

**Requirements:**
- Rate limit requests (token bucket or similar)
- Retry failed requests with exponential backoff
- Add jitter to prevent thundering herd
- Gracefully handle when all retries exhausted (skip the page, don't crash)
- All previous levels still work

**Key concepts:**
- Token bucket or `asyncio.sleep` based rate limiting
- Exponential backoff: `delay = base * 2^attempt + random_jitter`
- Composability: can you reuse your rate limiter from Project 3?

**Test Cases:**
```python
crawler = Crawler(
    max_pages=10, max_concurrent=3,
    requests_per_second=50, max_retries=5
)
result = await crawler.crawl_async("https://a.com")
assert len(result) >= 3  # should succeed despite flaky fetches
```
