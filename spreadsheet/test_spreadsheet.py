"""
Tests for Spreadsheet Engine (Project 6)
Run: pytest test_spreadsheet.py -k "TestLevel1" -v
"""

import pytest

from spreadsheet import Spreadsheet, CircularReferenceError


# ============================================================
# Level 1: Cell Storage
# ============================================================

class TestLevel1:
    def test_set_and_get_integer(self):
        ss = Spreadsheet()
        ss.set("A1", 42)
        assert ss.get("A1") == 42

    def test_set_and_get_float(self):
        ss = Spreadsheet()
        ss.set("A1", 3.14)
        assert ss.get("A1") == 3.14

    def test_set_and_get_string(self):
        ss = Spreadsheet()
        ss.set("A1", "hello")
        assert ss.get("A1") == "hello"

    def test_get_unset_cell_returns_none(self):
        ss = Spreadsheet()
        assert ss.get("A1") is None
        assert ss.get("Z9") is None

    def test_overwrite_cell(self):
        ss = Spreadsheet()
        ss.set("A1", 10)
        ss.set("A1", 20)
        assert ss.get("A1") == 20

    def test_overwrite_with_different_type(self):
        ss = Spreadsheet()
        ss.set("A1", 42)
        ss.set("A1", "hello")
        assert ss.get("A1") == "hello"

    def test_clear_cell_with_none(self):
        ss = Spreadsheet()
        ss.set("A1", 42)
        ss.set("A1", None)
        assert ss.get("A1") is None

    def test_multiple_cells(self):
        ss = Spreadsheet()
        ss.set("A1", 1)
        ss.set("B1", 2)
        ss.set("A2", 3)
        assert ss.get("A1") == 1
        assert ss.get("B1") == 2
        assert ss.get("A2") == 3

    def test_invalid_cell_address(self):
        ss = Spreadsheet()
        with pytest.raises(ValueError):
            ss.set("", 1)
        with pytest.raises(ValueError):
            ss.set("1A", 1)
        with pytest.raises(ValueError):
            ss.set("A0", 1)
        with pytest.raises(ValueError):
            ss.set("AA1", 1)  # multi-letter columns not required

    def test_case_insensitive_cell_address(self):
        ss = Spreadsheet()
        ss.set("a1", 42)
        assert ss.get("A1") == 42

    def test_various_columns(self):
        ss = Spreadsheet()
        for col in "ABCDEFGHIJKLMNOPQRSTUVWXYZ":
            ss.set(f"{col}1", ord(col))
        for col in "ABCDEFGHIJKLMNOPQRSTUVWXYZ":
            assert ss.get(f"{col}1") == ord(col)

    def test_large_row_number(self):
        ss = Spreadsheet()
        ss.set("A100", 99)
        assert ss.get("A100") == 99


# ============================================================
# Level 2: Formula Evaluation
# ============================================================

class TestLevel2:
    def test_simple_addition(self):
        ss = Spreadsheet()
        ss.set("A1", 10)
        ss.set("A2", 20)
        ss.set("A3", "=A1+A2")
        assert ss.get("A3") == 30

    def test_simple_subtraction(self):
        ss = Spreadsheet()
        ss.set("A1", 50)
        ss.set("A2", 20)
        ss.set("A3", "=A1-A2")
        assert ss.get("A3") == 30

    def test_multiplication(self):
        ss = Spreadsheet()
        ss.set("A1", 5)
        ss.set("A2", 6)
        ss.set("A3", "=A1*A2")
        assert ss.get("A3") == 30

    def test_division(self):
        ss = Spreadsheet()
        ss.set("A1", 100)
        ss.set("A2", 4)
        ss.set("A3", "=A1/A2")
        assert ss.get("A3") == 25.0

    def test_formula_with_literal(self):
        ss = Spreadsheet()
        ss.set("A1", 10)
        ss.set("A2", "=A1+5")
        assert ss.get("A2") == 15

    def test_formula_with_parentheses(self):
        ss = Spreadsheet()
        ss.set("A1", 2)
        ss.set("B1", 3)
        ss.set("C1", "=(A1+B1)*4")
        assert ss.get("C1") == 20

    def test_empty_cell_treated_as_zero(self):
        ss = Spreadsheet()
        ss.set("A1", 10)
        ss.set("A2", "=A1+B1")  # B1 is empty
        assert ss.get("A2") == 10

    def test_formula_re_evaluates_on_change(self):
        ss = Spreadsheet()
        ss.set("A1", 10)
        ss.set("A2", "=A1*2")
        assert ss.get("A2") == 20
        ss.set("A1", 5)
        assert ss.get("A2") == 10

    def test_chained_formulas(self):
        ss = Spreadsheet()
        ss.set("A1", 1)
        ss.set("B1", "=A1+1")
        ss.set("C1", "=B1+1")
        assert ss.get("C1") == 3

    def test_division_by_zero(self):
        ss = Spreadsheet()
        ss.set("A1", 10)
        ss.set("A2", 0)
        ss.set("A3", "=A1/A2")
        with pytest.raises(ValueError):
            ss.get("A3")

    def test_only_literal_formula(self):
        ss = Spreadsheet()
        ss.set("A1", "=42")
        assert ss.get("A1") == 42

    def test_complex_expression(self):
        ss = Spreadsheet()
        ss.set("A1", 2)
        ss.set("B1", 3)
        ss.set("C1", 4)
        ss.set("D1", "=A1+B1*C1")  # should be 2 + 12 = 14 (operator precedence)
        assert ss.get("D1") == 14

    def test_formula_referencing_formula(self):
        ss = Spreadsheet()
        ss.set("A1", 5)
        ss.set("B1", "=A1*2")
        ss.set("C1", "=B1+3")
        assert ss.get("C1") == 13


