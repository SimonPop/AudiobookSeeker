from docarray import Document, DocumentArray
import torch


class SearchEngine:
    def __init__(self, embeddings_path=None, data_path=None):
        if not embeddings_path is None and not data_path is None:
            embeddings, data = self.load(embeddings_path, data_path)
            books = DocumentArray(
                [
                    Document(id=data_id, embedding=embedding)
                    for data_id, embedding in zip(data.id, embeddings["weight"])
                ]
            )
            id2title = dict(
                [(book_id, title) for book_id, title in zip(data.id, data.title)]
            )
        else:
            books = DocumentArray([])
            id2title = {}
        self.books = books
        self.id2title = id2title

    def load(self, embeddings_path, data_path) -> DocumentArray:
        """Load both the torch_geometric data & model's embeddings."""
        embeddings = torch.load("embeddings.pt")
        data = torch.load("data.pt")
        return embeddings, data

    def search(self, embedding, limit=5, metric="euclidean"):
        """Search nearby embeddings in known books."""
        doc = Document(embedding=embedding)
        query = doc.match(self.books, limit=limit, exclude_self=True, metric=metric)
        matches = query.matches[:, "id"]
        titles = [self.id2title[id] for id in matches]
        return titles
