# Project 6: Spreadsheet Engine

## Level 1: Cell Storage

**Implement a class `Spreadsheet`:**

```
class Spreadsheet:
    __init__() -> None
    set(cell: str, value) -> None              # set cell value, e.g. set("A1", 42)
    get(cell: str) -> int | float | str | None  # get cell value
```

**Requirements:**
- Cell addresses use Excel-style notation: column letter(s) + row number (e.g. "A1", "B12", "Z3")
- Support columns A-Z (single letter is fine for now)
- Row numbers start at 1
- Supported value types: `int`, `float`, `str`
- Getting an unset cell returns `None`
- Setting a cell to `None` clears it
- Invalid cell addresses should raise `ValueError`

**Test Cases:**
```python
ss = Spreadsheet()
ss.set("A1", 42)
assert ss.get("A1") == 42
assert ss.get("B1") is None   # unset cell
ss.set("A1", "hello")         # overwrite
assert ss.get("A1") == "hello"
```

---

## Level 2: Formula Evaluation

**Extend `Spreadsheet`:**

```
set(cell: str, value) -> None  # value can be a formula string starting with "="
get(cell: str)                 # evaluates formula if cell contains one
```

**Requirements:**
- Formulas start with `=` (e.g. `"=A1+B2"`, `"=A1*2+B2"`)
- Support operators: `+`, `-`, `*`, `/`
- Support cell references in formulas (e.g. `A1`, `B2`)
- Support numeric literals in formulas (e.g. `=A1+10`)
- Support parentheses for grouping (e.g. `=(A1+B1)*2`)
- If a referenced cell is empty, treat as 0
- Division by zero should raise `ValueError`
- Invalid formula syntax should raise `ValueError`
- `get()` always returns the evaluated result, not the raw formula

**Test Cases:**
```python
ss = Spreadsheet()
ss.set("A1", 10)
ss.set("A2", 20)
ss.set("A3", "=A1+A2")
assert ss.get("A3") == 30
ss.set("A1", 5)         # change A1
assert ss.get("A3") == 25  # A3 re-evaluates
```

---

## Level 3: Dependency Graph + Topological Sort

**Extend `Spreadsheet`:**

```
get_dependencies(cell: str) -> set[str]  # cells that this cell depends on
```

**Requirements:**
- Build a dependency graph: track which cells depend on which
- When a cell's value changes, all dependent cells should reflect the new value
- Circular references should raise `CircularReferenceError` (custom exception)
  - `=A1` in A1 (self-reference)
  - A1 depends on B1, B1 depends on A1
  - Longer cycles: A1 -> B1 -> C1 -> A1
- Detect circular references at `set()` time, not at `get()` time
- Setting a formula that would create a cycle should raise and leave the cell unchanged

**Test Cases:**
```python
ss = Spreadsheet()
ss.set("A1", 1)
ss.set("B1", "=A1+1")
ss.set("C1", "=B1+1")
assert ss.get("C1") == 3
assert ss.get_dependencies("C1") == {"B1"}

# Circular reference detection
with pytest.raises(CircularReferenceError):
    ss.set("A1", "=C1")  # A1 -> C1 -> B1 -> A1
assert ss.get("A1") == 1  # A1 unchanged after failed set
```

---

## Level 4: Bulk Update + Topological Evaluation Order

**Extend `Spreadsheet`:**

```
bulk_set(updates: dict[str, any]) -> None  # set multiple cells atomically
get_evaluation_order() -> list[str]         # topological order of all formula cells
```

**Requirements:**
- `bulk_set` applies multiple cell updates atomically
  - If any update would create a circular reference, none of the updates are applied
  - All dependent cells are re-evaluated in correct topological order
- `get_evaluation_order` returns cells in an order where dependencies come first
- Handle diamond dependencies (A1 depends on B1 and C1, both depend on D1)
- Performance: changing one cell should only re-evaluate affected cells, not all formulas

**Test Cases:**
```python
ss = Spreadsheet()
ss.bulk_set({"A1": 1, "B1": 2, "C1": "=A1+B1"})
assert ss.get("C1") == 3

# Diamond dependency
ss.set("D1", "=A1+B1")
ss.set("E1", "=C1+D1")
order = ss.get_evaluation_order()
assert order.index("C1") < order.index("E1")
assert order.index("D1") < order.index("E1")
```
