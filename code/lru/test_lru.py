"""
Tests for LRU Cache (Project 2)
Run: pytest test_lru.py -k "TestLevel1" -v
"""

import time
import os
import pytest

from lru import LRUCache


# ============================================================
# Level 1: Basic LRU Cache
# ============================================================

class TestLevel1:
    def test_put_and_get(self):
        cache = LRUCache(2)
        cache.put(1, 1)
        assert cache.get(1) == 1

    def test_get_missing_key(self):
        cache = LRUCache(2)
        assert cache.get(1) == -1

    def test_eviction_order(self):
        cache = LRUCache(2)
        cache.put(1, 1)
        cache.put(2, 2)
        cache.get(1)       # makes 1 most recent
        cache.put(3, 3)    # evicts 2 (least recent)
        assert cache.get(2) == -1
        assert cache.get(1) == 1
        assert cache.get(3) == 3

    def test_full_leetcode_example(self):
        cache = LRUCache(2)
        cache.put(1, 1)
        cache.put(2, 2)
        assert cache.get(1) == 1
        cache.put(3, 3)         # evicts key 2
        assert cache.get(2) == -1
        cache.put(4, 4)         # evicts key 1
        assert cache.get(1) == -1
        assert cache.get(3) == 3
        assert cache.get(4) == 4

    def test_update_existing_key(self):
        cache = LRUCache(2)
        cache.put(1, 10)
        cache.put(1, 20)
        assert cache.get(1) == 20

    def test_update_makes_key_recent(self):
        cache = LRUCache(2)
        cache.put(1, 1)
        cache.put(2, 2)
        cache.put(1, 10)    # update 1 -> makes it most recent
        cache.put(3, 3)     # evicts 2 (least recent)
        assert cache.get(2) == -1
        assert cache.get(1) == 10

    def test_capacity_one(self):
        cache = LRUCache(1)
        cache.put(1, 1)
        cache.put(2, 2)     # evicts 1
        assert cache.get(1) == -1
        assert cache.get(2) == 2

    def test_many_operations(self):
        cache = LRUCache(3)
        for i in range(10):
            cache.put(i, i * 10)
        # Only last 3 should remain
        for i in range(7):
            assert cache.get(i) == -1
        for i in range(7, 10):
            assert cache.get(i) == i * 10


# ============================================================
# Level 2: Debug & Introspection
# ============================================================

class TestLevel2:
    def test_keys_order(self):
        cache = LRUCache(3)
        cache.put(1, 10)
        cache.put(2, 20)
        cache.put(3, 30)
        assert cache.keys() == [3, 2, 1]

    def test_keys_after_get(self):
        cache = LRUCache(3)
        cache.put(1, 10)
        cache.put(2, 20)
        cache.put(3, 30)
        cache.get(1)
        assert cache.keys() == [1, 3, 2]

    def test_size(self):
        cache = LRUCache(3)
        assert cache.size() == 0
        cache.put(1, 10)
        assert cache.size() == 1
        cache.put(2, 20)
        assert cache.size() == 2

    def test_size_at_capacity(self):
        cache = LRUCache(2)
        cache.put(1, 10)
        cache.put(2, 20)
        cache.put(3, 30)  # evicts 1
        assert cache.size() == 2

    def test_peek_does_not_update_recency(self):
        cache = LRUCache(3)
        cache.put(1, 10)
        cache.put(2, 20)
        cache.put(3, 30)
        assert cache.peek(1) == 10
        assert cache.keys() == [3, 2, 1]  # unchanged

    def test_peek_missing_key(self):
        cache = LRUCache(3)
        assert cache.peek(999) == -1

    def test_keys_empty_cache(self):
        cache = LRUCache(3)
        assert cache.keys() == []

    def test_level1_still_works(self):
        """Ensure Level 1 operations are not broken."""
        cache = LRUCache(2)
        cache.put(1, 1)
        cache.put(2, 2)
        cache.get(1)
        cache.put(3, 3)
        assert cache.get(2) == -1


# ============================================================
# Level 3: Durability
# ============================================================

class TestLevel3:
    def setup_method(self):
        self.filepath = "/tmp/test_lru_cache.dat"

    def teardown_method(self):
        if os.path.exists(self.filepath):
            os.remove(self.filepath)

    def test_save_and_load_values(self):
        cache1 = LRUCache(3)
        cache1.put(1, 10)
        cache1.put(2, 20)
        cache1.save(self.filepath)

        cache2 = LRUCache(3)
        cache2.load(self.filepath)
        assert cache2.get(1) == 10
        assert cache2.get(2) == 20

    def test_load_preserves_order(self):
        cache1 = LRUCache(3)
        cache1.put(1, 10)
        cache1.put(2, 20)
        cache1.get(1)           # makes 1 most recent
        cache1.save(self.filepath)

        cache2 = LRUCache(3)
        cache2.load(self.filepath)
        assert cache2.keys() == [1, 2]

    def test_load_replaces_current_state(self):
        cache1 = LRUCache(3)
        cache1.put(1, 10)
        cache1.save(self.filepath)

        cache2 = LRUCache(3)
        cache2.put(99, 99)
        cache2.load(self.filepath)
        assert cache2.get(99) == -1
        assert cache2.get(1) == 10

    def test_load_preserves_capacity(self):
        cache1 = LRUCache(2)
        cache1.put(1, 10)
        cache1.put(2, 20)
        cache1.save(self.filepath)

        cache2 = LRUCache(2)
        cache2.load(self.filepath)
        cache2.put(3, 30)  # should evict based on capacity=2
        assert cache2.size() == 2

    def test_save_empty_cache(self):
        cache1 = LRUCache(3)
        cache1.save(self.filepath)

        cache2 = LRUCache(3)
        cache2.load(self.filepath)
        assert cache2.keys() == []
        assert cache2.size() == 0


# ============================================================
# Level 4: TTL + Callbacks
# ============================================================

class TestLevel4:
    def test_ttl_basic(self):
        cache = LRUCache(2)
        cache.put(1, 10, ttl=1)
        assert cache.get(1) == 10
        time.sleep(1.5)
        assert cache.get(1) == -1

    def test_ttl_none_means_no_expiration(self):
        cache = LRUCache(2)
        cache.put(1, 10, ttl=None)
        time.sleep(0.5)
        assert cache.get(1) == 10

    def test_expired_items_dont_count_toward_capacity(self):
        cache = LRUCache(2)
        cache.put(1, 10, ttl=1)
        cache.put(2, 20)
        time.sleep(1.5)
        # Key 1 is expired, so capacity has room
        cache.put(3, 30)
        assert cache.get(2) == 20  # should NOT be evicted
        assert cache.get(3) == 30

    def test_on_evict_callback_capacity(self):
        evicted = []
        cache = LRUCache(2)
        cache.on_evict(lambda k, v: evicted.append((k, v)))
        cache.put(1, 10)
        cache.put(2, 20)
        cache.put(3, 30)  # evicts 1
        assert (1, 10) in evicted

    def test_on_evict_callback_ttl(self):
        evicted = []
        cache = LRUCache(2)
        cache.on_evict(lambda k, v: evicted.append((k, v)))
        cache.put(1, 10, ttl=1)
        time.sleep(1.5)
        cache.get(1)  # triggers expiration
        assert (1, 10) in evicted

    def test_multiple_evictions(self):
        evicted = []
        cache = LRUCache(1)
        cache.on_evict(lambda k, v: evicted.append((k, v)))
        cache.put(1, 10)
        cache.put(2, 20)  # evicts 1
        cache.put(3, 30)  # evicts 2
        assert evicted == [(1, 10), (2, 20)]
