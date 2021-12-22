from enum import Enum


class Polarity(Enum):
    POSITIVE = '+'
    NEGATIVE = '-'


class GraphElement(Enum):
    SOURCE = 'SOURCE'
    SINK = 'SINK'
