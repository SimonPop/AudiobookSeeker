import torch 
import torch
from torch import nn
import torch.nn.functional as F
import pytorch_lightning as pl
from torch_geometric.nn import GCNConv

class LinkPredictor(pl.LightningModule):
    def __init__(self, in_channels, hidden_channels, out_channels, edge_index):
        super().__init__()
        self.conv1 = GCNConv(in_channels, hidden_channels)
        self.conv2 = GCNConv(hidden_channels, out_channels)
        self.edge_index = edge_index

    def forward(self, x):
        # in lightning, forward defines the prediction/inference actions
        embedding = self.encoder(x)
        return embedding

    def encode(self, x, edge_index):
        x = self.conv1(x, edge_index).relu()
        return self.conv2(x, edge_index)

    def decode(self, z, edge_label_index):
        return (z[edge_label_index[0]] * z[edge_label_index[1]]).sum(dim=-1)

    def decode_all(self, z):
        prob_adj = z @ z.t()
        return (prob_adj > 0).nonzero(as_tuple=False).t()

    def training_step(self, batch, batch_idx):
        x, selected_edge_indexes, y = batch
        x = x.view(x.size(0), -1)
        z = self.encode(x, self.edge_index)
        y_hat = self.decode(z, selected_edge_indexes)
        loss =F.binary_cross_entropy_with_logits(y_hat, y)
        self.log("train_loss", loss)
        return loss

    def configure_optimizers(self):
        optimizer = torch.optim.Adam(self.parameters(), lr=1e-3)
        return optimizer