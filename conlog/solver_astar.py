from conlog.datatypes import (
    Addition,
    Graph,
    Initial,
    Node,
    Operation,
    Print,
    Subtraction,
    Terminal,
)
from dataclasses import dataclass


@dataclass(frozen=True)
class SearchState():
    node: Node
    values: dict[str, int]


def compute_new_values_from_node_function(node, values, reverse=True):
    new_values = dict(values)

    if isinstance(node.op, (Addition, Subtraction)):
        if isinstance(node.op.rhs, int):
            rhs = node.op.rhs
        else:
            rhs = new_values[node.op.rhs]

        sign = -1 if reverse else 1
        if isinstance(node.op, Subtraction):
            sign *= -1

        new_values[node.op.lhs] += sign * rhs

    return new_values


def solve_graph_bfs(graph: Graph):
    # Get key nodes and variables
    initial_node = next(node for node in graph.nodes if isinstance(node.op, Initial))
    terminal_node = next(node for node in graph.nodes if isinstance(node.op, Terminal))
    free, fixed = initial_node.op.free, dict(initial_node.op.fixed)
    var_names = list(free) + list(fixed)

    # Run a BFS search
    queue = [[SearchState(terminal_node, {n: 0 for n in var_names}), None]]
    it = 0
    while len(queue) > 0 and it < 10000:
        it += 1
        current_state, history = queue.pop(0)
        print(current_state)
        if current_state.node == initial_node and all(current_state.values[n] == fixed[n] for n in fixed):
            print(f'Done! {current_state=}')

            final_path = [current_state]
            while history is not None:
                head, history = history
                final_path.append(head)

            return current_state, final_path

        last_node = history[0].node if history is not None else None

        for successor_node in graph.neighbors(current_state.node):
            if successor_node == last_node:
                continue  # No backtracking allowed
            successor_values = compute_new_values_from_node_function(current_state.node, current_state.values, reverse=True)
            queue.append([SearchState(successor_node, successor_values), [current_state, history]])

    raise Exception("Search failed")


if __name__ == '__main__':
    """
    Graph that computes either T=triangle_sum(x) or T=triangle_sum(x-1)
    depending on the first path taken. (no one-way gadget used)

        Initial----------------None---DecrT---Terminal
        |                       |
        '--DecrX----SubFbyX-----'

    """
    either_trisum_nodes = [
        Node("initial", Initial(free=("T",), fixed=(("n", 6),))),
        Node("decr_x", Subtraction("n", 1)),
        Node("sub_t_x", Subtraction("T", "n")),
        Node("none", None),
        Node("terminal", Terminal()),
    ]
    either_trisum_d = {n.name: n for n in either_trisum_nodes}

    either_trisum_graph = Graph(
        nodes=tuple(either_trisum_d.values()),
        edges=(
            (either_trisum_d["initial"], either_trisum_d["decr_x"]),
            (either_trisum_d["decr_x"], either_trisum_d["sub_t_x"]),
            (either_trisum_d["sub_t_x"], either_trisum_d["none"]),
            (either_trisum_d["none"], either_trisum_d["initial"]),
            (either_trisum_d["none"], either_trisum_d["terminal"]),
        ),
    )

    ans, final_path = solve_graph_bfs(either_trisum_graph)
    print()
    print(ans)
    print()
    for n in final_path:
        print(n)

