"""
Deprecated

"""
from conlog.solver import solve_graph_bfs
from conlog.datatypes import (
    add_edges_to_graph,
    Addition,
    make_graph,
    Function,
    Initial,
    Node,
    Subtraction,
    Terminal,
)
import networkx as nx


if __name__ == '__main__':
    """
    Swaps x and y when used as a subgraph.

        Initial free: (x, y) fixed z=0
          |
         z+=y
         y-=z
         y+=x
         x-=y
         x+=z
         z+=x
          |
        Terminal

    """
    swap_nodes = [
        Node("initial", Initial(free=("X", "Y"), fixed=(("Z", 0),))),
        Node("add_z_y", Addition("Z", "Y")),
        Node("sub_y_z", Subtraction("Y", "Z")),
        Node("add_y_x", Addition("Y", "X")),
        Node("sub_x_y", Subtraction("X", "Y")),
        Node("add_x_z", Addition("X", "Z")),
        Node("sub_z_x", Subtraction("Z", "X")),
        Node("terminal", Terminal()),
    ]

    # Nice and linear
    swap_graph = make_graph(edges=list(zip(swap_nodes[:-1], swap_nodes[1:])))

    """
    Fibonacci!

        Initial----------------None--DecrX--Terminal
           |                    |
           '-SwapXY---SubXY---DecrZ

    """
    fib_graph = nx.Graph()
    fib_nodes = [
        Node("initial", Initial(free=("x", "y"), fixed=(("z", 8),))),
        Node("swap_x_y", Function(graph=swap_graph, var_map=(('x', 'X'), ('y', 'Y')))),
        Node("sub_x_y", Subtraction("x", "y")),
        Node("decr_z", Subtraction("z", 1)),
        Node("none", None),
        Node("decr_x", Subtraction("x", 1)),
        Node("terminal", Terminal()),
    ]
    fib_d = {n.name: n for n in fib_nodes}

    add_edges_to_graph(
        edges=[
            (fib_d["initial"], fib_d["swap_x_y"]),
            (fib_d["swap_x_y"], fib_d["sub_x_y"]),
            (fib_d["sub_x_y"], fib_d["decr_z"]),
            (fib_d["decr_z"], fib_d["none"]),
            (fib_d["none"], fib_d["initial"]),
            (fib_d["none"], fib_d["decr_x"]),
            (fib_d["decr_x"], fib_d["terminal"]),
        ],
        g=fib_graph,
    )

    ans, final_path = solve_graph_bfs(fib_graph)
    print()
    print(ans)
    print()
    for n in final_path:
        print(n)


