from collections import deque
from typing import Iterator

import networkx as nx

from conlog.brute import (
    compute_initial_values,
    find_initial_edges,
    make_candidate_solution,
)
from conlog.datatypes import (
    Addition,
    ConditionalDecrement,
    ConditionalIncrement,
    Initial,
    Node,
    Solution,
    Subtraction,
    Terminal,
)
from conlog.directed import make_uturnless
from conlog.evaluator import evaluate, partial_evaluate


def find_initial(g: nx.Graph) -> Initial:
    for node in g.nodes:
        match node.op:
            case Initial():
                return node.op
            case _:
                pass

    raise ValueError("No Initial node ")


def determine_monotone_variables(
    g: nx.Graph, initial: Initial
) -> tuple[set[str], set[str]]:
    increments = set()
    decrements = set()

    all_variables = set(initial.free) | set(x[0] for x in initial.fixed)

    non_monotonic = set()

    for node in g.nodes:
        match node.op:
            case Addition(lhs=lhs, rhs=rhs):
                if isinstance(rhs, int) and rhs >= 0:
                    increments.add(lhs)
                else:
                    non_monotonic.add(lhs)
            case Subtraction(lhs=lhs, rhs=rhs):
                if isinstance(rhs, int) and rhs >= 0:
                    decrements.add(lhs)
                else:
                    non_monotonic.add(lhs)
            case ConditionalIncrement(lhs=lhs):
                increments.add(lhs)
            case ConditionalDecrement(lhs=lhs):
                decrements.add(lhs)
            case _:
                pass

    return (
        all_variables - decrements - non_monotonic,
        all_variables - increments - non_monotonic,
    )


class FreePoison:
    def __add__(self, _):
        return self

    def __radd__(self, _):
        return self

    def __sub__(self, _):
        return self

    def __rsub__(self, _):
        return self


def bounds_violated(
    path: list[Node],
    monotone_increasing: set[str],
    monotone_decreasing: set[str],
    initial: Initial,
) -> bool:
    """Return whether monotone variables cannot be satisfied.

    If this function returns True, then no satisfying values
    exist; if False, satisfying values might exist.
    """

    # If there are no monotone variables there is nothing to check
    if not (monotone_increasing or monotone_decreasing):
        return False

    # Construct an initial assignment consisting of fixed variables and
    # poisoned free variables.
    #
    # Any computation involving a poisoned variable is poisoned.
    initial_assignment: dict[str, int | FreePoison] = dict(initial.fixed)
    poison = FreePoison()
    for free in initial.free:
        initial_assignment[free] = poison

    assignment, _ = partial_evaluate(path, initial_assignment)  # type: ignore

    for var in monotone_increasing:
        val = assignment[var]

        if isinstance(val, FreePoison):
            continue
        else:
            if val > 0:
                return True

    for var in monotone_decreasing:
        val = assignment[var]

        if isinstance(val, FreePoison):
            continue
        else:
            if val < 0:
                return True

    return False


def interpret(g: nx.Graph) -> Iterator[Solution]:
    initial = find_initial(g)
    dg = make_uturnless(g)

    monotone_inc, monotone_dec = determine_monotone_variables(g, initial)
    queue = deque()
    for edge in find_initial_edges(dg):
        queue.append([edge])

    while queue:
        history = queue.popleft()
        u, v = history[-1]

        check_bounds = False
        match v.op:
            case Terminal():
                path = make_candidate_solution(history)
                assignment = compute_initial_values(path)
                solution = evaluate(path, assignment)

                if solution is not None:
                    yield solution

                # We need not consider nodes after the terminal
                continue
            case Addition():
                check_bounds = True
            case Subtraction():
                check_bounds = True
            case ConditionalIncrement():
                check_bounds = True
            case ConditionalDecrement():
                check_bounds = True
            case _:
                pass

        # If the path ends in a modification, check to see whether monotonicity
        # bounds are violated. If they are, abandon the search.
        if check_bounds and bounds_violated(
            make_candidate_solution(history),
            monotone_inc,
            monotone_dec,
            initial,
        ):
            continue

        # Explore neighbors
        for node in dg.neighbors((u, v)):
            new_history = list(history)
            new_history.append(node)
            queue.append(new_history)
