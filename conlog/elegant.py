import operator
from collections import deque
from dataclasses import dataclass
from typing import Callable, Iterator, cast

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
from conlog.directed import elide_none_none, make_uturnless
from conlog.evaluator import evaluate, partial_evaluate
from conlog.monotonicity import (
    compute_monotone_variables,
    find_initial,
    find_initial_node,
)


def determine_monotone_variables(
    g: nx.Graph,
    initial: Initial,
    nonnegative: set[str] | None = None,
    nonpositive: set[str] | None = None,
) -> tuple[set[str], set[str]]:
    nonnegative = set() if nonnegative is None else nonnegative
    nonpositive = set() if nonpositive is None else nonpositive

    increments = set()
    decrements = set()

    all_variables = set(initial.free) | set(x[0] for x in initial.fixed)

    non_monotonic = set()

    for node in g.nodes:
        match node.op:
            case Addition(lhs=lhs, rhs=rhs):
                if (
                    isinstance(rhs, int)
                    and rhs >= 0
                    or (isinstance(rhs, str) and rhs in nonnegative)
                ):
                    increments.add(lhs)
                elif (
                    isinstance(rhs, int)
                    and rhs <= 0
                    or (isinstance(rhs, str) and rhs in nonpositive)
                ):
                    decrements.add(lhs)
                else:
                    non_monotonic.add(lhs)
            case Subtraction(lhs=lhs, rhs=rhs):
                if (
                    isinstance(rhs, int)
                    and rhs >= 0
                    or (isinstance(rhs, str) and rhs in nonnegative)
                ):
                    decrements.add(lhs)
                elif (
                    isinstance(rhs, int)
                    and rhs <= 0
                    or (isinstance(rhs, str) and rhs in nonpositive)
                ):
                    increments.add(lhs)
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


class _BoundedMixin:
    def __add__(self, other):
        return add_bounds(cast(Bound, self), other)

    def __radd__(self, other):
        return add_bounds(other, cast(Bound, self))

    def __sub__(self, other):
        return sub_bounds(cast(Bound, self), other)

    def __rsub__(self, other):
        return sub_bounds(other, cast(Bound, self))


@dataclass(frozen=True)
class Unknown(_BoundedMixin):
    pass


@dataclass(frozen=True)
class AtLeast(_BoundedMixin):
    lb: int


@dataclass(frozen=True)
class AtMost(_BoundedMixin):
    ub: int


Bound = int | AtMost | AtLeast | Unknown


def add_bounds(x: Bound, y: Bound) -> Bound:
    match x, y:
        case int(xx), int(yy):
            return xx + yy
        case int(xx), AtLeast(lb=lby):
            return AtLeast(xx + lby)
        case int(xx), AtMost(ub=uby):
            return AtMost(xx + uby)
        case AtLeast(lb=lbx), int(yy):
            return AtLeast(lbx + yy)
        case AtMost(ub=ubx), int(yy):
            return AtMost(ubx + yy)
        case AtLeast(lb=lbx), AtLeast(lb=lby):
            return AtLeast(lbx + lby)
        case AtMost(ub=ubx), AtMost(ub=uby):
            return AtMost(ubx + uby)
        case _:
            return Unknown()


def sub_bounds(x: Bound, y: Bound) -> Bound:
    match x, y:
        case int(xx), int(yy):
            return xx - yy
        case int(xx), AtLeast(lb=lby):
            return AtMost(xx - lby)
        case int(xx), AtMost(ub=uby):
            return AtLeast(xx - uby)
        case AtLeast(lb=lbx), int(yy):
            return AtLeast(lbx - yy)
        case AtMost(ub=ubx), int(yy):
            return AtMost(ubx - yy)
        case AtLeast(lb=lbx), AtMost(ub=lby):
            return AtLeast(lbx - lby)
        case AtMost(ub=ubx), AtLeast(lb=lby):
            return AtMost(ubx - lby)
        case _:
            return Unknown()


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
    initial_assignment: dict[str, Bound] = dict(initial.fixed)

    for free in initial.free:
        value: Bound
        match free in monotone_increasing, free in monotone_decreasing:
            case True, True:
                value = 0
            case True, False:
                value = AtMost(0)
            case False, True:
                value = AtLeast(0)
            case False, False:
                value = Unknown()
            case _:
                raise ValueError(
                    "Programmer error; exhaustive case analysis not exhaustive"
                )

        initial_assignment[free] = value

    assignment, _ = partial_evaluate(path, initial_assignment)  # type: ignore

    # Increasing variables must be at most 0
    for var in monotone_increasing:
        match assignment[var]:
            case int(x):
                if x > 0:
                    return True
            case AtLeast(lb=lb):
                if lb > 0:
                    return True

    # Decreasing variables must be at least 0
    for var in monotone_decreasing:
        match assignment[var]:
            case int(x):
                if x < 0:
                    return True
            case AtMost(ub=ub):
                if ub < 0:
                    return True

    return False


def interpret(g: nx.Graph, limit: int | None = None) -> Iterator[Solution]:
    initial = find_initial(g)

    node_depth = nx.single_source_shortest_path_length(g, find_initial_node(g))

    dg = elide_none_none(make_uturnless(g))

    monotone_inc, monotone_dec = compute_monotone_variables(g)
    queue = deque()
    for edge in find_initial_edges(dg):
        queue.append([edge])

    count = 0
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

        # Explore neighbors, favoring nodes moving closer to the Terminal
        neighbors = list(dg.neighbors((u, v)))
        neighbors.sort(key=lambda node: node_depth[node[0]], reverse=True)

        for node in neighbors:
            new_history = list(history)
            new_history.append(node)
            queue.append(new_history)

        # Enforce search limits
        count += 1
        if limit is not None and count > limit:
            break


def get_bounds_from_monotonicity(
    g: nx.Graph, increasing: set[str], decreasing: set[str]
) -> dict[str, tuple[int | float, int | float]]:
    initial = find_initial(g)
    free, fixed = set(initial.free), dict(initial.fixed)

    # Given some variables are monotonic, bound them.
    boundable_vars = increasing | decreasing
    bounds = {var: [float("-inf"), float("inf")] for var in boundable_vars}
    for var in boundable_vars:
        if var in increasing:
            bounds[var][1] = min(bounds[var][1], 0)
            if var in fixed:
                bounds[var][0] = max(bounds[var][0], fixed[var])
        if var in decreasing:
            bounds[var][0] = max(bounds[var][0], 0)
            if var in fixed:
                bounds[var][1] = min(bounds[var][1], fixed[var])

    return bounds


def determine_variable_bounds_multipass(
    g: nx.Graph,
) -> dict[str, tuple[int | float, int | float]]:
    initial = find_initial(g)
    free, fixed = set(initial.free), dict(initial.fixed)

    # N passes to allow propagation of nonnegativity/nonpositivity to all variables
    bounds = dict()
    nonpositive = set()
    nonnegative = set()
    for _ in range(len(free) + len(fixed)):
        increasing, decreasing = determine_monotone_variables(
            g, initial, nonnegative=nonnegative, nonpositive=nonpositive
        )

        bounds = get_bounds_from_monotonicity(g, increasing, decreasing)

        # Now, see if any are nonnegative / nonpositive vars
        nonnegative = {var for var, bounds in bounds.items() if bounds[0] >= 0}
        nonpositive = {var for var, bounds in bounds.items() if bounds[1] <= 0}

    return bounds
