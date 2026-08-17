# Milestone 6 Engineering Report — Semantic Search (Embeddings + Vector Database)

Date: 2026-08-17

## Summary

Milestone 6 transforms VideoMind AI from a pipeline that produces structured events into a semantic video search engine. Each event is converted into an embedding and indexed in ChromaDB, allowing natural language retrieval such as “show me the scene where someone is cooking.” The implementation follows the existing Clean Architecture layout, keeps the pipeline intact, and adds a minimal retrieval API that returns top-k matches with similarity scores.

## Files created

- `app/services/embedding_service.py` — lazy singleton SentenceTransformer wrapper
- `app/services/vector_store.py` — ChromaDB persistence wrapper with create/upsert/search/delete/count methods
- `app/services/retrieval.py` — natural language query embedding and retrieval orchestration
- `app/api/search.py` — `/search` FastAPI route
- `app/schemas/search.py` — request/response schemas for semantic search
- `tests/test_embedding.py` — embedding generation unit test
- `tests/test_vector_store.py` — vector insertion and search unit test
- `tests/test_search_api.py` — search endpoint unit test
- `MILESTONE6_REPORT.md` — milestone engineering report

## Files modified

- `app/core/config.py` — added `embedding_model`, `vector_db_path`, `top_k_default`, and `device`
- `app/api/__init__.py` — registered search router
- `app/services/stages.py` — event indexing to ChromaDB inserted after event-building stage
- `app/services/event_builder.py` — fallback generation for transcript-only events when scene data is empty
- `README.md` — milestone documentation and API usage instructions

## Architecture diagram

```mermaid
flowchart TD
  Upload --> Orchestrator
  Orchestrator --> Metadata
  Orchestrator --> Audio
  Orchestrator --> Whisper
  Orchestrator --> Scenes
  Orchestrator --> Keyframes
  Orchestrator --> Vision
  Orchestrator --> EventBuilder
  EventBuilder --> EventJSON[data/events/<video_id>.json]
  EventBuilder --> EmbeddingService
  EmbeddingService --> ChromaDB[ChromaDB vector database]
  UserQuery --> RetrievalService
  RetrievalService --> EmbeddingService
  RetrievalService --> ChromaDB
  ChromaDB --> SearchAPI[/search endpoint]
```

## Complete execution flow

1. Video is uploaded and processed via the orchestrator pipeline.
2. Metadata, audio, transcript, scenes, keyframes, and vision outputs are produced.
3. `EventStage` invokes the event builder to fuse scene-level metadata and transcript/vision text.
4. For each resulting event, a combined text string is created from summary/speech/caption/objects/activities.
5. `EmbeddingService` lazily loads a SentenceTransformer model and encodes the event text.
6. `VectorStore` persists the vector and metadata in ChromaDB under `data/vector_db`.
7. A natural-language query is embedded by `RetrievalService` and compared against the stored vectors.
8. Top-k results are ranked by cosine similarity and returned to the API client.

## Embedding generation process

Each event is converted into a text payload such as:

```text
"person enters kitchen cooking food indoors kitchen activity"
```

This is then embedded using the default model:

```text
BAAI/bge-small-en-v1.5
```

The model is loaded lazily and cached in a singleton instance. Logging records:

- model load start and completion
- embedding generation duration
- vector insertion latency
- retrieval time
- ranking score values

## ChromaDB explanation

ChromaDB is a vector database optimized for nearest-neighbor similarity search over embedded content. In this milestone, it stores one document per event with:

- `id`: unique event identifier
- `embedding`: dense vector representation of the event text
- `document`: source text used to generate the embedding
- `metadata`: event metadata such as `video_id`, `event_id`, `start`, `end`, `speech`, `vision`

The database is configured as a persistent local collection under `backend/data/vector_db`, which allows repeated reads without restarting the service.

## Similarity search explanation

A user query is embedded with the same model used for event generation. ChromaDB evaluates the query vector against the stored event embeddings using nearest-neighbor similarity. Results are ranked from highest similarity to lowest, and the retrieval service converts them into a user-friendly payload containing:

- `score`
- `video`
- `event_id`
- `start`
- `end`
- `speech`
- `vision`

