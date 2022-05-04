from libcpp cimport bool, nullptr
from numpy cimport uint64_t, int64_t, uint8_t
# from cython.cimports.libc.stdlib cimport malloc, free
cimport cython

from enum import Enum, auto
import numpy as np
from conlog.datatypes import Initial, Terminal
from conlog.elegant import determine_variable_bounds_multipass
from conlog.evaluator import evaluate



def func(t):
    return 0


class NodeTypePython(Enum):
    Initial = 1
    Terminal = 2
    Addition = 3
    IntegerPrint = 4
    UnicodePrint = 5
    Subtraction = 6
    ConditionalIncrement = 7
    ConditionalDecrement = 8
    NoneType = 9


cdef extern from "solver_c_fast.c":
    void * init_search_workspace_lowlevel(
        uint64_t num_fixed_values,
        uint64_t num_free_values,
        int64_t * fixed_values,
        uint64_t num_nodes,

        uint8_t * node_type_arr,
        int64_t * node_lhs_arr,
        uint8_t * node_rhs_is_constant_arr,
        int64_t * node_rhs_arr,

        uint8_t* adjacency_matrix,
        uint64_t limit,
        int64_t * lower_bounds,
        int64_t * upper_bounds,
    )

    int64_t * get_next_solution_lowlevel(void * the_workspace_ptr)


def solve_graph_bfs_c(graph, limit):
    # Some Python preprocessing

    initial_node = next(node for node in graph.nodes if isinstance(node.op, Initial))
    terminal_node = next(node for node in graph.nodes if isinstance(node.op, Terminal))
    free_vars, fixed_vars = initial_node.op.free, dict(initial_node.op.fixed)

    # VERY IMPORTANT THAT ALL FIXED COME FIRST!
    var_names = list(fixed_vars) + list(free_vars)

    num_fixed_values = len(fixed_vars)
    num_free_values = len(free_vars)
    num_values = num_fixed_values + num_free_values
    fixed_values = list(fixed_vars.values())

    nodes = list(graph.nodes)
    nodes = sorted(nodes, key=str)

    num_nodes = len(nodes)
    node_type_arr = [getattr(NodeTypePython, type(node.op).__name__).value for node in nodes]

    node_lhs_arr = [var_names.index(node.op.lhs) if node.op and hasattr(node.op, 'lhs') else 0 for node in nodes]
    node_rhs_is_constant_arr = [int(isinstance(node.op.rhs, int)) if (node.op and hasattr(node.op, 'lhs')) else 0 for node in nodes]
    node_rhs_arr = [(node.op.rhs if isinstance(node.op.rhs, int) else var_names.index(node.op.rhs))  if (node.op and hasattr(node.op, 'lhs')) else 0 for node in nodes]

    adjacency_matrix = [int(graph.has_edge(nodes[i], nodes[j])) for i in range(len(nodes)) for j in range(len(nodes))]

    # Get lowest signed int64:
    LOWEST, HIGHEST = -2**63, 2**63 - 1

    bounds = {k: [LOWEST, HIGHEST] for k in var_names}
    bounds.update(determine_variable_bounds_multipass(graph))

    lower_bounds = [int(bounds[var][0]) if bounds[var][0] > float('-inf') else LOWEST for var in var_names]
    upper_bounds = [int(bounds[var][1]) if bounds[var][1] < float('inf') else HIGHEST for var in var_names]

    assert var_names[0] == list(fixed_vars)[0]

    cdef void * the_workspace = NULL

    fixed_values = np.ascontiguousarray(np.array(fixed_values, dtype=np.int64))
    node_type_arr = np.ascontiguousarray(np.array(node_type_arr, dtype=np.uint8))
    node_lhs_arr = np.ascontiguousarray(np.array(node_lhs_arr, dtype=np.int64))
    node_rhs_is_constant_arr = np.ascontiguousarray(np.array(node_rhs_is_constant_arr, dtype=np.uint8))
    node_rhs_arr = np.ascontiguousarray(np.array(node_rhs_arr, dtype=np.int64))
    adjacency_matrix = np.ascontiguousarray(np.array(adjacency_matrix, dtype=np.uint8))
    lower_bounds = np.ascontiguousarray(np.array(lower_bounds, dtype=np.int64))
    upper_bounds = np.ascontiguousarray(np.array(upper_bounds, dtype=np.int64))

    # Make memoryviews (mvs)
    cdef int64_t[::1] fixed_values_mv = fixed_values
    cdef uint8_t[::1] node_type_arr_mv = node_type_arr
    cdef int64_t[::1] node_lhs_arr_mv = node_lhs_arr
    cdef uint8_t[::1] node_rhs_is_constant_arr_mv = node_rhs_is_constant_arr
    cdef int64_t[::1] node_rhs_arr_mv = node_rhs_arr
    cdef uint8_t[::1] adjacency_matrix_mv = adjacency_matrix
    cdef int64_t[::1] lower_bounds_mv = lower_bounds
    cdef int64_t[::1] upper_bounds_mv = upper_bounds

    cdef uint64_t num_fixed_values_ctype = np.uint64(num_fixed_values)
    cdef uint64_t num_free_values_ctype = np.uint64(num_free_values)
    cdef uint64_t num_nodes_ctype = np.uint64(num_nodes)
    cdef uint64_t limit_ctype = np.uint64(limit)

    the_workspace = init_search_workspace_lowlevel(
        num_fixed_values_ctype,
        num_free_values_ctype,
        &fixed_values_mv[0],
        num_nodes_ctype,
        &node_type_arr_mv[0],
        &node_lhs_arr_mv[0],
        &node_rhs_is_constant_arr_mv[0],
        &node_rhs_arr_mv[0],
        &adjacency_matrix_mv[0],
        limit_ctype,
        &lower_bounds_mv[0],
        &upper_bounds_mv[0],
    )

    if the_workspace == NULL:
        print ("Received NULL the_workspace from init")
        return

    cdef int64_t * ans

    while True:
        ans = get_next_solution_lowlevel(the_workspace)  # TODO: Something with the weird array format
        ans_len = ans[0]
        if ans_len == -1:
            # free(ans)   # TODO free ans
            break

        final_values = np.zeros((num_values,), dtype=np.int64)
        for i in range(num_values):
            final_values[i] = ans[1 + i]

        final_path = np.zeros((ans_len,), dtype=np.int64)
        for i in range(ans_len):
            final_path[i] = ans[1 + num_values + i]

        final_values = dict(zip(var_names, final_values))

        # Turn answer into a proper solution
        print([nodes[i] for i in final_path])
        print(final_values)
        solution = evaluate([nodes[i] for i in final_path], final_values)

        if solution is None:
            raise Exception('BFS solver thought an invalid solution was valid')

        # Free the malloced array
        # free(ans)   # TODO free ans

        yield solution

