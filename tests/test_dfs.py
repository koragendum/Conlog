from conlog.datatypes import Graph, Node, dfs


def test_dfs_line_graph():
    """Test DFS on a simple graph."""

    N = 3
    nodes = tuple(Node(name=str(i), op=None) for i in range(N))
    edges = tuple(zip(nodes, nodes[1:]))

    g = Graph(nodes=nodes, edges=edges)

    for i in range(N):
        gg = dfs(g, nodes[i])

        # We find all nodes regardless of starting point
        assert set(g.nodes) == set(gg.nodes)

        # We find all edges regardless of starting point
        for u, v in g.edges:
            assert gg.has_edge(u, v)