# ============================================================
# Level 3: Dependency Graph + Circular Reference Detection
# ============================================================

class TestLevel3:
    def test_get_dependencies(self):
        ss = Spreadsheet()
        ss.set("A1", 1)
        ss.set("B1", "=A1+1")
        deps = ss.get_dependencies("B1")
        assert deps == {"A1"}

    def test_no_dependencies_for_literal(self):
        ss = Spreadsheet()
        ss.set("A1", 42)
        deps = ss.get_dependencies("A1")
        assert deps == set()

    def test_multiple_dependencies(self):
        ss = Spreadsheet()
        ss.set("A1", 1)
        ss.set("B1", 2)
        ss.set("C1", "=A1+B1")
        deps = ss.get_dependencies("C1")
        assert deps == {"A1", "B1"}

    def test_self_reference_detected(self):
        ss = Spreadsheet()
        with pytest.raises(CircularReferenceError):
            ss.set("A1", "=A1")

    def test_two_cell_cycle_detected(self):
        ss = Spreadsheet()
        ss.set("A1", "=B1+1")
        with pytest.raises(CircularReferenceError):
            ss.set("B1", "=A1+1")

    def test_long_cycle_detected(self):
        ss = Spreadsheet()
        ss.set("A1", 1)
        ss.set("B1", "=A1+1")
        ss.set("C1", "=B1+1")
        with pytest.raises(CircularReferenceError):
            ss.set("A1", "=C1+1")  # A1 -> C1 -> B1 -> A1

    def test_cell_unchanged_after_cycle_error(self):
        ss = Spreadsheet()
        ss.set("A1", 10)
        ss.set("B1", "=A1+1")
        try:
            ss.set("A1", "=B1")
        except CircularReferenceError:
            pass
        assert ss.get("A1") == 10  # unchanged

    def test_dependent_cells_update(self):
        ss = Spreadsheet()
        ss.set("A1", 1)
        ss.set("B1", "=A1+1")
        ss.set("C1", "=B1+1")
        assert ss.get("C1") == 3
        ss.set("A1", 10)
        assert ss.get("B1") == 11
        assert ss.get("C1") == 12

    def test_no_false_cycle_after_overwrite(self):
        """Overwriting a formula should update the dependency graph."""
        ss = Spreadsheet()
        ss.set("A1", 1)
        ss.set("B1", "=A1+1")
        ss.set("B1", 42)  # overwrite formula with literal
        # Now A1 can reference B1 without a cycle
        ss.set("A1", "=B1+1")
        assert ss.get("A1") == 43

    def test_unset_cell_dependency(self):
        ss = Spreadsheet()
        ss.set("A1", "=Z9+1")
        deps = ss.get_dependencies("A1")
        assert deps == {"Z9"}
        assert ss.get("A1") == 1  # Z9 is empty = 0


# ============================================================
# Level 4: Bulk Update + Topological Evaluation Order
# ============================================================

class TestLevel4:
    def test_bulk_set_basic(self):
        ss = Spreadsheet()
        ss.bulk_set({"A1": 1, "B1": 2, "C1": "=A1+B1"})
        assert ss.get("C1") == 3

    def test_bulk_set_atomic_on_cycle(self):
        """If any cell in bulk_set creates a cycle, none are applied."""
        ss = Spreadsheet()
        ss.set("A1", 1)
        ss.set("B1", "=A1")
        with pytest.raises(CircularReferenceError):
            ss.bulk_set({"A1": "=B1", "C1": 99})
        assert ss.get("A1") == 1    # unchanged
        assert ss.get("C1") is None  # C1 was not set

    def test_evaluation_order_simple(self):
        ss = Spreadsheet()
        ss.set("A1", 1)
        ss.set("B1", "=A1+1")
        ss.set("C1", "=B1+1")
        order = ss.get_evaluation_order()
        # B1 must come before C1
        assert order.index("B1") < order.index("C1")

    def test_evaluation_order_diamond(self):
        ss = Spreadsheet()
        ss.set("A1", 1)
        ss.set("B1", "=A1+1")
        ss.set("C1", "=A1+2")
        ss.set("D1", "=B1+C1")
        order = ss.get_evaluation_order()
        assert order.index("B1") < order.index("D1")
        assert order.index("C1") < order.index("D1")

    def test_bulk_set_with_interdependencies(self):
        """Bulk set where new cells reference each other."""
        ss = Spreadsheet()
        ss.bulk_set({
            "A1": 10,
            "B1": "=A1*2",
            "C1": "=B1+5",
        })
        assert ss.get("B1") == 20
        assert ss.get("C1") == 25

    def test_evaluation_order_only_formula_cells(self):
        """Evaluation order should only include formula cells."""
        ss = Spreadsheet()
        ss.set("A1", 1)
        ss.set("B1", 2)
        ss.set("C1", "=A1+B1")
        order = ss.get_evaluation_order()
        assert "C1" in order
        assert "A1" not in order  # literal cells not in eval order
        assert "B1" not in order

    def test_bulk_set_updates_dependents(self):
        ss = Spreadsheet()
        ss.set("A1", 1)
        ss.set("B1", "=A1+1")
        ss.set("C1", "=B1+1")
        assert ss.get("C1") == 3
        ss.bulk_set({"A1": 10})
        assert ss.get("B1") == 11
        assert ss.get("C1") == 12
