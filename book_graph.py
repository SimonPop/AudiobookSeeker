import networkx as nx

class BookGraph():

    def __init__(self):
        self.graph = nx.Graph()

    def create_graph(self, df):
        """Creates a connection graph from dataframe."""
        self.graph = nx.Graph()
        for _, row in df.iterrows():

            self.graph.add_node(row['id'])
            for node in row['recommendations']:
                self.graph.add_edge(row['id'], node)

        return self.graph