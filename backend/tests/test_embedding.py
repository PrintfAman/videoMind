import math

from app.services.embedding_service import EmbeddingService


class FakeModel:
    def encode(self, texts, convert_to_numpy=False):
        if isinstance(texts, str):
            texts = [texts]
        vectors = []
        for text in texts:
            values = [float(len(text)), float(sum(ord(ch) for ch in text) % 100)]
            vectors.append(values)
        return vectors


def test_embedding_service_generates_vector(monkeypatch):
    EmbeddingService._instance = None

    def fake_loader(self):
        return FakeModel()

    monkeypatch.setattr(EmbeddingService, "_load_model", fake_loader)

    service = EmbeddingService()
    embedding = service.embed("person cooking in kitchen")

    assert isinstance(embedding, list)
    assert len(embedding) == 2
    assert all(isinstance(v, float) for v in embedding)
    assert math.isfinite(embedding[0])
    assert math.isfinite(embedding[1])
