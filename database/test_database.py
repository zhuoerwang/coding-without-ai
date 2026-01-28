"""
Tests for In-Memory Database (Project 1)
Run: pytest test_database.py -k "TestLevel1" -v
"""

import time
import os
import pytest

from database import Database


# ============================================================
# Level 1: Basic Operations
# ============================================================

class TestLevel1:
    def test_set_and_get(self):
        db = Database()
        db.set("name", "alice")
        assert db.get("name") == "alice"

    def test_get_missing_key(self):
        db = Database()
        assert db.get("age") is None

    def test_delete_existing_key(self):
        db = Database()
        db.set("name", "alice")
        assert db.delete("name") is True

    def test_get_after_delete(self):
        db = Database()
        db.set("name", "alice")
        db.delete("name")
        assert db.get("name") is None

    def test_delete_missing_key(self):
        db = Database()
        assert db.delete("name") is False

    def test_overwrite_value(self):
        db = Database()
        db.set("name", "alice")
        db.set("name", "bob")
        assert db.get("name") == "bob"

    def test_multiple_keys(self):
        db = Database()
        db.set("a", "1")
        db.set("b", "2")
        db.set("c", "3")
        assert db.get("a") == "1"
        assert db.get("b") == "2"
        assert db.get("c") == "3"

    def test_delete_then_reinsert(self):
        db = Database()
        db.set("key", "first")
        db.delete("key")
        db.set("key", "second")
        assert db.get("key") == "second"

    def test_empty_string_key_and_value(self):
        db = Database()
        db.set("", "empty_key")
        assert db.get("") == "empty_key"
        db.set("key", "")
        assert db.get("key") == ""


# ============================================================
# Level 2: Scan Operations
# ============================================================

class TestLevel2:
    def test_scan_all(self):
        db = Database()
        db.set("user:1", "alice")
        db.set("user:2", "bob")
        db.set("config:debug", "true")
        result = db.scan()
        assert result == [
            ("config:debug", "true"),
            ("user:1", "alice"),
            ("user:2", "bob"),
        ]

    def test_scan_empty_db(self):
        db = Database()
        assert db.scan() == []

    def test_scan_by_prefix(self):
        db = Database()
        db.set("user:1", "alice")
        db.set("user:2", "bob")
        db.set("config:debug", "true")
        result = db.scan_by_prefix("user:")
        assert result == [("user:1", "alice"), ("user:2", "bob")]

    def test_scan_by_prefix_no_match(self):
        db = Database()
        db.set("user:1", "alice")
        assert db.scan_by_prefix("nonexistent") == []

    def test_scan_by_prefix_empty_prefix(self):
        db = Database()
        db.set("a", "1")
        db.set("b", "2")
        result = db.scan_by_prefix("")
        assert result == [("a", "1"), ("b", "2")]

    def test_scan_sorted_order(self):
        db = Database()
        db.set("c", "3")
        db.set("a", "1")
        db.set("b", "2")
        result = db.scan()
        assert result == [("a", "1"), ("b", "2"), ("c", "3")]

    def test_scan_after_delete(self):
        db = Database()
        db.set("a", "1")
        db.set("b", "2")
        db.delete("a")
        assert db.scan() == [("b", "2")]

    def test_level1_still_works(self):
        """Ensure Level 1 operations are not broken."""
        db = Database()
        db.set("key", "value")
        assert db.get("key") == "value"
        assert db.delete("key") is True
        assert db.get("key") is None


# ============================================================
# Level 3: TTL Support
# ============================================================

class TestLevel3:
    def test_set_with_ttl(self):
        db = Database()
        db.set("temp", "data", ttl=2)
        assert db.get("temp") == "data"

    def test_expired_key_returns_none(self):
        db = Database()
        db.set("temp", "data", ttl=1)
        time.sleep(1.5)
        assert db.get("temp") is None

    def test_permanent_key_survives(self):
        db = Database()
        db.set("permanent", "stays")
        db.set("temporary", "goes", ttl=1)
        time.sleep(1.5)
        assert db.get("permanent") == "stays"
        assert db.get("temporary") is None

    def test_delete_expired_key_returns_false(self):
        db = Database()
        db.set("temp", "data", ttl=1)
        time.sleep(1.5)
        assert db.delete("temp") is False

    def test_scan_excludes_expired(self):
        db = Database()
        db.set("permanent", "stays")
        db.set("temporary", "goes", ttl=1)
        time.sleep(1.5)
        result = db.scan()
        assert result == [("permanent", "stays")]

    def test_scan_by_prefix_excludes_expired(self):
        db = Database()
        db.set("user:1", "alice", ttl=1)
        db.set("user:2", "bob")
        time.sleep(1.5)
        result = db.scan_by_prefix("user:")
        assert result == [("user:2", "bob")]

    def test_overwrite_resets_ttl(self):
        db = Database()
        db.set("key", "old", ttl=1)
        db.set("key", "new", ttl=10)
        time.sleep(1.5)
        assert db.get("key") == "new"

    def test_overwrite_with_no_ttl_removes_expiration(self):
        db = Database()
        db.set("key", "old", ttl=1)
        db.set("key", "permanent")
        time.sleep(1.5)
        assert db.get("key") == "permanent"

    def test_ttl_none_means_no_expiration(self):
        db = Database()
        db.set("key", "value", ttl=None)
        time.sleep(0.5)
        assert db.get("key") == "value"


# ============================================================
# Level 4: Persistence
# ============================================================

class TestLevel4:
    def setup_method(self):
        self.filepath = "/tmp/test_db_backup.db"

    def teardown_method(self):
        if os.path.exists(self.filepath):
            os.remove(self.filepath)

    def test_save_and_load(self):
        db1 = Database()
        db1.set("key1", "value1")
        db1.set("key2", "value2")
        db1.save(self.filepath)

        db2 = Database()
        db2.load(self.filepath)
        assert db2.get("key1") == "value1"
        assert db2.get("key2") == "value2"

    def test_load_replaces_existing_data(self):
        db1 = Database()
        db1.set("key1", "value1")
        db1.save(self.filepath)

        db2 = Database()
        db2.set("other", "data")
        db2.load(self.filepath)
        assert db2.get("key1") == "value1"
        assert db2.get("other") is None

    def test_save_preserves_ttl(self):
        db1 = Database()
        db1.set("permanent", "stays")
        db1.set("temporary", "goes", ttl=3600)
        db1.save(self.filepath)

        db2 = Database()
        db2.load(self.filepath)
        assert db2.get("permanent") == "stays"
        assert db2.get("temporary") == "goes"

    def test_load_nonexistent_file(self):
        db = Database()
        db.set("existing", "data")
        # Should handle gracefully - not crash
        try:
            db.load("/tmp/nonexistent_file_12345.db")
        except FileNotFoundError:
            pass  # Acceptable to raise FileNotFoundError
        except Exception:
            pass  # Other graceful handling is also fine

    def test_save_empty_database(self):
        db1 = Database()
        db1.save(self.filepath)

        db2 = Database()
        db2.load(self.filepath)
        assert db2.scan() == []

    def test_save_preserves_scan_order(self):
        db1 = Database()
        db1.set("c", "3")
        db1.set("a", "1")
        db1.set("b", "2")
        db1.save(self.filepath)

        db2 = Database()
        db2.load(self.filepath)
        assert db2.scan() == [("a", "1"), ("b", "2"), ("c", "3")]
