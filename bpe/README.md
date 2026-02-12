# Project 9: BPE Tokenizer

## Level 1: Byte-Pair Encoding — Training

**Implement a class `BPETokenizer`:**

```
class BPETokenizer:
    __init__() -> None
    train(text: str, vocab_size: int) -> None     # learn merge rules from text
    get_vocab() -> dict[int, bytes]                # token_id -> token bytes
    get_merges() -> list[tuple[bytes, bytes]]      # ordered list of learned merges
```

**Requirements:**
- Start with a base vocabulary of 256 byte-level tokens (0x00–0xFF)
- Repeatedly find the most frequent adjacent pair of tokens in the corpus
- Merge that pair into a new token, add it to vocabulary
- Stop when `vocab_size` is reached
- Merges are ordered: first merge = most frequent pair at time of merge
- Handle ties in frequency deterministically (e.g. lexicographic order of pair)
- Track merge rules in order for encoding/decoding

**Algorithm:**
```
1. Split text into bytes: [104, 101, 108, 108, 111] for "hello"
2. Count adjacent pairs: (104,101)=1, (101,108)=1, (108,108)=1, (108,111)=1
3. Merge most frequent pair -> new token ID (256, 257, ...)
4. Repeat until vocab_size reached
```

**Test Cases:**
```python
tokenizer = BPETokenizer()
tokenizer.train("aaabdaaabac", vocab_size=259)  # 256 base + 3 merges
merges = tokenizer.get_merges()
assert len(merges) == 3
# First merge should be (b"a", b"a") since "aa" is most frequent
assert merges[0] == (b"a", b"a")
vocab = tokenizer.get_vocab()
assert len(vocab) == 259
```

---

## Level 2: Encoding + Decoding

**Extend `BPETokenizer`:**

```
encode(text: str) -> list[int]      # text -> token IDs
decode(ids: list[int]) -> str       # token IDs -> text
```

**Requirements:**
- `encode()`: apply learned merge rules in order to compress text
  - Start with byte-level tokens
  - Apply merges in the same order they were learned during training
  - Each merge pass: find all occurrences of the pair and merge them
- `decode()`: concatenate token bytes and decode to string
- Round-trip property: `decode(encode(text)) == text` for any training text
- Handle text with characters not seen during training (fall back to byte-level)
- Handle empty string: `encode("") == []`, `decode([]) == ""`
- Encoding should be deterministic

**Test Cases:**
```python
tokenizer = BPETokenizer()
tokenizer.train("hello world hello world", vocab_size=270)

encoded = tokenizer.encode("hello world")
assert isinstance(encoded, list)
assert all(isinstance(t, int) for t in encoded)
assert len(encoded) < len("hello world")  # compression happened

decoded = tokenizer.decode(encoded)
assert decoded == "hello world"

# Round-trip
assert tokenizer.decode(tokenizer.encode("hello world")) == "hello world"

# Empty
assert tokenizer.encode("") == []
assert tokenizer.decode([]) == ""
```
