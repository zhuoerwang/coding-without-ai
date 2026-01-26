## Level 1: Basic Operations ✅ COMPLETE

**Implement a class `Database` with:**

```
set(key: str, value: str) -> None
get(key: str) -> str | None
delete(key: str) -> bool  # returns True if key existed
```

**Requirements:**
- All operations O(1)
- Keys and values are strings
- `get` returns `None` if key doesn't exist
- `delete` returns `False` if key doesn't exist

**Test Cases:**
```
db = Database()
db.set("name", "alice")
db.get("name")          # "alice"
db.get("age")           # None
db.delete("name")       # True
db.get("name")          # None
db.delete("name")       # False
```

---

## Level 2: Scan Operations (Unlock after Level 1)

**Add methods:**

```
scan() -> list[tuple[str, str]]  # returns all key-value pairs, sorted by key
scan_by_prefix(prefix: str) -> list[tuple[str, str]]  # filtered + sorted
```

**Requirements:**
- Results sorted alphabetically by key
- Empty list if no matches
- Original set/get/delete still work

**Test Cases:**
```
db = Database()
db.set("user:1", "alice")
db.set("user:2", "bob")
db.set("config:debug", "true")

db.scan()
# [("config:debug", "true"), ("user:1", "alice"), ("user:2", "bob")]

db.scan_by_prefix("user:")
# [("user:1", "alice"), ("user:2", "bob")]

db.scan_by_prefix("nonexistent")
# []
```

---

## Level 3: TTL Support (Unlock after Level 2)

**Modify methods:**

```
set(key: str, value: str, ttl: int | None = None) -> None
# ttl is seconds until expiration, None means no expiration
```

**Requirements:**
- Expired keys should not appear in `get`, `scan`, `scan_by_prefix`
- `delete` on expired key returns `False`
- Do NOT use background threads for cleanup
- Lazy expiration is acceptable (clean up on access)

**Test Cases:**
```
import time

db = Database()
db.set("temp", "data", ttl=2)
db.get("temp")          # "data"
time.sleep(3)
db.get("temp")          # None (expired)

db.set("permanent", "stays")
db.set("temporary", "goes", ttl=1)
time.sleep(2)
db.scan()               # [("permanent", "stays")]
```

---

## Level 4: Persistence (Unlock after Level 3)

**Add methods:**

```
save(filepath: str) -> None  # save database to file
load(filepath: str) -> None  # load database from file (replaces current data)
```

**Requirements:**
- File format: your choice (JSON, custom, etc.)
- Must preserve TTL information correctly
- Loading a file replaces all current data
- Handle file not found gracefully

**Bonus Challenge:**
- Add compression (gzip)
- Track storage size per key prefix

**Test Cases:**
```
db1 = Database()
db1.set("key1", "value1")
db1.set("key2", "value2", ttl=3600)
db1.save("backup.db")

db2 = Database()
db2.load("backup.db")
db2.get("key1")         # "value1"
db2.get("key2")         # "value2" (TTL preserved relative to save time)
```

---