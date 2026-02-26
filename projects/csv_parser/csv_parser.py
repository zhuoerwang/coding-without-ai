from enum import Enum
from typing import Iterable, Iterator

class States(Enum):
    FIELD_START = "FIELD_START"
    QUOTED = "QUOTED"
    UNQUOTED = "UNQUOTED"
    QUOTE_IN_QUOTED = "QUOTE_IN_QUOTED"

class CSVParser:
    def __init__(self, delimiter: str = ",", quotechar: str='"') -> None:
        self.quotechar = quotechar
        self.delimiter = delimiter
        self.transition_rules = {
            States.FIELD_START: {
                quotechar: States.QUOTED,
                delimiter: States.FIELD_START,
                "OTHERS": States.UNQUOTED
            },
            States.UNQUOTED: {
                delimiter: States.FIELD_START,
                "OTHERS": States.UNQUOTED
            },
            States.QUOTED: {
                quotechar: States.QUOTE_IN_QUOTED,
                "OTHERS": States.QUOTED
            },            
            States.QUOTE_IN_QUOTED: {
                quotechar: States.QUOTED, # escape quotes
                delimiter: States.FIELD_START,
                "OTHERS": States.QUOTE_IN_QUOTED
            }
        }

    def parse_row(self, line: str) -> list[str]:
        """ parse a single CSV line into fields """
        curr_state = States.FIELD_START
        field_list = []
        field_content = []
        for char in line:
            if char in self.transition_rules[curr_state]:
                if curr_state == States.QUOTE_IN_QUOTED and char == self.quotechar:
                    # escape the quote char
                    field_content.append(char)
                curr_state = self.transition_rules[curr_state][char]
            else:
                field_content.append(char)
                # accumulate the filed when it's not special condition
                curr_state = self.transition_rules[curr_state]["OTHERS"]

            # If the state is States.FIELD_START, emit the content
            # and reset the field_content
            if curr_state == States.FIELD_START:
                field_list.append(''.join(field_content))
                field_content = []
        
        # Handle end of line case, just emit what we collected
        field_list.append(''.join(field_content))
        return field_list

    def parse(self, text: str) -> list[list[str]]:
        """ parse multi-line CSV text """
        res = []
        line = []
        curr_state = States.FIELD_START
        for char in text:
            if char in self.transition_rules[curr_state]:
                curr_state = self.transition_rules[curr_state][char]
            else:
                if curr_state != States.QUOTED and char == "\n" and len(line) != 0:
                    res.append(self.parse_row(''.join(line)))
                    curr_state = States.FIELD_START
                    line = []
                    continue
                curr_state = self.transition_rules[curr_state]["OTHERS"]
            line.append(char)
        
        # process last line
        if len(line) != 0:
            res.append(self.parse_row(''.join(line)))

        return res


class CSVStream:
    def __init__(self, parser: CSVParser, header: bool = True) -> None:
        self.header = header
        self.parser = parser

    def _value(self, item: str) -> str | int | float:
        try:
            return int(item)
        except ValueError:
            try:
                return float(item)
            except ValueError:
                return item

    def iter_rows(self, source: Iterable[str]) -> Iterator[dict[str, str]] | Iterator[list]:
        # The first row is a header, and return a iterator of a dict
        head = self.parser.parse_row(next(source)) if self.header else []
        row_list, count_quotes = [], 0

        # Process the rest of the content
        for line in source:
            row_list.append(line)
            count_quotes += line.count(self.parser.quotechar)
            # edge case, quotecahr expand to multiple lines
            if count_quotes % 2 == 1:
                continue

            row = '\n'.join(row_list)
            row_content = {} if self.header else []
            for i, item in enumerate(self.parser.parse_row(row)):
                value = self._value(item)
                if self.header:
                    # Handle edge case: more cols than head
                    if i >= len(head):
                        continue
                    row_content[head[i]] = value
                else:
                    row_content.append(value)
            
            # Edge case: add missing field, append ""
            for j in range(i+1, len(head)):
                if self.header:
                    row_content[head[j]] = ""
                else:
                    row_content.append("")
            
            # reset the values
            row_list, count_quotes = [], 0
            # Yield result
            yield row_content

    def iter_rows_from_file(self, filepath: str) -> Iterator[dict[str, str]]| Iterator[list]:
        with open(filepath, "r") as fp:
            yield from self.iter_rows(fp)


class WindowAggregator:
    def __init__(self):
        pass