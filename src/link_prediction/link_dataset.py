from ..graph.book_graph import BookGraph
import torch
from torch_geometric.utils.negative_sampling import negative_sampling
from torch_geometric.transforms import RandomLinkSplit
from pytorch_lightning.utilities.seed import seed_everything

seed_everything()


class LinkDataset(torch.utils.data.Dataset):
    def __init__(self, data, full_edge_data, epochs=10):
        self.data = data
        self.full_edge_data = full_edge_data  # Used not to create accidentally negative edges that exists in validation / train / test but not this set.
        self.epochs = epochs
        self.in_channels = 4

    def __getitem__(self, index):

        # Positive sampling
        pos_edge_indexes = self.data.edge_index
        pos_edge_labels = self.data.edge_label.new_zeros(pos_edge_indexes.size(1)) + 1

        # Negative sampling
        neg_edge_indexes = negative_sampling(
            edge_index=self.full_edge_data.edge_index,
            num_neg_samples=self.data.num_edges,
        )
        neg_edge_labels = self.data.edge_label.new_zeros(neg_edge_indexes.size(1))

        hours = torch.tensor([float(r) for r in self.data.hours]).nan_to_num()
        minutes = torch.tensor([float(r) for r in self.data.minutes]).nan_to_num()
        ratings = torch.tensor([float(r) for r in self.data.ratings]).nan_to_num()
        stars = torch.tensor([float(r) for r in self.data.stars]).nan_to_num()
        node_ids = torch.tensor([i for i in range(self.data.num_nodes)]).nan_to_num()
        features = torch.stack((hours, minutes, ratings, stars)).T.float()

        return (
            features,
            node_ids,
            pos_edge_indexes,
            neg_edge_indexes,
            pos_edge_labels,
            neg_edge_labels,
        )

    def __len__(self):
        return self.epochs

    def prepare_features(self):
        # Edge Features
        self.data.edge_label = torch.ones(self.data.edge_index.size(0))
