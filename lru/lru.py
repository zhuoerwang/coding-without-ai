import json
import time
from collections.abc import Callable

class Node():
    def __init__(self, key: int | None = None, val: int | None = None):
        self.key, self.val = key, val
        self.prev: Node | None = None
        self.next: Node | None = None


class LRUCache():
    def __init__(self, cap: int):
        self._cache = {}
        self._expire = {}
        self._head: Node = Node()
        self._tail: Node = Node()
        self._head.next, self._tail.prev = self._tail, self._head
        self._cap = cap
        self._on_evict_cb = None
    
    def get(self, key: int) -> int:
        if key in self._cache:
            if key in self._expire and time.time() > self._expire[key]:
                self._evict_node(self._cache[key])
                return -1
            node = self._cache[key]
            self._remove(node)
            self._move_to_end(node)

            return node.val
        
        return -1
    
    def put(self, key: int, val: int, ttl: int | None = None) -> None:
        for k in list(self._expire):
            if time.time() > self._expire[k]:
                self._evict_node(self._cache[k])
        
        if key in self._cache:
            self._remove(self._cache[key])

        if ttl is not None:
            self._expire[key] = time.time() + ttl
        elif key in self._expire:
            del self._expire[key]

        self._cache[key] = Node(key, val)
        self._move_to_end(self._cache[key])

        if len(self._cache) > self._cap:
            self._evict_node(self._head.next)

    def _move_to_end(self, node: Node):
        prev, nxt = self._tail.prev, self._tail
        assert prev is not None
        node.prev, node.next = prev, nxt
        prev.next, nxt.prev = node, node

    def _remove(self, node: Node):
        prev, nxt = node.prev, node.next
        assert prev is not None and nxt is not None
        nxt.prev, prev.next = prev, nxt
    
    def keys(self) -> list[int]:
        res = []
        node = self._tail.prev
        while node is not None and node != self._head:
            if not (node.key in self._expire and time.time() > self._expire[node.key]):
                res.append(node.key)
            node = node.prev

        return res
    
    def peek(self, key: int) -> int:
        if key in self._cache:
            if key in self._expire and time.time() > self._expire[key]:
                self._evict_node(self._cache[key])
                return -1
            return self._cache[key].val
        
        return -1

    def _evict_node(self, node: Node | None) -> None:
        if node is None: return

        if self._on_evict_cb:
            assert node.key is not None and node.val is not None
            self._on_evict_cb(node.key, node.val)
        
        self._remove(node)
        del self._cache[node.key]
        if node.key in self._expire:
            del self._expire[node.key]
    
    def size(self) -> int:
        size = 0
        for key in self._cache:
            if key in self._expire and time.time() > self._expire[key]:
                continue
            size += 1
        return size

    def on_evict(self, callback: Callable[[int, int], None]) -> None:
        self._on_evict_cb = callback

    def save(self, filepath: str) -> None:
        json_obj = {"cache": [], "cap": self._cap}
        node = self._head.next
        while node is not None and node != self._tail:
            json_obj["cache"].append((node.key, node.val))
            node = node.next

        with open(filepath, "w") as fp:
            json.dump(json_obj, fp)
    
    def load(self, filepath: str) -> None:
        with open(filepath, "r") as fp:
            json_obj = json.load(fp)
        
        cache = {}
        head, tail = Node(), Node()
        root = head
        for key, val in json_obj["cache"]:
            node = Node(key, val)
            cache[key] = node
            root.next, node.prev = node, root
            root = root.next

        root.next, tail.prev = tail, root
        
        self._cache = cache
        self._head, self._tail = head, tail
        self._cap = json_obj["cap"]