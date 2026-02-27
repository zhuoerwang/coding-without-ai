from enum import Enum
from typing import Iterator, Iterable

# ============================================================
# Level 1: CSV Parser State Machine
# ============================================================

class States(Enum):
    START = "START"
    QUOTE = "QUOTE"
    UNQUOTE = "UNQUOTE"
    QUOTE_IN_QUOTE = "QUOTE_IN_QUOTE"


class CSVParser:
    def __init__(self, delimiter=',', quote='"'):
        self.delimiter = delimiter
        self.quote = quote
        self.state_transition = {
            States.START: {
                delimiter: States.START,
                quote: States.QUOTE,
                "OTHERS": States.UNQUOTE
            },
            States.UNQUOTE: {
                delimiter: States.START,
                "OTHERS": States.UNQUOTE

            },
            States.QUOTE: {
                quote: States.QUOTE_IN_QUOTE,
                "OTHERS": States.QUOTE
            },

            States.QUOTE_IN_QUOTE: {
                delimiter: States.START,
                quote: States.QUOTE, # escape
                "OTHERS": States.QUOTE_IN_QUOTE
            }
        }

    def _value(self, cell: str) -> str | int | float:
        try:
            return int(cell)
        except ValueError:
            try:
                return float(cell)
            except ValueError:
                return cell

    def parse_row(self, row: str) -> list:
        """ Parse a single CSV row into fields. No newline inside cells. """
        state = States.START
        row_list = []
        cell = []
        for char in row:
            if char in self.state_transition[state]:
                # quote escape in quote in quote states
                if state == States.QUOTE_IN_QUOTE and char == self.quote:
                    cell.append(char)
                state = self.state_transition[state][char]
            else:
                cell.append(char)
                state = self.state_transition[state]["OTHERS"]

            # if state is States.START, emit cell content
            if state == States.START:
                row_list.append(self._value(''.join(cell)))
                cell = []

        row_list.append(self._value(''.join(cell)))
        return row_list


    def parse(self, text: list[str]) -> list[list]:
        """ Parse all rows (load all into memory). """
        res = []
        for row in text:
            res.append(self.parse_row(row.strip()))
        return res

    def iter(self, source: Iterable[str]) -> Iterator[list]:
        """ Streaming: yield one parsed row at a time, O(1) memory. """
        for row in source:
            yield self.parse_row(row.strip())

    def iter_from_file(self, filepath: str) -> Iterator[list]:
        with open(filepath, "r") as fp:
            yield from self.iter(fp)


class WindowAggregator:
    def __init__(self, window_size: float, ts_index: int, val_index: int) -> None:
        self.window_size = window_size
        self.ts_index = ts_index
        self.val_index = val_index
        self.aggregate_result = {}

    def _aggregate(self, row: list) -> None:
        ts, val = row[self.ts_index], row[self.val_index]
        self.aggregate_result["count"] = self.aggregate_result.get("count", 0) + 1
        self.aggregate_result["sum"] = self.aggregate_result.get("sum", 0) + val
        self.aggregate_result["avg"] = self.aggregate_result["sum"] / self.aggregate_result["count"]
        self.aggregate_result["max"] = max(self.aggregate_result.get("max", float('-inf')), val)
        self.aggregate_result["min"] = min(self.aggregate_result.get("min", float('inf')), val)
        self.aggregate_result["window_start"] = ts // self.window_size * self.window_size
        self.aggregate_result["window_end"] = self.aggregate_result["window_start"] + self.window_size
    
    def add_row(self, row: list) -> dict | None:
        """ returns result when window completes """
        completed = None
        if row[self.ts_index] >= self.aggregate_result.get("window_end", float('inf')):
            completed = self.flush()
        
        self._aggregate(row)

        return completed

    def flush(self) -> dict | None:
        res = self.aggregate_result.copy()
        self.aggregate_result = {}
        return res if res != {} else None

parser = CSVParser()
agg = WindowAggregator(window_size=10, ts_index=3, val_index=2)
for row in parser.iter_from_file('example.csv'):
    result = agg.add_row(row)
    if result:
        print(result)