from app.services.vector_store import VectorStore


def test_vector_store_upsert_and_search(tmp_path):
    store = VectorStore(path=str(tmp_path / "vector_db"), collection_name="unit_test_events")
    store.create_collection()

    inserted = store.upsert(
        event_id="evt-1",
        video_id="video-1",
        start=12.0,
        end=18.0,
        text="person cooking in kitchen",
        metadata={"scene_id": 1},
        embedding=[0.1, 0.2, 0.3],
    )

    assert inserted is True
    assert store.count() == 1

    results = store.search([0.1, 0.2, 0.3], n_results=5)
    assert len(results) == 1
    assert results[0]["metadata"]["video_id"] == "video-1"
    assert results[0]["metadata"]["event_id"] == "evt-1"
