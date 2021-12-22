"""Contains code for parsing input files and writing output files."""
import csv
from pathlib import Path
from random import shuffle
from typing import Dict, List, Optional

from alloa_matching.agents import Hierarchy
from alloa_matching.graph import AllocationGraph


class Line:
    """Represents a line of data read from input CSV file."""
    def __init__(self, line: List[str]) -> None:
        self.line = [x.strip() for x in line]
        self.raw_name = line[0]
        self.capacities = [int(x) for x in self.line[1:3]]
        self.raw_preferences = self.line[3:]

    def __eq__(self, other) -> bool:
        return self.line == other.line

    def __repr__(self) -> str:
        return str(self.line)


class FileReader:
    """Contains data parsed from input CSV file."""
    def __init__(
        self,
        level: Optional[int] = None,
        randomise: bool = False,
        quoting: int = csv.QUOTE_NONE,
    ) -> None:
        self.randomise = randomise
        self.quoting = quoting
        self.level = level

        self.hierarchy = Hierarchy(level) if level else None

        self.file_content = []
