"""A brute-force interpreter."""

from collections import deque
from typing import Iterator, cast

import networkx as nx

from conlog.datatypes import (
    Addition,
    Initial,
    Node,
    IntegerPrint,
    UnicodePrint,
    Solution,
    Subtraction,
    Terminal,
)
from conlog.directed import make_uturnless
from conlog.evaluator import evaluate


def find_initial_edges(g: nx.DiGraph) -> Iterator[tuple[Node, Node]]:
    for u, v in g.nodes:
        if isinstance(u.op, Initial):
            yield u, v


def make_candidate_solution(nodes: list[tuple[Node, Node]]) -> list[Node]:
    path = []
    path.append(nodes[0][0])
    path.append(nodes[0][1])
    for _, v in nodes[1:]:
        path.append(v)

    return path


def compute_initial_values(path: list[Node]) -> dict[str, int]:
    initial = cast(Initial, path[0].op)

    assignment = {pair[0]: 0 for pair in initial.fixed}
    for v in initial.free:
        assignment[v] = 0

    for node in reversed(path):
        match node.op:
            case Initial():
                pass
            case None:
                pass
            case IntegerPrint():
                pass
            case UnicodePrint():
                pass
            case Addition(lhs=lhs, rhs=rhs):
                if isinstance(rhs, int):
                    assignment[lhs] -= rhs
                else:
                    assignment[lhs] -= assignment[rhs]
            case Subtraction(lhs=lhs, rhs=rhs):
                if isinstance(rhs, int):
                    assignment[lhs] += rhs
                else:
                    assignment[lhs] += assignment[rhs]
            case Terminal():
                pass
            case _:
                raise ValueError(f"Unknown operation: {node.op}")

    return assignment


def interpret(g: nx.Graph) -> Iterator[Solution]:
    dg = make_uturnless(g)

    queue = deque()
    for edge in find_initial_edges(dg):
        queue.append([edge])

    while queue:
        history = queue.popleft()

        u, v = history[-1]
        if isinstance(v.op, Terminal):
            path = make_candidate_solution(history)
            assignment = compute_initial_values(path)
            solution = evaluate(path, assignment)

            if solution is not None:
                yield solution

        for node in dg.neighbors((u, v)):
            new_history = list(history)
            new_history.append(node)
            queue.append(new_history)
