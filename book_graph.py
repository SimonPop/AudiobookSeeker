import networkx as nx
from neo4j.graph import Node, Relationship
from torch_geometric.utils.convert import from_networkx
from graph_visualization import plot_graph


class BookGraph:
    def __init__(self, data=None):
        self.graph = nx.Graph()
        if not data is None:
            self.graph = self.graph_from_cypher(data)
        self.add_edge_labels()

    def add_edge_labels(self):
        nx.set_edge_attributes(self.graph, 1, "edge_label")

    def to_torch(self):
        """Converts to a usable PyTorh Geometric data."""
        return from_networkx(self.graph)

    def plot(self, **kwargs):
        """Plots the graph"""
        plot_graph(self.graph, **kwargs)

    def graph_from_cypher(self, data):
        G = nx.MultiDiGraph()

        def add_node(node):
            # Adds node id it hasn't already been added
            u = node.id
            if G.has_node(u):
                return
            G.add_node(u, **dict(node))

        def add_edge(relation):
            # Adds edge if it hasn't already been added.
            # Make sure the nodes at both ends are created
            for node in (relation.start_node, relation.end_node):
                add_node(node)
            # Check if edge already exists
            u = relation.start_node.id
            v = relation.end_node.id
            eid = relation.id
            if G.has_edge(u, v, key=eid):
                return
            # If not, create it
            G.add_edge(u, v, key=eid, **dict(relation))

        for d in data:
            for entry in d.values():
                # Parse node
                if isinstance(entry, Node):
                    add_node(entry)

                # Parse link
                elif isinstance(entry, Relationship):
                    add_edge(entry)
                else:
                    raise TypeError("Unrecognized object")
        return G
