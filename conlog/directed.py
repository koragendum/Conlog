import networkx as nx


def make_uturnless(g: nx.Graph) -> nx.DiGraph:
    """Create a directed copy of a graph where u-turns are not legal."""

    nodes = list(g.edges)
    nodes.extend((v, u) for u, v in g.edges)

    edges = []
    for u, v in nodes:
        for w in g.neighbors(v):
            if w != u:
                edges.append(((u, v), (v, w)))

    directed = nx.DiGraph()
    directed.add_nodes_from(nodes)
    directed.add_edges_from(edges)

    return directed
