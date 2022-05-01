import matplotlib.pyplot as plt
import networkx as nx


def plot_graph(g: nx.Graph) -> None:
    fig = plt.figure(figsize=(20, 20))

    ax = fig.add_subplot(1, 1, 1)

    labels = {node: str(node.op) for node in g.nodes}

    nx.draw_networkx(g, ax=ax, labels=labels, pos=nx.spring_layout(g))

    plt.show()