In practice, queries like “person entering kitchen” align with events whose text summaries include kitchen, cooking, scene, or motion semantics even when exact keywords are absent.

## API documentation

### Endpoint

`POST /search`

### Request

```json
{
  "query": "person entering kitchen",
  "top_k": 5
}
```

### Response

```json
[
  {
    "score": 0.93,
    "video": "abc.mp4",
    "event_id": "abc:3",
    "start": 12.3,
    "end": 19.7,
    "speech": "person enters kitchen",
    "vision": "someone cooking"
  }
]
```

## Engineering review

### Strengths

- Clean separation between event generation, embedding, and retrieval.
- Singleton embedding service prevents repeated model load overhead.
- Vector database is local and persistent for easier local development.
- Search API is thin and follows FastAPI patterns already used by the project.

### Risks

- Embedding model download can be slow on first run.
- Scene detection may still return zero scenes on some videos; fallback transcript-based events are used to preserve functionality.
- Default model is CPU-only in local config; GPU can be enabled via the `device` setting when available.

## Scalability discussion

This implementation is sufficient for local experimentation and small production workloads. For scale:

- move from local ChromaDB to a hosted vector database for multi-instance deployments
- shard or partition by video ID or tenant
- add async indexing workers for large upload queues
- use hybrid retrieval combining BM25 keyword search with vector search
- add TTL/retention policies for old embeddings

## Security discussion

- Input query strings are accepted as plain text and embedded without sanitization beyond trimming.
- The API does not execute model-generated code or external commands.
- The vector database is local and file-based, so access control is inherited from filesystem permissions.
- For production deployment, protect the API behind authentication, add request limits, and avoid exposing raw debug logs in public endpoints.

## 20 interview questions

1. What is the difference between keyword search and semantic search?
2. Why use embeddings for video retrieval?
3. How does a vector database differ from a relational database?
4. What is cosine similarity and why is it useful?
5. What is the role of the embedding model in retrieval quality?
6. How do you handle sparse scene detection results?
7. What are the trade-offs between exact and approximate nearest-neighbor search?
8. Why use a persistent ChromaDB collection?
9. How would you tune `top_k` for different UX requirements?
10. What metrics would you use to evaluate retrieval quality?
11. How would you handle multilingual videos?
12. How would you support large-scale indexed video libraries?
13. What is the advantage of indexing event summaries instead of raw transcripts only?
14. What happens when a query is too broad or ambiguous?
15. How would you re-rank results with metadata or recency filters?
16. What is the cost of embedding generation at runtime?
17. How would you scale this to millions of events?
18. What is a fallback strategy when embeddings are unavailable?
19. How would you add analytics for query success and click-through rates?
20. How would you make this production-ready for enterprise workloads?

## Remaining roadmap

- Add automated quality evaluation for semantic retrieval benchmarks.
- Integrate hybrid lexical + semantic ranking for better recall.
- Add multi-video search and metadata facets.
- Support user-authored saved searches and ranking feedback.
- Expose search results through a richer frontend experience.

## Resume bullet points

- Built a semantic video search engine using SentenceTransformers and ChromaDB.
- Designed and deployed a persistent vector store for scene and event retrieval.
- Integrated embedding generation into the existing event pipeline for natural-language queries.
- Created search APIs that return ranked, top-k video event matches.
- Added unit tests covering embeddings, vector persistence, and retrieval endpoints.

## Production recommendations

- Set `embedding_model` and `device` via environment configuration rather than hard-coded values.
- Add caching and batching for large batches of events to reduce GPU/CPU overhead.
- Monitor embedding model load times and retrieval latency to detect degradation.
- Add a retry layer and health checks for ChromaDB and model dependencies.
- Use authentication, rate limiting, and logging around `/search` in production.
- Consider hybrid search with BM25 for higher recall and improved precision on domain-specific queries.

## Validation summary

The project was validated with:

- full backend test suite: 20 passed
- real sample-video pipeline execution: successful
- vector database insertion: successful
- semantic retrieval on a sample query: successful

This milestone is complete and the system is ready for further expansion into a stronger production semantic video search service.
