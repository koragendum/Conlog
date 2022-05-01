from typing import cast

from conlog.datatypes import (
    Addition,
    ConditionalDecrement,
    ConditionalIncrement,
    Initial,
    IntegerPrint,
    Node,
    Solution,
    Subtraction,
    Terminal,
    UnicodePrint,
)


def partial_evaluate(
    path: list[Node], assignment: dict[str, int]
) -> tuple[dict[str, int], list[str | int]]:
    var_values = dict(assignment)
    prints = []

    found_terminal = False

    for node in path[1:]:
        match node.op:
            case Terminal():
                return var_values, prints
            case None:
                pass
            case op:
                op.update(var_values, prints)

        if found_terminal:
            break

    return var_values, prints


def evaluate(path: list[Node], assignment: dict[str, int]) -> Solution | None:
    initial = cast(Initial, path[0].op)

    # Verify assignments agree with boundary conditions
    for x, y in initial.fixed:
        if assignment[x] != y:
            return None

    var_values, prints = partial_evaluate(path, assignment)

    match path[-1].op:
        case Terminal():
            for _, x in var_values.items():
                if x != 0:
                    return None
        case _:
            raise ValueError(f"Unknown operation: {path[-1].op}")

    return Solution(path, assignment, prints)
