import networkx as nx

from conlog.brute import interpret
from conlog.datatypes import Initial, Node, Subtraction, Terminal


def test_triangle_sum() -> None:
    nodes = {
        x.name: x
        for x in [
            Node("initial", Initial(free=("T",), fixed=(("n", 6),))),
            Node("decr_x", Subtraction("n", 1)),
            Node("sub_t_x", Subtraction("T", "n")),
            Node("none", None),
            Node("terminal", Terminal()),
        ]
    }

    g = nx.Graph()
    g.add_edges_from(
        [
            (nodes["initial"], nodes["decr_x"]),
            (nodes["decr_x"], nodes["sub_t_x"]),
            (nodes["sub_t_x"], nodes["none"]),
            (nodes["none"], nodes["initial"]),
            (nodes["none"], nodes["terminal"]),
        ]
    )

    sols = interpret(g)

    sol_1 = next(sols)
    sol_2 = next(sols)

    # One solution has T == 21, another has T == 15
    assert {sol_1.assignment["T"], sol_2.assignment["T"]} == {15, 21}
