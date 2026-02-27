# Project: CSV Parser + Streaming Aggregation

**Core skills tested**: State machine design, streaming/iterator patterns, windowed aggregation

## Level 1: CSV Parser State Machine

**Implement a class `CSVParser`:**

```
class CSVParser:
    __init__(delimiter: str = ",", quote: str = '"') -> None
    parse_row(row: str) -> list                    # parse a single CSV row into fields
    parse(text: list[str]) -> list[list]           # parse all rows (load all into memory)
```

**Assumptions:**
- No newlines inside quoted fields (each line = one row)
- Escaped quotes use the doubled-quote convention: `""` inside a quoted field
- Whitespace is preserved, not trimmed
- Empty fields are valid: `a,,c` -> `["a", "", "c"]`
- Type coercion: attempt `int`, then `float`, then keep as `str`

**Requirements:**
- Handle basic comma-separated values: `a,b,c` -> `["a", "b", "c"]`
- Handle quoted fields: `"hello, world",b` -> `["hello, world", "b"]`
- Handle escaped quotes (doubled): `"say ""hi""",b` -> `['say "hi"', "b"]`
- Handle empty fields: `a,,c` -> `["a", "", "c"]`
- Handle trailing delimiter: `a,b,` -> `["a", "b", ""]`
- Type coercion on each field (int > float > str)
- Implement as a **state machine** with explicit states: `START`, `QUOTE`, `UNQUOTE`, `QUOTE_IN_QUOTE`

**State transitions:**
```
START --[quote]-->     QUOTE
START --[delimiter]--> START (emit empty field)
START --[char]-->      UNQUOTE

UNQUOTE --[delimiter]--> START (emit field)
UNQUOTE --[char]-->      UNQUOTE

QUOTE --[quote]--> QUOTE_IN_QUOTE
QUOTE --[char]-->  QUOTE

QUOTE_IN_QUOTE --[quote]-->     QUOTE (escaped quote)
QUOTE_IN_QUOTE --[delimiter]--> START (emit field)
QUOTE_IN_QUOTE --[EOF]-->       (emit field)
```

**Test Cases:**
```python
parser = CSVParser()
assert parser.parse_row('a,b,c') == ['a', 'b', 'c']
assert parser.parse_row('"hello, world",b') == ['hello, world', 'b']
assert parser.parse_row('"say ""hi""",b') == ['say "hi"', 'b']
assert parser.parse_row('a,,c') == ['a', '', 'c']
assert parser.parse_row('a,b,') == ['a', 'b', '']
assert parser.parse_row('') == ['']
assert parser.parse_row('10,3.14,hello') == [10, 3.14, 'hello']
```

---

## Level 2: Streaming Iterator

**Extend `CSVParser` with a streaming interface:**

```
class CSVParser:
    ...
    iter(source: Iterable[str]) -> Iterator[list]          # stream parsed rows
    iter_from_file(filepath: str) -> Iterator[list]        # stream from file
```
**Assumptions:**
- File could be large, so we stream line-by-line (generator-based, O(1) memory)
- Each line is one complete CSV row (no newlines in cells)

**Requirements:**
- `iter()` takes any iterable of strings and yields parsed rows using `yield`
- Generator-based: never loads full file into memory
- `iter_from_file()` opens a file and delegates to `iter()` using `yield from`
- Rows are stripped of trailing newlines before parsing

**Key design point:**
- `parse()` loads all rows into memory — fine for small files
- `iter()` yields one row at a time — O(1) memory for any file size
- Interview progression: start with `parse()`, refactor to `iter()` when asked about large files

**Test Cases:**
```python
parser = CSVParser()

# Streaming from list
rows = list(parser.iter(iter(["a,b,c", "1,2,3"])))
assert rows == [["a", "b", "c"], [1, 2, 3]]

# Generator-based (doesn't load all at once)
def infinite_lines():
    i = 0
    while True:
        yield f"{i},{i*10}"
        i += 1

gen = parser.iter(infinite_lines())
assert next(gen) == [0, 0]
assert next(gen) == [1, 10]
```

---

## Level 3: Windowed Aggregation

**Implement tumbling window aggregation over streaming rows:**

```
class WindowAggregator:
    __init__(window_size: float, ts_index: int, val_index: int) -> None
    add_row(row: list) -> dict | None       # returns result when window completes
    flush() -> dict | None                  # flush remaining incomplete window
```

**Assumptions:**
- Timestamps arrive in sorted order
- Window boundaries are epoch-aligned: `[0, size), [size, 2*size), ...`
- Aggregate a single numeric column specified by index

**Requirements:**
- `window_size`: window duration in seconds
- `ts_index`: column index for timestamp field
- `val_index`: column index for numeric value to aggregate
- **Tumbling window**: non-overlapping fixed windows
  - When a row arrives beyond the current window, emit the completed window
  - The triggering row belongs to the next window
- `add_row()` returns a dict when a window closes, `None` otherwise
- `flush()` emits whatever is accumulated (for end-of-data), `None` if empty
- Result dict contains: `window_start`, `window_end`, `count`, `sum`, `avg`, `min`, `max`

**End-to-end pipeline:**
```
CSV File -> parser.iter_from_file() -> agg.add_row() -> windowed results
```

**Test Cases:**
```python
# Basic tumbling window
agg = WindowAggregator(window_size=10, ts_index=1, val_index=0)
assert agg.add_row([10, 1.0]) is None
assert agg.add_row([20, 5.0]) is None
result = agg.add_row([30, 12.0])
# Window [0, 10) complete
assert result["count"] == 2
assert result["sum"] == 30
assert result["avg"] == 15.0

# Flush incomplete window
agg2 = WindowAggregator(window_size=10, ts_index=1, val_index=0)
agg2.add_row([10, 1.0])
agg2.add_row([20, 5.0])
result = agg2.flush()
assert result["count"] == 2

# Empty flush
agg3 = WindowAggregator(window_size=10, ts_index=1, val_index=0)
assert agg3.flush() is None

# End-to-end: stream CSV -> aggregate
parser = CSVParser()
agg4 = WindowAggregator(window_size=10, ts_index=3, val_index=2)
for row in parser.iter_from_file("example.csv"):
    result = agg4.add_row(row)
    if result:
        print(result)
remaining = agg4.flush()
```
