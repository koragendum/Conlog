from conlog.datatypes import (
    Addition,
    ConditionalAddition,
    make_graph,
    Initial,
    Node,
    Subtraction,
    Terminal,
)
import networkx as nx


def make_swap_graph(x: str = "X", y: str = "Y", z: str = "Z") -> nx.Graph:
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
        Node("initial", Initial(free=(x, y), fixed=((z, 0),))),
        Node("add_z_y", Addition(z, y)),
        Node("sub_y_z", Subtraction(y, z)),
        Node("add_y_x", Addition(y, x)),
        Node("sub_x_y", Subtraction(x, y)),
        Node("add_x_z", Addition(x, z)),
        Node("sub_z_x", Subtraction(z, x)),
        Node("terminal", Terminal()),
    ]
    # Nice and linear
    return make_graph(edges=list(zip(swap_nodes[:-1], swap_nodes[1:])))


def make_diode_graph(y: str = "Y", z: str = "Z") -> nx.Graph:
    """
    Swaps x and y when used as a subgraph.

        Initial free: (x, y) fixed z=0
          |
         y+=1
         z+?y
         y-=1
          |
        Terminal

    """
    diode_nodes = [
        Node("initial", Initial(free=tuple(), fixed=((y, 0), (z, 0),))),
        Node("incr_y", Addition(y, 1)),
        Node("cond_add_z_y", ConditionalAddition(z, y)),
        Node("decr_y", Subtraction(y, 1)),
        Node("terminal", Terminal()),
    ]
    # Nice and linear
    return make_graph(edges=list(zip(diode_nodes[:-1], diode_nodes[1:])))
