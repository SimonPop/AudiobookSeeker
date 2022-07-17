from book_graph import BookGraph
import torch
from torch_geometric.utils.convert import from_networkx
from torch_geometric.utils.negative_sampling import negative_sampling


class LinkDataset(torch.utils.data.Dataset):
    def __init__(self, data, epochs=10):
        self.bookGraph = BookGraph(data)
        self.data = from_networkx(self.bookGraph.graph)
        self.epochs = epochs
        self.in_channels = 4

    def __getitem__(self, index):

        if index % 2 == 0:
            # Positive sampling
            edge_indexes = self.data.edge_index
            edge_labels = self.data.edge_label

        else:
            # Negative sampling
            edge_indexes = negative_sampling(
                edge_index=self.data.edge_index,
                num_neg_samples=None,
            )
            edge_labels = self.data.edge_label.new_zeros(edge_indexes.size(1))

        hours = torch.tensor([float(r) for r in self.data.hours])
        minutes = torch.tensor([float(r) for r in self.data.minutes])
        ratings = torch.tensor([float(r) for r in self.data.ratings])
        stars = torch.tensor([float(r) for r in self.data.stars])
        node_ids = torch.tensor([i for i in range(self.data.num_nodes)])
        features = torch.stack((hours, minutes, ratings, stars)).T.float()

        return features, node_ids, edge_indexes, edge_labels

    def __len__(self):
        return self.epochs

    def prepare_features(self):
        # Edge Features
        self.data.edge_label = torch.ones(self.data.edge_index.size(0))
