from docarray import Document, DocumentArray
import torch


class SearchEngine:
    def __init__(self, embeddings_path=None, data_path=None):
        if not embeddings_path is None and not data_path is None:
            embeddings, data = self.load(embeddings_path, data_path)
            books = DocumentArray(
                [
                    Document(id=data_id, embedding=embedding)
                    for data_id, embedding in zip(data.id, embeddings)
                ]
            )
            id2title = dict(
                [(book_id, title) for book_id, title in zip(data.id, data.title)]
            )
            title2num = dict([(t, i) for i, t in enumerate(data.title)])
        else:
            books = DocumentArray([])
            embeddings = None
            data = None
            id2title = {}
            title2num = {}

        self.embeddings = embeddings
        self.data = data
        self.books = books
        self.id2title = id2title
        self.title2num = title2num

    def load(self, embeddings_path, data_path) -> DocumentArray:
        """Load both the torch_geometric data & model's embeddings."""
        embeddings = torch.load("embeddings.pt")["weight"]
        data = torch.load("data.pt")
        return embeddings, data

    def search(self, titles, limit=5, metric="euclidean"):
        """Search nearby embeddings in known books."""
        embedding = torch.stack(
            [self.embeddings[self.title2num[title]] for title in titles], dim=0
        ).sum(dim=0) / len(titles)
        doc = Document(embedding=embedding)
        query = doc.match(self.books, limit=limit, exclude_self=True, metric=metric)
        matches = query.matches[:, "id"]
        scores = [m.scores["euclidean"].value for m in query.matches]
        titles = [self.id2title[id] for id in matches]
        return titles, scores

    def all_titles(self):
        return self.data.title
