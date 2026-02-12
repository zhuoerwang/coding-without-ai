import asyncio
import random
import time
import urllib
from dataclasses import dataclass
from collections import deque

# Provided mock - used across all levels
MOCK_WEB = {
    "https://a.com": ["https://a.com/about", "https://b.com"],
    "https://a.com/about": ["https://a.com"],
    "https://b.com": ["https://b.com/contact"],
    "https://b.com/contact": [],
}

@dataclass
class BucketState:
    tokens: float
    last_refill: float

exceptions = [
    TimeoutError("Request timed out"),
    ConnectionError("Connection refused"),
    Exception("500 Internal Server Error")
]

class Crawler:
    def __init__(self, max_pages: int,
                        allowed_domains: list[str] | None = None,
                        max_concurrent: int = 1,
                        requests_per_second: float = 10,
                        max_retries: int = 0):
        self.max_pages = max_pages
        self.allowed_domains = allowed_domains
        self.max_concurrent = max_concurrent
        self.requests_per_second = requests_per_second
        self.max_retries = max_retries
        self.bucket = {}
    
    def crawl(self, start_url: str) -> list[str]:
        """Return list of discovered URls in BFS order"""
        visited = set()
        queue = deque([])
        queue.append(start_url)

        discovered = []
        while len(queue) > 0 and len(discovered) < self.max_pages:
            url = queue.popleft()
            
            hostname = urllib.parse.urlparse(url).hostname
            if self.allowed_domains is not None and hostname not in self.allowed_domains:
                continue

            if url in visited:
                continue

            visited.add(url)
            discovered.append(url)
            
            for link in [link for link in self.fetch(url) if link not in visited]:
                queue.append(link)
        
        return discovered
    
    async def crawl_async(self, start_url: str) -> list[str]:
        visited = set()
        queue = deque([])
        queue.append(start_url)

        discovered = []
        while queue and len(discovered) < self.max_pages:
            batch = []
            while (queue and len(batch) < self.max_concurrent and
                   len(discovered) + len(batch) < self.max_pages):
                url = queue.popleft()
                if url in visited:
                    continue
                
                hostname = urllib.parse.urlparse(url).hostname
                if self.allowed_domains is not None and hostname not in self.allowed_domains:
                    continue

                visited.add(url)
                discovered.append(url)
                batch.append(url)

            tasks = [self.fetch_with_retry(url) for url in batch]

            for new_urls in await asyncio.gather(*tasks):
                for new_url in new_urls:
                    queue.append(new_url)
        
        return discovered

    async def fetch_with_retry(self, url: str) -> list[str]:
        # Should try self.max_retries + 1, original try not count retries.
        for attempt in range(self.max_retries + 1):
            try:
                result = await self.fetch_async(url)
                return result
            except Exception as e:
                if attempt == self.max_retries:
                    return []
                # default wait 0.5s, and extra attempt will increase the delay expontially, also add jitter randomize it within 1s
                delay = 0.5 * 2 ** attempt + random.random()
                await asyncio.sleep(delay)

        return []

    async def fetch_async(self, url: str) -> list[str]:
        if self.requests_per_second > 0:
            now = time.time()
            hostname = urllib.parse.urlparse(url).hostname
            if hostname not in self.bucket:
                state = BucketState(self.requests_per_second, now)
                self.bucket[hostname] = state
            else:
                state = self.bucket[hostname]
                # Update the token
                refill = (now - state.last_refill) * self.requests_per_second
                state.tokens = min(state.tokens + refill, self.requests_per_second)
                state.last_refill = now
                self.bucket[hostname] = state
                # No enough token
                if state.tokens < 1:
                    # Add waiting time for those reached rate limit
                    # Real world, it's better to raise 429 exception
                    wait_time = (1 - state.tokens) / self.requests_per_second
                    await asyncio.sleep(wait_time)
                    # refill token
                    now = time.time()
                    elapsed = now - state.last_refill
                    refill = elapsed * self.requests_per_second
                    state.tokens = min(state.tokens + refill, self.requests_per_second)
                    state.last_refill = now
            
            # consume a token
            state.tokens -= 1
            self.bucket[hostname] = state
        
        if self.max_retries > 0:
            # Intentional exceptions
            if random.random() < 0.2:
                raise random.choice(exceptions)
        else:
            # No retry and rate limit are not enabled
            await asyncio.sleep(0.05)

        return MOCK_WEB.get(url, [])
    
    def fetch(self, url: str) -> list[str]:
        """Return list of links found on page"""
        return MOCK_WEB.get(url, [])