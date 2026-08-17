from fastapi.testclient import TestClient

from app.main import app


class FakeRetrievalService:
    def search(self, query, k=5):
        return [
            {
                "score": 0.93,
                "video": "abc.mp4",
                "event_id": "evt-1",
                "start": 12.3,
                "end": 19.7,
                "speech": "person enters kitchen",
                "vision": "someone cooking",
            }
        ]


def test_search_endpoint(monkeypatch):
    import app.api.search as search_module

    monkeypatch.setattr(search_module, "retrieval_service", FakeRetrievalService())

    client = TestClient(app)
    response = client.post("/search", json={"query": "person entering kitchen", "top_k": 5})

    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["video"] == "abc.mp4"
    assert data[0]["score"] == 0.93
