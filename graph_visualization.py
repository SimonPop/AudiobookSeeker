import networkx as nx
import matplotlib.pyplot as plt


def plot_graph(graph, figsize=(20, 20), sample=None):
    """Plots the graph fro quick visualization."""
    plt.figure(figsize=figsize)
    if not sample is None:
        graph = graph.subgraph(range(sample))
    layout = nx.spring_layout(graph)
    size = [v * figsize[0] for v in dict(graph.degree).values()]
    labels = nx.get_node_attributes(graph, "title")
    plt.title(
        "Book Graph {} ".format(
            "(sample {})".format(sample) if sample is not None else ""
        )
    )
    nx.draw(
        graph,
        pos=layout,
        labels=labels,
        with_labels=True,
        node_size=size,
        connectionstyle="arc3,rad=0.3",
    )
    plt.show()
