import networkx as nx
import re 
import numpy as np
import pandas as pd
import math
import ast 

class BookGraph():

    def __init__(self, df):
        self.graph = nx.Graph()
        self.df = self.prepare_dataframe(df)
        self.create_graph(self.df)
        self.enrich_graph()
        self.add_edge_labels()

    def prepare_dataframe(self, df):
        time_pattern = re.compile("Length: ([0-9]*) hrs and ([0-9]*) mins")
        rating_pattern = re.compile("\(([0-9,]*) ratings\)")
        stars_pattern = re.compile("^[0-9,]")

        def extract_time(x):
            time_res = time_pattern.search(x)
            if time_res is None:
                return np.NaN, np.NaN
            else:
                return float(time_res.group(1)[0]), float(time_res.group(2)[0])

        def extract_stars_rating(raw_stars):
            ratings = stars = np.NaN
            if raw_stars is not None and str(raw_stars) != "nan":
                stars = float(stars_pattern.search(raw_stars).group(0)[0])
                ratings = float(rating_pattern.search(raw_stars).group(1)[0])
            return stars, ratings
        
        df['hours'], df['minutes'] = zip(*df['length'].apply(extract_time))
        df['stars'], df['ratings'] = zip(*df['stars'].apply(extract_stars_rating))

        return df

    def create_graph(self, df):
        """Creates a connection graph from dataframe."""
        self.graph = nx.Graph()
        for _, row in df.iterrows():
            self.graph.add_node(row['id'])
            for node in ast.literal_eval(row['recommendations']):
                if node in df['id'].values:
                    self.graph.add_edge(row['id'], node)


    def get_node_information(self, node_id):
        node = self.df[self.df['id'] == node_id]
        if len(node) == 0:
            return {
                'hours': np.NaN,
                'minutes': np.NaN,
                'ratings': np.NaN,
                'stars': np.NaN
            }
        return {
            'hours': node['hours'].iloc[0],
            'minutes': node['minutes'].iloc[0],
            'ratings': node['ratings'].iloc[0],
            'stars': node['stars'].iloc[0]
        }

    def get_edge_information(self, node_a, node_b):
        row_a = self.df[self.df['id'] == node_a]
        row_b = self.df[self.df['id'] == node_b]
        return {
            'same_author': row_a['author'].iloc[0] == row_b['author'].iloc[0] if (min(len(row_b), len(row_a)) > 0) else False,
            'same_narrator': row_a['narrator'].iloc[0] == row_b['narrator'].iloc[0] if (min(len(row_b), len(row_a)) > 0) else False,
            'same_series': row_a['subtitle'].iloc[0] == row_b['subtitle'].iloc[0] if (min(len(row_b), len(row_a)) > 0) else False
        }

    def enrich_graph(self):
        edge_features = [{}, {}, {}, {}]
        node_features = [{}, {}, {}, {}, {}]
        for e in self.graph.edges():
            e_info = self.get_edge_information(*e)
            for d, v in zip(edge_features, e_info.values()):
                d[e] = v
        for n in self.graph.nodes():
            n_info = self.get_node_information(n)
            for d, v in zip(node_features, n_info.values()):
                d[n] = v
        for d, k in zip(node_features, n_info.keys()):
            nx.set_node_attributes(self.graph, d, k)
        for d, k in zip(edge_features, e_info.keys()):
            nx.set_edge_attributes(self.graph, d, k)
    
    def add_edge_labels(self):
        nx.set_edge_attributes(self.graph, 1, "edge_label")