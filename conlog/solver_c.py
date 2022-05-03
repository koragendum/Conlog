from __future__ import annotations
from enum import Enum, auto
from dataclasses import dataclass
from conlog.datatypes import Initial, Terminal
from conlog.elegant import determine_variable_bounds_multipass
from conlog.evaluator import evaluate
import networkx as nx



class arr_ptr:
    def __init__(self, arr, offset):
        self.arr = arr
        self.offset = offset
    def __iadd__(self, num):
        self.offset += num
        return self
    def __iter__(self):
        yield self.arr[self.offset]
    def __imul__(self, val):
        self.arr[self.offset] = val
        return self
    def __gt__(self, other):
        return self.offset > other.offset
    def __lt__(self, other):
        return self.offset < other.offset
    def __ge__(self, other):
        return self.offset >= other.offset
    def __le__(self, other):
        return self.offset <= other.offset
    def __eq__(self, other):
        return self.offset == other.offset
    def __ne__(self, other):
        return self.offset != other.offset



# Solve the grid BFS C pseudopython

MAX_DEGREE = 16
MAX_NUM_VALUES = 32
MAX_QUEUE_LENGTH = 1000000 # 2**24 = 16777216


uint8_t = int
uint16_t = int
uint32_t = int
uint64_t = int
int64_t = int
char = int
size_t = uint64_t


class NodeType(Enum):   # enum NodeType
    Initial = auto()
    Terminal = auto()
    Addition = auto()
    IntegerPrint = auto()
    UnicodePrint = auto()
    Subtraction = auto()
    ConditionalIncrement = auto()
    ConditionalDecrement = auto()
    NoneType = auto()


@dataclass
class CNode():  # Struct CNode
    node_type: NodeType
    node_i: uint64_t
    lhs: int64_t  # Index of the lhs operand
    rhs_is_constant: bool  # Whether rhs is a constant or an index
    rhs: int64_t  # Index/value of the rhs operand
    num_neighbors: size_t  # Number of neighbors of this node
    neighbor_arr: list[tuple[CNode]] # CNode * [MAX_DEGREE] (Yes, a POINTER ARRAY)


@dataclass
class CSearchState():  # Struct CSearchState
    node: tuple[CNode]  # CNode *
    last_node: tuple[CNode]  # CNode *
    values: list[int]  # int64_t[MAX_NUM_VALUES]
    parent_search_state: tuple[CSearchState]  # SearchState *


@dataclass
class CSearchWorkspace:  # Struct CSearchWorkspace
    search_queue: list[CSearchState]  # CSearchState[MAX_QUEUE_LENGTH]
    search_queue_next_free: arr_ptr  # CSearchState* . Add things via: *search_queue_next_free = thing; search_queue_next_free++
    search_queue_next_to_pop: arr_ptr  # CSearchState* . Add things via: thing = *search_queue_next_to_pop; search_queue_next_to_pop++
    node_arr: list[CNode]  # CNode[num_nodes]
    num_values: size_t  # Number of values of the graph
    num_free_values: size_t  # Number of values of the graph
    num_fixed_values: size_t  # Number of values of the graph
    fixed_values: list[uint64_t]  # uint64_t *  The values themselves
    terminal_node: tuple[CNode]  # CNode *
    iterations: uint64_t
    limit: uint64_t
    lower_bounds: int64_t
    upper_bounds: int64_t


# These don't have C equivalents; just make it easier to pretend
def _malloc_CNode():
    return CNode(
        node_type=None,
        node_i=None,
        lhs=None,
        rhs_is_constant=None,
        rhs=None,
        num_neighbors=None,
        neighbor_arr=[None] * MAX_DEGREE,
    )
def _stack_CSearchState():
    return CSearchState(  # ON THE STACK
        node=66,
        last_node=67, # placeholder that isn't None
        values=[None] * MAX_NUM_VALUES,
        parent_search_state=68, # placeholder that isn't None
    )
def _malloc_CSearchWorkspace():
    return CSearchWorkspace(
        search_queue=[None for _ in range(MAX_QUEUE_LENGTH)],
        search_queue_next_free=None,
        search_queue_next_to_pop=None,
        node_arr=None,
        num_values=None,
        num_free_values=None,
        num_fixed_values=None,
        fixed_values=None,
        terminal_node=None,
        iterations=None,
        limit=None,
        lower_bounds=None,
        upper_bounds=None,
    )



