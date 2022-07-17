import torch
import torch
from torch import batch_norm_stats, nn
import torch.nn.functional as F
import pytorch_lightning as pl
from torch_geometric.nn import GCNConv


class LinkPredictor(pl.LightningModule):
    def __init__(
        self,
        in_channels,
        hidden_channels,
        out_channels,
        edge_index,
        embedding_size,
        num_nodes,
    ):
        super().__init__()
        self.embedding_size = embedding_size
        self.num_nodes = num_nodes

        self.conv1 = GCNConv(in_channels + self.embedding_size, hidden_channels)
        self.conv2 = GCNConv(hidden_channels, out_channels)
        self.embedding = nn.Embedding(
            self.num_nodes, self.embedding_size, max_norm=True
        )

        self.edge_index = edge_index
        self.feature_nb = in_channels

    def forward(self, x):
        # in lightning, forward defines the prediction/inference actions
        embedding = self.encoder(x)
        return embedding

    def encode(self, x_features, node_ids, edge_index):
        x_embeddings = self.embedding(node_ids)
        x_features = x_features
        x = torch.concat((x_embeddings, x_features), dim=-1)
        x = self.conv1(x, edge_index).relu()
        return self.conv2(x, edge_index)

    def decode(self, z, edge_label_index):
        index_1 = edge_label_index[0]
        index_2 = edge_label_index[1]
        q = z[index_1] * z[index_2]
        return q.sum(dim=-1)

    def decode_all(self, z):
        prob_adj = z @ z.t()
        return (prob_adj > 0).nonzero(as_tuple=False).t()

    def training_step(self, batch, batch_idx):
        y_hat, y = self._step(batch)
        loss = F.binary_cross_entropy_with_logits(y_hat, y.float())
        self.log("train_loss", loss)
        return loss

    def validation_step(self, batch, batch_idx):
        y_hat, y = self._step(batch)
        loss = F.binary_cross_entropy_with_logits(y_hat, y.float())
        self.log("val_loss", loss)
        return loss

    def _step(self, batch):
        x, node_ids, selected_edge_indexes, y = batch
        z = self.encode(x, node_ids, self.edge_index)
        y_hat = self.decode(z.view(x.size(1), -1), selected_edge_indexes.view(2, -1))
        return y_hat, y.squeeze()

    def configure_optimizers(self):
        optimizer = torch.optim.Adam(self.parameters(), lr=1e-3)
        return optimizer
