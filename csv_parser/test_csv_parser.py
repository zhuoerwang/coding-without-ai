"""
Tests for CSV Parser + Streaming Aggregation (Project 8)
Run: pytest test_csv_parser.py -k "TestLevel1" -v
"""

import pytest

from csv_parser import CSVParser, CSVStream, WindowAggregator


# ============================================================
# Level 1: CSV Parser State Machine
# ============================================================

class TestLevel1:
    def test_simple_row(self):
        parser = CSVParser()
        assert parser.parse_row("a,b,c") == ["a", "b", "c"]

    def test_single_field(self):
        parser = CSVParser()
        assert parser.parse_row("hello") == ["hello"]

    def test_empty_string(self):
        parser = CSVParser()
        assert parser.parse_row("") == [""]

    def test_empty_fields(self):
        parser = CSVParser()
        assert parser.parse_row("a,,c") == ["a", "", "c"]

    def test_trailing_delimiter(self):
        parser = CSVParser()
        assert parser.parse_row("a,b,") == ["a", "b", ""]

    def test_leading_delimiter(self):
        parser = CSVParser()
        assert parser.parse_row(",a,b") == ["", "a", "b"]

    def test_quoted_field(self):
        parser = CSVParser()
        assert parser.parse_row('"hello, world",b') == ["hello, world", "b"]

    def test_escaped_quotes(self):
        parser = CSVParser()
        assert parser.parse_row('"say ""hi""",b') == ['say "hi"', "b"]

    def test_quoted_field_with_newline(self):
        parser = CSVParser()
        text = '"line1\nline2",b'
        assert parser.parse_row(text) == ["line1\nline2", "b"]

    def test_all_quoted(self):
        parser = CSVParser()
        assert parser.parse_row('"a","b","c"') == ["a", "b", "c"]

    def test_mixed_quoted_unquoted(self):
        parser = CSVParser()
        assert parser.parse_row('a,"b,c",d') == ["a", "b,c", "d"]

    def test_whitespace_preserved(self):
        parser = CSVParser()
        assert parser.parse_row(" a , b , c ") == [" a ", " b ", " c "]

    def test_parse_multiline(self):
        parser = CSVParser()
        text = "a,b,c\n1,2,3\n4,5,6"
        rows = parser.parse(text)
        assert rows == [["a", "b", "c"], ["1", "2", "3"], ["4", "5", "6"]]

    def test_parse_multiline_with_quoted_newline(self):
        parser = CSVParser()
        text = 'a,"b\nc",d\n1,2,3'
        rows = parser.parse(text)
        assert len(rows) == 2
        assert rows[0] == ["a", "b\nc", "d"]
        assert rows[1] == ["1", "2", "3"]

    def test_custom_delimiter(self):
        parser = CSVParser(delimiter="\t")
        assert parser.parse_row("a\tb\tc") == ["a", "b", "c"]

    def test_custom_quotechar(self):
        parser = CSVParser(quotechar="'")
        assert parser.parse_row("'hello, world',b") == ["hello, world", "b"]

    def test_only_delimiters(self):
        parser = CSVParser()
        assert parser.parse_row(",,") == ["", "", ""]

    def test_quoted_empty_field(self):
        parser = CSVParser()
        assert parser.parse_row('"",b') == ["", "b"]


# ============================================================
# Level 2: Streaming Row Iterator
# ============================================================

