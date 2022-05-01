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


def elide_none_none(g: nx.DiGraph) -> nx.DiGraph:
    elided = nx.DiGraph()
    elided.add_nodes_from(g.nodes)

    for x, y in g.edges:
        if y[0].op is None and y[1].op is None:
            for _, yy in iter(g.out_edges(y)):
                elided.add_edge(x, yy)
        else:
            elided.add_edge(x, y)

    return elided
