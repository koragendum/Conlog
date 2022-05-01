from __future__ import annotations
from conlog.datatypes import (
    Addition,
    ConditionalDecrement,
    ConditionalIncrement,
    Function,
    Initial,
    Node,
    Subtraction,
    Terminal,
)
from conlog.evaluator import evaluate
from dataclasses import dataclass
import networkx as nx

@dataclass(frozen=True)
class SearchState():
    node: Node
    last_node: Node | None
    values: dict[str, int]
    graph: nx.Graph
    call_stack_parent: SearchState | None


def compute_new_values_from_node(node, values, reverse=True):
    new_values = dict(values)

    if isinstance(node.op, (Addition, Subtraction, ConditionalIncrement, ConditionalDecrement)):
        if isinstance(node.op.rhs, int):
            rhs = node.op.rhs
        else:
            rhs = new_values[node.op.rhs]

        rvalue = (-1 if reverse else 1)
        if isinstance(node.op, (Subtraction, ConditionalDecrement)):
            rvalue *= -1
        if isinstance(node.op, (Addition, Subtraction)):
            rvalue *= rhs
        if isinstance(node.op, (ConditionalIncrement, ConditionalDecrement)) and rhs <= 0:
            rvalue = 0  # Do nothing if condition not satisfied

        new_values[node.op.lhs] += rvalue

    return new_values


def compute_successor_states(current_state):
    if isinstance(current_state.node.op, Terminal) and current_state.last_node is not None:
        return []  # Terminals terminate the search.

    successor_states = []
    successor_values = compute_new_values_from_node(current_state.node, current_state.values, reverse=True)
    for successor_node in current_state.graph.neighbors(current_state.node):
        if successor_node == current_state.last_node:
            continue  # No backtracking allowed
        successor_states.append(SearchState(
            node=successor_node,
            last_node=current_state.node,
            values=successor_values,
            graph=current_state.graph,
            call_stack_parent=current_state.call_stack_parent,
        ))

    return successor_states


def compute_successor_states_with_functions(current_state):
    if isinstance(current_state.node.op, Terminal) and current_state.last_node is not None:
        return []  # Terminals terminate the search.

    if isinstance(current_state.node.op, Function):
        # Recurse into function
        next_initial_node = next(node for node in current_state.node.op.graph.nodes if isinstance(node.op, Initial))
        next_terminal_node = next(node for node in current_state.node.op.graph.nodes if isinstance(node.op, Terminal))
        var_map = dict(current_state.node.op.var_map)
        successor_state = SearchState(
            node=next_terminal_node,
            last_node=None,
            values={**{var_map[k]: current_state.values[k] for k in var_map}, **{k: 0 for k in dict(next_initial_node.op.fixed)}},
            graph=current_state.node.op.graph,
            call_stack_parent=current_state,
        )
        return [successor_state]

    successor_states = []
    if isinstance(current_state.node.op, Initial) and current_state.call_stack_parent is not None \
            and all(current_state.values[n] == dict(current_state.node.op.fixed)[n] for n in dict(current_state.node.op.fixed)):
        # We are in a function, on an initial state, and all
        # fixed constraints are satisfied. One possible action
        # is to return from that function.
        parent_state = current_state.call_stack_parent
        # Some values changed through our function
        successor_values = {
            **parent_state.values,
            **{k: current_state.values[v] for k, v in dict(parent_state.node.op.var_map).items()},
        }

        for successor_node in parent_state.graph.neighbors(parent_state.node):
            if successor_node == parent_state.last_node:
                continue  # No backtracking allowed
            successor_state = SearchState(
                node=successor_node,
                last_node=parent_state.node,
                values=successor_values,
                graph=parent_state.graph,
                call_stack_parent=parent_state.call_stack_parent,
            )
            successor_states.append(successor_state)

    successor_values = compute_new_values_from_node(current_state.node, current_state.values, reverse=True)
    for successor_node in current_state.graph.neighbors(current_state.node):
        if successor_node == current_state.last_node:
            continue  # No backtracking allowed
        successor_states.append(SearchState(
            node=successor_node,
            last_node=current_state.node,
            values=successor_values,
            graph=current_state.graph,
            call_stack_parent=current_state.call_stack_parent,
        ))

    return successor_states


def solve_graph_bfs(graph: nx.Graph, limit = None):
    if limit is None:
        limit = 65536

    # Get key nodes and variables
    initial_node = next(node for node in graph.nodes if isinstance(node.op, Initial))
    terminal_node = next(node for node in graph.nodes if isinstance(node.op, Terminal))
    free, fixed = initial_node.op.free, dict(initial_node.op.fixed)
    var_names = list(free) + list(fixed)

    # Run a BFS search
    queue = [[SearchState(
        node=terminal_node,
        last_node=None,
        values={n: 0 for n in var_names},
        graph=graph,
        call_stack_parent=None,
    ), None]]
    it = 0
    while len(queue) > 0 and it < limit:
        it += 1
        current_state, history = queue.pop(0)
        if current_state.node == initial_node and all(current_state.values[n] == fixed[n] for n in fixed):
            final_path = [current_state]
            while history is not None:
                head, history = history
                final_path.append(head)

            # One last check: try evaluator on search result.
            evaluate([cs.node for cs in final_path], current_state.values)

            return current_state, final_path

        for successor_state in compute_successor_states(current_state):
            queue.append([successor_state, [current_state, history]])

    return None
