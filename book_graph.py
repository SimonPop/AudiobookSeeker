import networkx as nx
import re 
import numpy as np
import pandas as pd
import math
import ast 

class BookGraph():

    def __init__(self, df):
        self.graph = nx.Graph()
        self.df = pd.DataFrame()
        self.create_graph(df)
        self.enrich_graph()

    def create_graph(self, df):
        """Creates a connection graph from dataframe."""
        self.graph = nx.Graph()
        rows = []
        for _, row in df.iterrows():

            res = self.parse_row(row)
            rows.append(res)

            self.graph.add_node(row['id'])
            for node in ast.literal_eval(row['recommendations']):
                self.graph.add_edge(row['id'], node)

        self.df = pd.DataFrame(rows)

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
        for d, k in zip(edge_features, n_info.keys()):
            nx.set_edge_attributes(self.graph, d, k)
    
    def parse_row(self, row):
        length_regex = re.search("Length: ([0-9]*) hrs and ([0-9]*) mins", row['length'])
        ratings = stars = np.NaN
        if row['stars'] is not None and not row['stars'] != "nan": # TODO: != nan
            stars = float(re.search("^[0-9,]", row['stars']).group(0)[0])
            ratings = float(re.search("\(([0-9,]*) ratings\)", row['stars']).group(1)[0])
        return {
            'recommendations': row['recommendations'],
            'id': row['id'],
            'title': row['title'], 
            'subtitle': row['subtitle'], 
            'author': row['author'], 
            'narrator': row['narrator'], 
            'hours': np.NaN if length_regex is None else float(length_regex.group(1)[0]), 
            'minutes': np.NaN if length_regex is None else float(length_regex.group(2)[0]), 
            'stars': stars,
            'ratings': ratings
        }