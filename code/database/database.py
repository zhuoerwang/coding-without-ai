import time

class Database:
    """in-memory database from scratch"""
    
    def __init__(self) -> None:
        self._data = {}
        self._expire = {}

    def set(self, key: str, value: str, ttl: int | None = None) -> None:
        self._data[key] = value
        if ttl is not None:
            self._expire[key] = time.time() + ttl
        elif key in self._expire:
            del self._expire[key]
    
    def get(self, key: str) -> str | None:
        return self._data[key] if key in self._data and not self._is_expired(key) else None
    
    def delete(self, key: str) -> bool:
        if key not in self._data:
            return False
        
        del self._data[key]
        
        is_expired = False
        if key in self._expire:
            is_expired = self._is_expired(key)
            del self._expire[key]

        return not is_expired
    
    def _is_expired(self, key: str) -> bool:
        return key in self._expire and self._expire[key] < time.time()
    
    def scan(self) -> list[tuple[str, str]]:
        """Return key-value pairs, sorted by key"""
        return [(k, v) for k, v in sorted(self._data.items(), key=lambda x:x[0]) if not self._is_expired(k)]
    

    def scan_by_prefix(self, prefix: str) -> list[tuple[str, str]]:
        """filtered + sorted"""
        return [(k, v) for k, v in sorted(self._data.items(), key=lambda x:x[0]) if k.startswith(prefix) and not self._is_expired(k)]
