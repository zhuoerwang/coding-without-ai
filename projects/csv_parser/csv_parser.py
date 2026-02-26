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
    def __init__(self):
        pass