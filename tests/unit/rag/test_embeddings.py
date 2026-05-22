from types import SimpleNamespace

from app.rag import embeddings


class FakeTextEmbedding:
    def __init__(self):
        self.embedded_batches = []

    def embed(self, texts):
        self.embedded_batches.append(list(texts))
        return [[1.0, 0.0]]


def test_warm_embedding_model_loads_configured_fastembed_model(monkeypatch):
    fake_embedding = FakeTextEmbedding()
    monkeypatch.setattr(
        embeddings,
        "get_settings",
        lambda: SimpleNamespace(embedding_model_name="local-demo-embedding-model"),
    )
    monkeypatch.setattr(embeddings, "_get_text_embedding", lambda: fake_embedding)

    model_name = embeddings.warm_embedding_model()

    assert model_name == "local-demo-embedding-model"
    assert fake_embedding.embedded_batches == [["sabi pass embedding warmup"]]
