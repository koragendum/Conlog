from typing import cast

from conlog.datatypes import (
    Addition,
    ConditionalDecrement,
    ConditionalIncrement,
    Initial,
    Node,
    IntegerPrint,
    UnicodePrint,
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
                pass
            case None:
                pass
            case IntegerPrint(var=var):
                if isinstance(var, int):
                    prints.append(str(var))
                else:
                    prints.append(str(var_values[var]))
            case UnicodePrint(var=var):
                if isinstance(var, int):
                    prints.append(chr(var))
                else:
                    prints.append(chr(var_values[var]))
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
            case ConditionalIncrement(lhs=lhs, rhs=rhs):
                if isinstance(rhs, int):
                    rvalue = rhs
                else:
                    rvalue = var_values[rhs]
                if rvalue > 0:
                    var_values[lhs] += 1
            case ConditionalDecrement(lhs=lhs, rhs=rhs):
                if isinstance(rhs, int):
                    rvalue = rhs
                else:
                    rvalue = var_values[rhs]
                if rvalue > 0:
                    var_values[lhs] -= 1
            case Terminal():
                for _, x in var_values.items():
                    if x != 0:
                        return None
                found_terminal = True
            case _:
                raise ValueError(f"Unknown operation: {node.op}")

        if found_terminal:
            break
    else:
        raise ValueError("Path does not end in Terminal")

    return Solution(path, assignment, prints)
