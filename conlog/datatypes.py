from collections import defaultdict
from dataclasses import dataclass, field


@dataclass(frozen=True)
class Operation:
    pass


@dataclass(frozen=True)
class Initial(Operation):
    free: tuple[str]
    fixed: tuple[tuple[str, int]]


@dataclass(frozen=True)
class Terminal(Operation):
    pass


@dataclass(frozen=True)
class Addition(Operation):
    lhs: str
    rhs: str | int
    

@dataclass(frozen=True)
class Print(Operation):
    var: str


@dataclass(frozen=True)
class Subtraction(Operation):
    lhs: str
    rhs: str | int


@dataclass(frozen=True)
class Node:
    name: str
    op: Operation | None


@dataclass(frozen=True)
class Graph:
    nodes: list[Node]
    edges: list[tuple[Node, Node]]

    _adjacency: dict[Node, list[Node]] = field(
        default_factory=lambda: defaultdict(list), init=False
    )

    def __post_init__(self):
        for u, v in self.edges:
            self._adjacency[u].append(v)
            self._adjacency[v].append(u)

    def neighbors(self, u: Node) -> list[Node]:
        yield from self._adjacency[u]

