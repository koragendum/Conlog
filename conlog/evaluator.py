from typing import cast

from conlog.datatypes import (
    Addition,
    Initial,
    Node,
    Print,
    Solution,
    Subtraction,
    Terminal,
)


def evaluate(path: list[Node], assignment: dict[str, int]) -> Solution | None:
    initial = cast(Initial, path[0].op)

    # Verify assignments agree with boundary conditions
    for x, y in initial.fixed:
        if assignment[x] != y:
            return None

    var_values = dict(assignment)
    prints = []

    found_terminal = False

    for node in path[1:]:
        match node.op:
            case Initial():
                raise ValueError(f"Initial node found in path: {node}")
            case Print(var=var):
                prints.append(str(var_values[var]))
            case Addition(lhs=lhs, rhs=rhs):
                if isinstance(rhs, int):
                    var_values[lhs] += rhs
                else:
                    var_values[lhs] += var_values[rhs]
            case Subtraction(lhs=lhs, rhs=rhs):
                if isinstance(rhs, int):
                    var_values[lhs] -= rhs
                else:
                    var_values[lhs] -= var_values[rhs]
            case Terminal():
                for _, x in var_values.items():
                    if x != 0:
                        return None
                found_terminal = True
            case None:
                pass
            case _:
                raise ValueError(f"Unknown operation: {node.op}")

        if found_terminal:
            break
    else:
        raise ValueError("Path does not end in Terminal")

    return Solution(path, assignment, prints)