# public void * init_search_workspace()
def init_search_workspace(
    num_fixed_values: uint64_t,
    num_free_values: uint64_t,
    fixed_values: list[uint64_t],  # uint64_t *
    num_nodes: uint64_t,

    node_type_arr: uint8_t,
    node_lhs_arr: uint64_t,  # Index of the lhs operand
    node_rhs_is_constant_arr: bool,  # Whether rhs is a constant or an index
    node_rhs_arr: uint64_t,  # Index/value of the rhs operand

    adjacency_matrix: list[list[uint8_t]],  # uint8_t[num_nodes][num_nodes]
    limit: uint64_t,
    lower_bounds: list[uint64_t],  # lower_bounds[num_values]
    upper_bounds: list[uint64_t],  # upper_bounds[num_values]
) -> tuple[CSearchWorkspace]:

    # CSearchWorkspace * the_workspace = malloc(sizeof(CSearchWorkspace))
    the_workspace = _malloc_CSearchWorkspace()

    # Make the node array
    # Cnode * node_type_arr = malloc(sizeof(CNode) * num_nodes)
    node_arr = [_malloc_CNode() for _ in range(num_nodes)]
    for i in range(num_nodes):
        # Basics
        node_arr[i].node_type = node_type_arr[i]
        node_arr[i].node_i = i
        node_arr[i].lhs = node_lhs_arr[i]
        node_arr[i].rhs_is_constant = node_rhs_is_constant_arr[i]
        node_arr[i].rhs = node_rhs_arr[i]
        node_arr[i].num_neighbors = 0
    for i in range(num_nodes):
        for j in range(num_nodes):
            if (adjacency_matrix[i][j]):
                # node_arr[i].neighbor_arr[node_arr[i].num_neighbors] = &(node_arr[j])
                node_arr[i].neighbor_arr[node_arr[i].num_neighbors] = (node_arr[j],)
                node_arr[i].num_neighbors += 1  # ++
                if (node_arr[i].num_neighbors >= MAX_DEGREE):
                    print('Degree too high')
                    return None  # FAILURE; NULL VECTOR

    # .  ==>  ->
    # Put the first node on the search queue; the terminal node
    found_it: uint8_t = 0
    for i in range(num_nodes):
        if node_arr[i].node_type == NodeType.Terminal:
            found_it = 1
            the_workspace.terminal_node = node_arr[i]
            the_workspace.terminal_node_i = i
    if (not found_it):
        print('Did not find terminal node')
        return None  # FAILURE; NULL VECTOR

    first_search_state = _stack_CSearchState()

    first_search_state.node = the_workspace.terminal_node,
    first_search_state.last_node = None
    for i in range(MAX_NUM_VALUES):
        first_search_state.values[i] = 0
    first_search_state.parent_search_state = None

    # the_workspace.search_queue_next_to_pop = &(the_workspace->search_queue[0])
    the_workspace.search_queue_next_to_pop = arr_ptr(the_workspace.search_queue, 0)
    # the_workspace.search_queue_next_free = &(the_workspace->search_queue[0])
    the_workspace.search_queue_next_free = arr_ptr(the_workspace.search_queue, 0)
    # * (the_workspace->search_queue_next_free) = first_search_state
    the_workspace.search_queue_next_free *= first_search_state

    the_workspace.search_queue_next_free += 1

    # .  ==>  ->
    the_workspace.node_arr = node_arr 
    the_workspace.num_free_values = num_free_values
    the_workspace.num_fixed_values = num_fixed_values
    the_workspace.num_values = num_free_values + num_fixed_values
    # the_workspace->fixed_values = malloc(sizeof(uint64_t) * num_fixed_values)
    the_workspace.fixed_values = [0] * num_fixed_values
    for i in range(num_fixed_values):
        the_workspace.fixed_values[i] = fixed_values[i]
    the_workspace.iterations = 0
    the_workspace.limit = limit
    the_workspace.lower_bounds = lower_bounds
    the_workspace.upper_bounds = upper_bounds

    return the_workspace,  # the_workspace

