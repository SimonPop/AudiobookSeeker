import torch
from torch import nn
import torch.nn.functional as F
import pytorch_lightning as pl
from torch_geometric.nn import GCNConv
import torchmetrics
import optuna
from optuna.integration import PyTorchLightningPruningCallback


class LinkPredictor(pl.LightningModule):
    def __init__(
        self,
        in_channels,
        hidden_channels,
        out_channels,
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

        self.valid_acc = torchmetrics.Accuracy()

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
        self.valid_acc(y_hat, y)
        self.log("val_acc", self.valid_acc, on_step=True, on_epoch=True)
        return loss

    def _step(self, batch):
        (
            features,
            node_ids,
            pos_edge_indexes,
            neg_edge_indexes,
            pos_edge_labels,
            neg_edge_labels,
        ) = batch
        edge_indexes = torch.cat((neg_edge_indexes, pos_edge_indexes), dim=-1)
        labels = torch.cat((pos_edge_labels, neg_edge_labels), dim=-1)
        z = self.encode(features, node_ids, pos_edge_indexes.view(2, -1))
        y_hat = self.decode(
            z.view(features.size(1), -1),
            edge_indexes.view(2, -1),
        )
        return y_hat, labels.squeeze()

    def configure_optimizers(self):
        optimizer = torch.optim.Adam(self.parameters(), lr=1e-3)
        return optimizer

    def get_embeddings_weights(self):
        return self.embedding.weight

    def save_embeddings(self, path="embeddings.pt"):
        torch.save(self.embedding.state_dict(), path)

    @staticmethod
    def optimize(data, train_loader, val_loader):
        def objective(trial):

            hidden_layers = 2 ** trial.suggest_int("hidden_channels", 1, 3)
            # Create model for predicting links.
            model = LinkPredictor(
                in_channels=4,
                hidden_channels=hidden_layers,
                out_channels=1,
                embedding_size=16,
                num_nodes=data.num_nodes,
            )

            trainer = pl.Trainer(
                logger=True,
                checkpoint_callback=False,
                max_epochs=100,
                gpus=1 if torch.cuda.is_available() else None,
                callbacks=[PyTorchLightningPruningCallback(trial, monitor="val_acc")],
            )
            hyperparameters = dict(hidden_channels=hidden_layers)
            trainer.logger.log_hyperparams(hyperparameters)
            trainer.fit(model, train_loader, val_loader)

            return trainer.callback_metrics["val_acc"].item()

        # 3. Create a study object and optimize the objective function.
        study = optuna.create_study(direction="maximize")
        study.optimize(objective, n_trials=10)
        return study
