from collections import defaultdict
from dataclasses import dataclass, field
from typing import Iterable

import networkx as nx


@dataclass(frozen=True, order=True)
class Operation:
    def update(self, assignment: dict[str, int], stdout: list[str | int]) -> None:
        """Update the variable assignments and stdout in-place
        by visiting this operation."""

        pass


@dataclass(frozen=True, order=True)
class Initial(Operation):
    free: tuple[str, ...]
    fixed: tuple[tuple[str, int], ...]

    def __str__(self) -> str:
        fixed_vars = [f"{x}={y}" for x, y in self.fixed]
        vars = fixed_vars + list(self.free)
        return ", ".join(vars)


@dataclass(frozen=True, order=True)
class Terminal(Operation):
    def __str__(self) -> str:
        return "Terminal"


@dataclass(frozen=True, order=True)
class Addition(Operation):
    lhs: str
    rhs: str | int

    def __str__(self) -> str:
        return f"{self.lhs}+={self.rhs}"

    def update(self, assignment: dict[str, int], stdout: list[str | int]) -> None:
        if isinstance(self.rhs, int):
            assignment[self.lhs] += self.rhs
        else:
            assignment[self.lhs] += assignment[self.rhs]


@dataclass(frozen=True, order=True)
class IntegerPrint(Operation):
    var: str | int

    def __str__(self) -> str:
        return f"iprint {self.var}"

    def update(self, assignment: dict[str, int], stdout: list[str | int]) -> None:
        if isinstance(self.var, int):
            stdout.append(self.var)
        else:
            stdout.append(assignment[self.var])


@dataclass(frozen=True, order=True)
class UnicodePrint(Operation):
    var: str | int

    def __str__(self) -> str:
        return f"uprint {self.var}"

    def update(self, assignment: dict[str, int], stdout: list[str | int]) -> None:
        if isinstance(self.var, int):
            stdout.append(chr(self.var))
        else:
            stdout.append(chr(assignment[self.var]))


@dataclass(frozen=True, order=True)
class Subtraction(Operation):
    lhs: str
    rhs: str | int

    def __str__(self) -> str:
        return f"{self.lhs}-={self.rhs}"

    def update(self, assignment: dict[str, int], stdout: list[str | int]) -> None:
        if isinstance(self.rhs, int):
            assignment[self.lhs] -= self.rhs
        else:
            assignment[self.lhs] -= assignment[self.rhs]


@dataclass(frozen=True, order=True)
class ConditionalIncrement(Operation):
    lhs: str
    rhs: str | int

    def __str__(self) -> str:
        return f"{self.lhs}++?{self.rhs}"

    def update(self, assignment: dict[str, int], stdout: list[str | int]) -> None:
        if isinstance(self.rhs, int):
            if self.rhs > 0:
                assignment[self.lhs] += 1
        elif assignment[self.rhs] > 0:
            assignment[self.lhs] += 1


@dataclass(frozen=True, order=True)
class ConditionalDecrement(Operation):
    lhs: str
    rhs: str | int

    def __str__(self) -> str:
        return f"{self.lhs}--?{self.rhs}"

    def update(self, assignment: dict[str, int], stdout: list[str | int]) -> None:
        if isinstance(self.rhs, int):
            if self.rhs > 0:
                assignment[self.lhs] -= 1
        elif assignment[self.rhs] > 0:
            assignment[self.lhs] -= 1


@dataclass(frozen=True, order=True)
class Node:
    name: str
    op: Operation | None


@dataclass(frozen=True)
class Solution:
    path: list[Node]
    assignment: dict[str, int]
    stdout: list[str | int]


def make_graph(edges: Iterable[tuple[Node, Node]]) -> nx.Graph:
    g = nx.Graph()
    g.add_edges_from(edges)
    return g


def add_edges_to_graph(edges: Iterable[tuple[Node, Node]], g: nx.Graph) -> None:
    g.add_edges_from(edges)
