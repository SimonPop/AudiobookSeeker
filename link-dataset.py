from book_graph import BookGraph
import torch

class LinkDataset(torch.utils.data.Dataset):

    def __init__(self):
        self.bookGraph = BookGraph()

    def __getitem__(self):
        pass

    def __len__(self):
        pass

    def prepare_features(self):
        # Edge Features
        self.prepare_edge_features()
        # Node Features
        self.prepare_node_features()

    def prepare_edge_features(self):
        # Same author
        # Same narator
        # Same series
        pass

    def prepare_node_features(self):
        # Rating
        # Length
        # Catégories
        # Text features
        pass