# public int64_t * get_next_solution(
def get_next_solution(
    the_workspace: tuple[CSearchWorkspace], # void * the_workspace,  # Really it's a CSearchWorkspace * .. void* so I don't have to explain that to caller
) -> list[int]:
    # Doc: Returns an int64_t * ptr. It's an array of length at least 1, specced as follows:
    #
    #   [arr_size values0 values1 ... values{N-1} node_id0 node_id1 ... node_id{arr_size-1}]
    #
    # The elements are the node ids of the solution path.
    #
    # (note that it has arr_size+num_values+1 elements, if arr_size >= 0)
    #
    # If arr_size < 0, search failed. The malloc'd array is of length 1, eg.:
    #
    #   [-1]
    #

    the_workspace = the_workspace[0] # IGNORE THIS

    # queue_end = &(the_workspace->search_queue[MAX_QUEUE_LENGTH])
    queue_end = arr_ptr(the_workspace.search_queue, MAX_QUEUE_LENGTH - MAX_DEGREE - 1)

    iterations: uint64_t = the_workspace.iterations
    limit: uint64_t = the_workspace.limit
    num_values: size_t = the_workspace.num_values
    fixed_values: list[uint64_t] = the_workspace.fixed_values
    num_fixed_values: size_t = the_workspace.num_fixed_values
    search_queue_next_to_pop = the_workspace.search_queue_next_to_pop
    search_queue_next_free = the_workspace.search_queue_next_free
    lower_bounds = the_workspace.lower_bounds
    upper_bounds = the_workspace.upper_bounds

    # uint64_t new_values[MAX_NUM_VALUES];
    new_values: uint64_t = [0] * MAX_NUM_VALUES

    found_solution = False
    answer_search_head: CSearchState = None
    while (search_queue_next_free < queue_end) and (iterations < limit) and (not found_solution):
        iterations += 1

        if iterations == ((iterations >> 15) << 15):
            print(iterations)

        current_state ,= search_queue_next_to_pop
        search_queue_next_to_pop += 1

        # Create new values for this state

        for i in range(num_values):
            new_values[i] = current_state.values[i]

        match current_state.node[0].node_type:
            case NodeType.Addition | NodeType.Subtraction | NodeType.ConditionalIncrement | NodeType.ConditionalDecrement:
                rhs: uint64_t
                if current_state.node[0].rhs_is_constant:
                    rhs = current_state.node[0].rhs
                else:
                    rhs = new_values[current_state.node[0].rhs]

                rvalue: int64_t = -1  # reverse-search, so reverse the operation

                match current_state.node[0].node_type:
                    case NodeType.Subtraction | NodeType.ConditionalDecrement:
                        rvalue *= -1
                match current_state.node[0].node_type:
                    case NodeType.Addition | NodeType.Subtraction:
                        rvalue *= rhs
                match current_state.node[0].node_type:
                    case NodeType.ConditionalIncrement | NodeType.ConditionalDecrement:
                        if (rhs <= 0):
                            rvalue = 0  # Do nothing if condition not satisfied

                new_values[current_state.node[0].lhs] += rvalue
            case _:
                pass


        keep_going_from_here = True

        if (current_state.node[0].node_type == NodeType.Terminal) and (current_state.last_node != None):
            # Terminal nodes terminate this search path, unless it's the first node
            keep_going_from_here = False

        for i in range(num_values):
            if (new_values[i] < lower_bounds[i]) or (new_values[i] > upper_bounds[i]):
                keep_going_from_here = False
                # Bounds violation.
                break



        if (keep_going_from_here):
            # Make all successor states (this is where the LOGIC happens!)
            # for successor_state in compute_successor_states(current_state, bounds=bounds):
            #     queue.append([successor_state, [current_state, history]])
            for i in range(current_state.node[0].num_neighbors):
                # CNode * neighbor_node = current_state.node[0].neighbor_arr[i]
                neighbor_node: tuple[CNode] = current_state.node[0].neighbor_arr[i]

                if neighbor_node == current_state.last_node:
                    continue  # No backtracking allowed

                next_search_state = _stack_CSearchState()

                next_search_state.node = neighbor_node
                next_search_state.last_node = current_state.node[0],
                for i in range(num_values):
                    next_search_state.values[i] = new_values[i]
                # next_search_state.parent_search_state = &(current_state)
                next_search_state.parent_search_state = current_state,

                search_queue_next_free *= next_search_state
                search_queue_next_free += 1



        if (current_state.node[0].node_type == NodeType.Initial):
            fixed_equal = True
            for i in range(num_fixed_values):
                if (current_state.values[i] != fixed_values[i]):
                    fixed_equal = False
                    break

            if fixed_equal:
                found_solution = True
                answer_search_head = current_state


    # int64_t * ans;
    ans: int64_t

    if found_solution:
        # Traverse the `SearchState`s to find the length of the answer. Then malloc + copy node ids

        # CSearchState * current_search_head
        current_search_head: tuple[CSearchState]

        soln_len: uint64_t = 1
        current_search_head = answer_search_head,
        # [0]. ===> ->
        while current_search_head[0].parent_search_state != None:
            # current_search_head = current_search_head->parent_search_state
            current_search_head = current_search_head[0].parent_search_state
            soln_len += 1

        # ans = malloc(sizeof(int64_t) * (1 + num_values + soln_len))
        ans = [None] * (1 + num_values + soln_len)

        offset: uint64_t = 0

        ans[offset] = soln_len
        offset += 1

        for i in range(num_values):
            ans[offset] = current_state.values[i]
            offset += 1

        current_search_head = answer_search_head,
        ans[offset] = current_search_head[0].node[0].node_i
        offset += 1
        # [0]. ===> ->
        while current_search_head[0].parent_search_state != None:
            # current_search_head = current_search_head->parent_search_state
            current_search_head = current_search_head[0].parent_search_state
            ans[offset] = current_search_head[0].node[0].node_i
            offset += 1

    else:
        # ans = malloc(sizeof(int64_t) * 1)
        ans = [None]
        ans[0] = -1  # This special array will make it clear we failed.

    # . ===> ->
    the_workspace.iterations = iterations
    the_workspace.limit = limit
    the_workspace.search_queue_next_to_pop = search_queue_next_to_pop

    return ans



