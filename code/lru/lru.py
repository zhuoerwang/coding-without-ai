class Node:
    def __init__(self, key: int | None=None, value: int | None=None):
        self.key, self.value = key, value
        self.prev, self.next = None, None

class LRUCache():
    def __init__(self, cap: int):
        self._cache = {}
        self._head, self._tail = Node(), Node()
        self._head.next, self._tail.prev = self._tail, self._head
        self._cap = cap
    
    def get(self, key: int) -> int:
        if key not in self._cache:
            return -1
        
        node = self._cache[key]
        self._remove(node)
        self._insert(node)
        return node.value
    
    def put(self, key: int, value: int) -> None:
        if key in self._cache:
            self._remove(self._cache[key])
        
        self._cache[key] = Node(key, value)
        self._insert(self._cache[key])

        if len(self._cache) > self._cap:
            evict_node = self._tail.prev
            self._remove(evict_node)
            del self._cache[evict_node.key]

    def _insert(self, node: Node):
        node.prev, node.next = self._head, self._head.next
        node.next.prev = node
        self._head.next = node

    def _remove(self, node: Node):
        node.prev.next, node.next.prev = node.next, node.prev
    
    def keys(self) -> list[int]:
        res = []
        node = self._head.next
        while node != self._tail:
            res.append(node.key)
            node = node.next
        
        return res
    
    def size(self) -> int:
        return len(self._cache)
    
    def peek(self, key: int) -> int:
        if key not in self._cache:
            return -1
        
        return self._cache[key].value

    def save(self, filepath: str) -> None:
        pass
    
    def laod(self, filepath: str) -> None:
        pass