import networkx as nx

from conlog.datatypes import (
    Addition,
    Initial,
    Node,
    Operation,
    Print,
    Subtraction,
    Terminal,
    make_graph,
)

"""
Graph that computes either T=triangle_sum(x) or T=triangle_sum(x-1)
depending on the first path taken. (no one-way gadget used)

    Initial----------------None---Terminal
       |                    |
       '--DecrX----SubFbyX--'

"""
either_trisum_nodes = [
    Node("initial", Initial(free=("T",), fixed=(("n", 6),))),
    Node("decr_x", Subtraction("n", 1)),
    Node("sub_t_x", Subtraction("T", "n")),
    Node("none", None),
    Node("terminal", Terminal()),
]
either_trisum_d = {n.name: n for n in either_trisum_nodes}

either_trisum_graph = make_graph(
    edges=[
        (either_trisum_d["initial"], either_trisum_d["decr_x"]),
        (either_trisum_d["decr_x"], either_trisum_d["sub_t_x"]),
        (either_trisum_d["sub_t_x"], either_trisum_d["none"]),
        (either_trisum_d["none"], either_trisum_d["initial"]),
        (either_trisum_d["none"], either_trisum_d["terminal"]),
    ],
)