def solve_graph_bfs_c(graph: nx.Graph, limit = None):
    # Some Python preprocessing

    initial_node = next(node for node in graph.nodes if isinstance(node.op, Initial))
    terminal_node = next(node for node in graph.nodes if isinstance(node.op, Terminal))
    free, fixed = initial_node.op.free, dict(initial_node.op.fixed)

    # VERY IMPORTANT THAT ALL FIXED COME FIRST!
    var_names = list(fixed) + list(free)

    num_fixed_values = len(fixed)
    num_free_values = len(free)
    num_values = num_fixed_values + num_free_values
    fixed_values = list(fixed.values())

    nodes = list(graph.nodes)

    num_nodes = len(nodes)
    node_type_arr = [getattr(NodeType, type(node.op).__name__) for node in nodes]

    node_lhs_arr = [var_names.index(node.op.lhs) if node.op and hasattr(node.op, 'lhs') else 0 for node in nodes]
    node_rhs_is_constant_arr = [int(isinstance(node.op.rhs, int)) if (node.op and hasattr(node.op, 'lhs')) else 0 for node in nodes]
    node_rhs_arr = [(node.op.rhs if isinstance(node.op.rhs, int) else var_names.index(node.op.rhs))  if (node.op and hasattr(node.op, 'lhs')) else 0 for node in nodes]
    
    adjacency_matrix = [[graph.has_edge(nodes[i], nodes[j]) for i in range(len(nodes))] for j in range(len(nodes))]

    # Get lowest signed int64:
    LOWEST, HIGHEST = -2**63, 2**63 - 1

    bounds = {k: [LOWEST, HIGHEST] for k in var_names}
    bounds.update(determine_variable_bounds_multipass(graph))

    lower_bounds = [int(bounds[var][0]) if bounds[var][0] > float('-inf') else LOWEST for var in var_names]
    upper_bounds = [int(bounds[var][1]) if bounds[var][1] < float('inf') else HIGHEST for var in var_names]

    assert var_names[0] == list(fixed)[0]

    the_workspace = init_search_workspace(
        num_fixed_values,
        num_free_values,
        fixed_values,
        num_nodes,
        node_type_arr,
        node_lhs_arr,
        node_rhs_is_constant_arr,
        node_rhs_arr,
        adjacency_matrix,
        limit,
        lower_bounds,
        upper_bounds,
    )

    ans = None
    while True:
        ans = get_next_solution(the_workspace)  # TODO: Something with the weird array format
        ans_len = ans[0]
        if ans_len == -1:
            break

        final_values = ans[1:num_values + 1]
        final_path = ans[num_values + 1:ans_len + num_values + 1]
        print(ans)

        final_values = dict(zip(var_names, final_values))

        # Turn answer into a proper solution
        solution = evaluate([nodes[i] for i in final_path], final_values)

        if solution is None:
            raise Exception('BFS solver thought an invalid solution was valid')

        # Free the malloced ans
        # free(ans)
        del ans

        yield solution
