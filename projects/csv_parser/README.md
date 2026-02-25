# Project 8: CSV Parser + Streaming Aggregation

**Key Points**:
- State machine design with clear transitions and invariants
- Streaming/windowed aggregation comfort
- Handling dirty/malformed data gracefully

## Level 1: CSV Parser State Machine

**Implement a class `CSVParser`:**

```
class CSVParser:
    __init__(delimiter: str = ",", quotechar: str = '"') -> None
    parse_row(line: str) -> list[str]              # parse a single CSV line into fields
    parse(text: str) -> list[list[str]]            # parse multi-line CSV text
```

**Assumptions to state:**
- Escaped quotes use the doubled-quote convention: `""` inside a quoted field
- Whitespace is preserved, not trimmed
- Empty fields are valid: `a,,c` -> `["a", "", "c"]`

**Requirements:**
- Handle basic comma-separated values: `a,b,c` -> `["a", "b", "c"]`
- Handle quoted fields: `"hello, world",b` -> `["hello, world", "b"]`
- Handle escaped quotes (doubled): `"say ""hi""",b` -> `['say "hi"', "b"]`
- Handle newlines inside quoted fields: `"line1\nline2",b` -> `["line1\nline2", "b"]`
- Handle empty fields: `a,,c` -> `["a", "", "c"]`
- Handle trailing delimiter: `a,b,` -> `["a", "b", ""]`
- Whitespace is preserved (not trimmed)
- Implement as a **state machine** with explicit states: `FIELD_START`, `UNQUOTED`, `QUOTED`, `QUOTE_IN_QUOTED`

**State transitions (narrate these as you code):**
```
FIELD_START --["]-->   QUOTED
FIELD_START --[,]-->   FIELD_START (emit empty field)
FIELD_START --[char]--> UNQUOTED

UNQUOTED --[,]--> FIELD_START (emit field)
UNQUOTED --[char]--> UNQUOTED

QUOTED --["]--> QUOTE_IN_QUOTED
QUOTED --[char]--> QUOTED

QUOTE_IN_QUOTED --["]--> QUOTED (escaped quote)
QUOTE_IN_QUOTED --[,]--> FIELD_START (emit field)
QUOTE_IN_QUOTED --[EOF]--> (emit field)
```

**Invariants to mention:**
- Every state transition either appends to the current field or emits it
- At EOF, the current field is always emitted (handles trailing content)
- The state machine is O(n) single-pass — no backtracking

**Test Cases:**
```python
parser = CSVParser()
assert parser.parse_row('a,b,c') == ['a', 'b', 'c']
assert parser.parse_row('"hello, world",b') == ['hello, world', 'b']
assert parser.parse_row('"say ""hi""",b') == ['say "hi"', 'b']
assert parser.parse_row('a,,c') == ['a', '', 'c']
assert parser.parse_row('a,b,') == ['a', 'b', '']
assert parser.parse_row('') == ['']
```

---

## Level 2: Streaming Row Iterator

**Extend with a streaming interface:**

```
class CSVStream:
    __init__(parser: CSVParser, header: bool = True) -> None
    iter_rows(source: Iterable[str]) -> Iterator[dict[str, str]]
    iter_rows_from_file(filepath: str) -> Iterator[dict[str, str]]
```

**Clarification questions to ask:**
- How large is the file? (motivates streaming vs load-all)
- Should I auto-detect types (int/float) or keep everything as strings?
- What if a row has more/fewer columns than the header?
- Is the data clean, or should I expect malformed rows?

**Assumptions to state:**
- File could be large, so we stream line-by-line (generator-based, O(1) memory)
- Mismatched columns: extra fields truncated, missing fields filled with `""`
- Type coercion: attempt `int`, then `float`, then keep as `str`

**Requirements:**
- `source` is any iterable of strings (lines), enabling streaming from files/network
- If `header=True`, first row is used as column names; yields `dict` per row
- If `header=False`, yields `list` per row
- **Generator-based**: never loads full file into memory
- Handle rows that span multiple lines (quoted newlines)
- Handle mismatched column count: extra fields are truncated, missing fields are empty string
- Type coercion: auto-detect int, float, or keep as string

**Key design point** — handling multi-line quoted fields in a streaming context:
- You can't just `for line in source` — a single CSV row may span multiple lines
- Need a line accumulator: if a line has an unclosed quote, keep reading until the quote closes
- This is a common follow-up question

