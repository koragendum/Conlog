from collections import defaultdict
from dataclasses import dataclass, field
from typing import Iterable

import networkx as nx


@dataclass(frozen=True, order=True)
class Operation:
    pass


@dataclass(frozen=True, order=True)
class Initial(Operation):
    free: tuple[str, ...]
    fixed: tuple[tuple[str, int], ...]


@dataclass(frozen=True, order=True)
class Terminal(Operation):
    pass


@dataclass(frozen=True, order=True)
class Addition(Operation):
    lhs: str
    rhs: str | int


@dataclass(frozen=True, order=True)
class IntegerPrint(Operation):
    var: str | int


@dataclass(frozen=True, order=True)
class UnicodePrint(Operation):
    var: str | int


@dataclass(frozen=True, order=True)
class Subtraction(Operation):
    lhs: str
    rhs: str | int


@dataclass(frozen=True, order=True)
class ConditionalIncrement(Operation):
    lhs: str
    rhs: str | int


@dataclass(frozen=True, order=True)
class ConditionalDecrement(Operation):
    lhs: str
    rhs: str | int


@dataclass(frozen=True, order=True)
class Node:
    name: str
    op: Operation | None


@dataclass(frozen=True)
class Solution:
    path: list[Node]
    assignment: dict[str, int]
    stdout: list[str]


def make_graph(edges: Iterable[tuple[Node, Node]]) -> nx.Graph:
    g = nx.Graph()
    g.add_edges_from(edges)
    return g


def add_edges_to_graph(edges: Iterable[tuple[Node, Node]], g: nx.Graph) -> None:
    g.add_edges_from(edges)
