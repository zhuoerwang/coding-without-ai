"""
Tests for CSV Parser + Streaming Aggregation
Run: pytest test_csv.py -v
"""

import pytest
from csv_parser import CSVParser, WindowAggregator


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

    def test_all_quoted(self):
        parser = CSVParser()
        assert parser.parse_row('"a","b","c"') == ["a", "b", "c"]

    def test_mixed_quoted_unquoted(self):
        parser = CSVParser()
        assert parser.parse_row('a,"b,c",d') == ["a", "b,c", "d"]

    def test_whitespace_preserved(self):
        parser = CSVParser()
        assert parser.parse_row(" a , b , c ") == [" a ", " b ", " c "]

    def test_only_delimiters(self):
        parser = CSVParser()
        assert parser.parse_row(",,") == ["", "", ""]

    def test_quoted_empty_field(self):
        parser = CSVParser()
        assert parser.parse_row('"",b') == ["", "b"]

    def test_type_coercion_int(self):
        parser = CSVParser()
        assert parser.parse_row("42,hello") == [42, "hello"]

    def test_type_coercion_float(self):
        parser = CSVParser()
        assert parser.parse_row("3.14,hello") == [3.14, "hello"]

    def test_type_coercion_mixed(self):
        parser = CSVParser()
        assert parser.parse_row("10,3.14,hello") == [10, 3.14, "hello"]

    def test_parse_multiline(self):
        parser = CSVParser()
        text = ["a,b,c", "1,2,3", "4,5,6"]
        rows = parser.parse(text)
        assert rows == [["a", "b", "c"], [1, 2, 3], [4, 5, 6]]

    def test_custom_delimiter(self):
        parser = CSVParser(delimiter="\t")
        assert parser.parse_row("a\tb\tc") == ["a", "b", "c"]

    def test_custom_quotechar(self):
        parser = CSVParser(quote="'")
        assert parser.parse_row("'hello, world',b") == ["hello, world", "b"]


# ============================================================
# Level 2: Streaming Iterator
# ============================================================

class TestLevel2:
    def test_iter_from_list(self):
        parser = CSVParser()
        rows = list(parser.iter(iter(["a,b,c", "1,2,3"])))
        assert rows == [["a", "b", "c"], [1, 2, 3]]

    def test_iter_type_coercion(self):
        parser = CSVParser()
        rows = list(parser.iter(iter(["42,3.14,hello"])))
        assert rows == [[42, 3.14, "hello"]]

    def test_generator_based(self):
        """Should not load all rows at once — works with infinite source."""
        parser = CSVParser()

        def infinite_lines():
            i = 0
            while True:
                yield f"{i},{i*10}"
                i += 1

        gen = parser.iter(infinite_lines())
        assert next(gen) == [0, 0]
        assert next(gen) == [1, 10]
        assert next(gen) == [2, 20]

    def test_iter_quoted_field(self):
        parser = CSVParser()
        rows = list(parser.iter(iter(['"hello, world",b'])))
        assert rows == [["hello, world", "b"]]

    def test_iter_empty_source(self):
        parser = CSVParser()
        rows = list(parser.iter(iter([])))
        assert rows == []


# ============================================================
# Level 3: Windowed Aggregation
# ============================================================

class TestLevel3:
    def test_tumbling_window_basic(self):
        agg = WindowAggregator(window_size=10, ts_index=1, val_index=0)
        assert agg.add_row([10, 1.0]) is None
        assert agg.add_row([20, 5.0]) is None
        result = agg.add_row([30, 12.0])
        assert result is not None
        assert result["count"] == 2
        assert result["sum"] == 30
        assert result["avg"] == 15.0
        assert result["min"] == 10
        assert result["max"] == 20

    def test_tumbling_window_multiple(self):
        agg = WindowAggregator(window_size=5, ts_index=1, val_index=0)
        agg.add_row([10, 1.0])
        agg.add_row([20, 3.0])
        result = agg.add_row([30, 6.0])
        assert result is not None
        assert result["count"] == 2
        result2 = agg.add_row([40, 11.0])
        assert result2 is not None
        assert result2["count"] == 1  # only [30, 6.0] in [5, 10)

    def test_tumbling_window_min_max(self):
        agg = WindowAggregator(window_size=10, ts_index=1, val_index=0)
        agg.add_row([5, 1.0])
        agg.add_row([15, 2.0])
        agg.add_row([10, 3.0])
        result = agg.add_row([99, 11.0])
        assert result["min"] == 5
        assert result["max"] == 15

    def test_flush_incomplete_window(self):
        agg = WindowAggregator(window_size=10, ts_index=1, val_index=0)
        agg.add_row([10, 1.0])
        agg.add_row([20, 5.0])
        result = agg.flush()
        assert result is not None
        assert result["count"] == 2
        assert result["sum"] == 30

    def test_empty_flush(self):
        agg = WindowAggregator(window_size=10, ts_index=1, val_index=0)
        assert agg.flush() is None

    def test_window_boundaries(self):
        """Window result includes start and end."""
        agg = WindowAggregator(window_size=10, ts_index=1, val_index=0)
        agg.add_row([10, 1.0])
        result = agg.add_row([20, 12.0])
        assert result["window_start"] == 0.0
        assert result["window_end"] == 10.0

    def test_end_to_end_stream_aggregate(self):
        """Parse rows from list, stream into aggregator."""
        parser = CSVParser()
        lines = ["10,1.0", "20,5.0", "30,12.0", "40,15.0"]
        agg = WindowAggregator(window_size=10, ts_index=1, val_index=0)

        results = []
        for row in parser.iter(iter(lines)):
            result = agg.add_row(row)
            if result:
                results.append(result)
        remaining = agg.flush()
        if remaining:
            results.append(remaining)

        # Window [0, 10): rows at ts=1.0 and ts=5.0
        assert results[0]["count"] == 2
        assert results[0]["avg"] == 15.0
        # Window [10, 20): rows at ts=12.0 and ts=15.0
        assert results[1]["count"] == 2
        assert results[1]["avg"] == 35.0