**Test Cases:**
```python
parser = CSVParser()
stream = CSVStream(parser)
lines = ["name,age,city", "Alice,30,NYC", "Bob,25,LA"]
rows = list(stream.iter_rows(iter(lines)))
assert rows == [
    {"name": "Alice", "age": 30, "city": "NYC"},
    {"name": "Bob", "age": 25, "city": "LA"},
]

# Mismatched columns
lines2 = ["a,b", "1,2,3", "4"]
rows2 = list(stream.iter_rows(iter(lines2)))
assert rows2 == [{"a": 1, "b": 2}, {"a": 4, "b": ""}]
```

---

## Level 3: Windowed Aggregation

**Implement windowed aggregation over streaming rows:**

```
class WindowAggregator:
    __init__(window_type: str, window_size: float, time_column: str) -> None
    add_row(row: dict) -> list[dict] | None   # returns completed window results
    flush() -> list[dict]                      # flush remaining incomplete window
```

**Clarification questions to ask:**
- Are timestamps guaranteed to be sorted / monotonically increasing?
- What aggregations do you want? (count, sum, avg, min, max?)
- For tumbling windows — are boundaries aligned to epoch (0, size, 2*size...) or relative to first row?
- Should I handle the case where a single row triggers multiple window closes?

**Assumptions to state:**
- Timestamps arrive in order (for now — Level 4 relaxes this)
- Window boundaries are epoch-aligned: `[0, size), [size, 2*size), ...`
- Aggregate all numeric columns automatically

**Requirements:**
- `window_type`: `"tumbling"` or `"sliding"`
- `window_size`: window duration in seconds
- `time_column`: name of the column containing timestamps (epoch float or ISO string)
- **Tumbling window**: non-overlapping fixed windows
  - Window boundaries: `[0, size), [size, 2*size), ...`
  - When a row arrives beyond the current window, emit the completed window
- **Sliding window**: window slides with each new row
  - For each new row, include all rows within `window_size` seconds before it
  - Emit aggregate for each row
- Aggregation functions: `count`, `sum`, `avg`, `min`, `max` per numeric column
- `add_row()` returns completed window result when a window closes, `None` otherwise

**Test Cases:**
```python
agg = WindowAggregator(window_type="tumbling", window_size=10, time_column="ts")
result = agg.add_row({"ts": 1.0, "value": 10})
assert result is None  # window not complete
result = agg.add_row({"ts": 5.0, "value": 20})
assert result is None  # still in [0, 10) window
result = agg.add_row({"ts": 12.0, "value": 30})
# Window [0, 10) is complete
assert result[0]["count"] == 2
assert result[0]["sum_value"] == 30
assert result[0]["avg_value"] == 15.0
```

---

## Level 4: Multi-Key Group-By + Late-Arriving Data

*Unlikely to code in interview — good for discussion / "how would you extend this?"*

**Extend `WindowAggregator`:**

```
__init__(..., group_by: list[str] | None = None, allowed_lateness: float = 0) -> None
```

**Clarification questions to ask:**
- How late can data arrive? Is there a watermark?
- When a late row updates a closed window, should I re-emit the updated result?
- How do I signal that a row was dropped?

**Requirements:**
- `group_by`: columns to group by before aggregating (e.g. `["city"]`)
  - Each group maintains its own window state
  - Results include the group key values
- `allowed_lateness`: seconds of slack for late-arriving data
  - Rows arriving within `allowed_lateness` after window close are still included
  - Windows are kept open for `allowed_lateness` duration after they would normally close
  - Rows arriving after the lateness threshold are dropped (return a "dropped" indicator)
- Handle out-of-order data within allowed lateness
- Multiple groups should emit independently

**Test Cases:**
```python
agg = WindowAggregator(
    window_type="tumbling", window_size=10, time_column="ts",
    group_by=["city"], allowed_lateness=5.0
)
agg.add_row({"ts": 1.0, "city": "NYC", "value": 10})
agg.add_row({"ts": 2.0, "city": "LA", "value": 20})
agg.add_row({"ts": 12.0, "city": "NYC", "value": 30})  # triggers NYC window [0,10)
# But LA window [0,10) still open due to lateness allowance
agg.add_row({"ts": 8.0, "city": "LA", "value": 25})  # late but within lateness
result = agg.add_row({"ts": 16.0, "city": "LA", "value": 40})
# LA window [0,10) now emitted with both rows
```