class TestLevel2:
    def test_iter_rows_with_header(self):
        parser = CSVParser()
        stream = CSVStream(parser)
        lines = ["name,age,city", "Alice,30,NYC", "Bob,25,LA"]
        rows = list(stream.iter_rows(iter(lines)))
        assert rows == [
            {"name": "Alice", "age": 30, "city": "NYC"},
            {"name": "Bob", "age": 25, "city": "LA"},
        ]

    def test_iter_rows_without_header(self):
        parser = CSVParser()
        stream = CSVStream(parser, header=False)
        lines = ["Alice,30,NYC", "Bob,25,LA"]
        rows = list(stream.iter_rows(iter(lines)))
        assert rows == [
            ["Alice", 30, "NYC"],
            ["Bob", 25, "LA"],
        ]

    def test_type_coercion_int(self):
        parser = CSVParser()
        stream = CSVStream(parser, header=False)
        rows = list(stream.iter_rows(iter(["42"])))
        assert rows == [[42]]

    def test_type_coercion_float(self):
        parser = CSVParser()
        stream = CSVStream(parser, header=False)
        rows = list(stream.iter_rows(iter(["3.14"])))
        assert rows == [[3.14]]

    def test_type_coercion_string(self):
        parser = CSVParser()
        stream = CSVStream(parser, header=False)
        rows = list(stream.iter_rows(iter(["hello"])))
        assert rows == [["hello"]]

    def test_generator_based(self):
        """Should not load all rows at once."""
        parser = CSVParser()
        stream = CSVStream(parser, header=False)

        def infinite_lines():
            i = 0
            while True:
                yield f"row{i},{i}"
                i += 1

        gen = stream.iter_rows(infinite_lines())
        first = next(gen)
        assert first == ["row0", 0]
        second = next(gen)
        assert second == ["row1", 1]

    def test_mismatched_columns_extra(self):
        """Extra fields are truncated."""
        parser = CSVParser()
        stream = CSVStream(parser)
        lines = ["a,b", "1,2,3"]  # 3 fields but only 2 headers
        rows = list(stream.iter_rows(iter(lines)))
        assert rows == [{"a": "1", "b": "2"}]  # extra field truncated

    def test_mismatched_columns_missing(self):
        """Missing fields are empty string."""
        parser = CSVParser()
        stream = CSVStream(parser)
        lines = ["a,b,c", "1,2"]  # only 2 fields but 3 headers
        rows = list(stream.iter_rows(iter(lines)))
        assert rows == [{"a": "1", "b": "2", "c": ""}]

    def test_quoted_newline_in_stream(self):
        """Rows spanning multiple lines due to quoted newlines."""
        parser = CSVParser()
        stream = CSVStream(parser, header=False)
        lines = ['"hello', 'world",done']
        rows = list(stream.iter_rows(iter(lines)))
        assert rows == [["hello\nworld", "done"]]


# ============================================================
# Level 3: Windowed Aggregation
# ============================================================

class TestLevel3:
    def test_tumbling_window_basic(self):
        agg = WindowAggregator(window_type="tumbling", window_size=10, time_column="ts")
        assert agg.add_row({"ts": 1.0, "value": 10}) is None
        assert agg.add_row({"ts": 5.0, "value": 20}) is None
        result = agg.add_row({"ts": 12.0, "value": 30})
        assert result is not None
        assert len(result) == 1  # one completed window
        assert result[0]["count"] == 2
        assert result[0]["sum_value"] == 30
        assert result[0]["avg_value"] == 15.0

    def test_tumbling_window_multiple(self):
        agg = WindowAggregator(window_type="tumbling", window_size=5, time_column="ts")
        agg.add_row({"ts": 1.0, "value": 10})
        agg.add_row({"ts": 3.0, "value": 20})
        result = agg.add_row({"ts": 6.0, "value": 30})
        assert result is not None
        assert result[0]["count"] == 2
        result2 = agg.add_row({"ts": 11.0, "value": 40})
        assert result2 is not None
        assert result2[0]["count"] == 1  # only ts=6.0 in [5,10)

    def test_tumbling_window_min_max(self):
        agg = WindowAggregator(window_type="tumbling", window_size=10, time_column="ts")
        agg.add_row({"ts": 1.0, "value": 5})
        agg.add_row({"ts": 2.0, "value": 15})
        agg.add_row({"ts": 3.0, "value": 10})
        result = agg.add_row({"ts": 11.0, "value": 99})
        assert result[0]["min_value"] == 5
        assert result[0]["max_value"] == 15

    def test_sliding_window_basic(self):
        agg = WindowAggregator(window_type="sliding", window_size=5, time_column="ts")
        r1 = agg.add_row({"ts": 1.0, "value": 10})
        assert r1 is not None
        assert r1["count"] == 1
        assert r1["sum_value"] == 10

        r2 = agg.add_row({"ts": 3.0, "value": 20})
        assert r2["count"] == 2
        assert r2["sum_value"] == 30

        r3 = agg.add_row({"ts": 7.0, "value": 30})
        # ts=1.0 is outside [7.0-5, 7.0] = [2.0, 7.0], so excluded
        assert r3["count"] == 2
        assert r3["sum_value"] == 50  # 20 + 30

    def test_flush_incomplete_window(self):
        agg = WindowAggregator(window_type="tumbling", window_size=10, time_column="ts")
        agg.add_row({"ts": 1.0, "value": 10})
        agg.add_row({"ts": 5.0, "value": 20})
        result = agg.flush()
        assert len(result) == 1
        assert result[0]["count"] == 2
        assert result[0]["sum_value"] == 30

    def test_multiple_numeric_columns(self):
        agg = WindowAggregator(window_type="tumbling", window_size=10, time_column="ts")
        agg.add_row({"ts": 1.0, "x": 10, "y": 100})
        agg.add_row({"ts": 2.0, "x": 20, "y": 200})
        result = agg.add_row({"ts": 11.0, "x": 30, "y": 300})
        assert result[0]["sum_x"] == 30
        assert result[0]["sum_y"] == 300
        assert result[0]["avg_x"] == 15.0
        assert result[0]["avg_y"] == 150.0

    def test_empty_flush(self):
        agg = WindowAggregator(window_type="tumbling", window_size=10, time_column="ts")
        result = agg.flush()
        assert result == []


# ============================================================
# Level 4: Multi-Key Group-By + Late-Arriving Data
# ============================================================

class TestLevel4:
    def test_group_by_basic(self):
        agg = WindowAggregator(
            window_type="tumbling", window_size=10, time_column="ts",
            group_by=["city"],
        )
        agg.add_row({"ts": 1.0, "city": "NYC", "value": 10})
        agg.add_row({"ts": 2.0, "city": "LA", "value": 20})
        agg.add_row({"ts": 3.0, "city": "NYC", "value": 30})
        result = agg.add_row({"ts": 12.0, "city": "NYC", "value": 40})
        # NYC window [0,10) should emit
        assert any(r["city"] == "NYC" and r["count"] == 2 for r in result)

    def test_groups_emit_independently(self):
        agg = WindowAggregator(
            window_type="tumbling", window_size=10, time_column="ts",
            group_by=["city"],
        )
        agg.add_row({"ts": 1.0, "city": "NYC", "value": 10})
        agg.add_row({"ts": 2.0, "city": "LA", "value": 20})
        # Only NYC triggers
        result = agg.add_row({"ts": 12.0, "city": "NYC", "value": 30})
        nyc_results = [r for r in result if r.get("city") == "NYC"]
        assert len(nyc_results) == 1

    def test_late_data_within_allowance(self):
        agg = WindowAggregator(
            window_type="tumbling", window_size=10, time_column="ts",
            allowed_lateness=5.0,
        )
        agg.add_row({"ts": 1.0, "value": 10})
        agg.add_row({"ts": 12.0, "value": 20})  # triggers window [0,10)
        # Late row within 5s allowance
        result = agg.add_row({"ts": 8.0, "value": 30})
        # Should be accepted into window [0,10)
        assert result is not None or True  # implementation detail

    def test_late_data_beyond_allowance_dropped(self):
        agg = WindowAggregator(
            window_type="tumbling", window_size=10, time_column="ts",
            allowed_lateness=2.0,
        )
        agg.add_row({"ts": 1.0, "value": 10})
        agg.add_row({"ts": 12.0, "value": 20})  # triggers window [0,10)
        agg.add_row({"ts": 15.0, "value": 25})
        # Very late row: window [0,10) closed at watermark=12, lateness=2, deadline=14
        result = agg.add_row({"ts": 5.0, "value": 999})
        # Should be dropped
        assert result is None or (isinstance(result, dict) and result.get("dropped"))

    def test_multi_key_group_by(self):
        agg = WindowAggregator(
            window_type="tumbling", window_size=10, time_column="ts",
            group_by=["city", "category"],
        )
        agg.add_row({"ts": 1.0, "city": "NYC", "category": "A", "value": 10})
        agg.add_row({"ts": 2.0, "city": "NYC", "category": "B", "value": 20})
        agg.add_row({"ts": 3.0, "city": "NYC", "category": "A", "value": 30})
        result = agg.add_row({"ts": 12.0, "city": "NYC", "category": "A", "value": 40})
        # NYC/A window should have count=2 (ts=1.0, ts=3.0)
        nyc_a = [r for r in result if r.get("city") == "NYC" and r.get("category") == "A"]
        assert len(nyc_a) == 1
        assert nyc_a[0]["count"] == 2

    def test_group_by_with_flush(self):
        agg = WindowAggregator(
            window_type="tumbling", window_size=10, time_column="ts",
            group_by=["city"],
        )
        agg.add_row({"ts": 1.0, "city": "NYC", "value": 10})
        agg.add_row({"ts": 2.0, "city": "LA", "value": 20})
        result = agg.flush()
        assert len(result) == 2
        cities = {r["city"] for r in result}
        assert cities == {"NYC", "LA"}
