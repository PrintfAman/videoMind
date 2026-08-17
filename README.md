# VideoMind AI

VideoMind AI is an event-aware multimodal retrieval engine for long-form videos. This repository contains the Sprint 0 production-ready foundation: a FastAPI backend scaffold, configuration, logging, and basic project structure. AI functionality will be added in later sprints.

## Vision

Enable users to upload long-form videos, extract audio and visual events, build event-driven representations, generate embeddings, store them in a vector database, and answer natural-language queries with timestamps and evidence.

## Folder structure

- backend/ – FastAPI backend (primary deliverable for Sprint 0)
- frontend/ – React + Vite frontend skeleton (initialized)
- docs/ – Documentation and design artifacts
- research/ – Research notes and references
- datasets/ – Sample datasets and ingestion notes
- scripts/ – Utility scripts for maintenance or deployment

See the `backend` README for backend-specific run instructions.

## Tech stack

- Python 3.11+
- FastAPI
- Uvicorn
- Pydantic v2 (pydantic-settings)
- React + Vite (frontend initialized)

## Getting started (backend)

1. Create and activate a Python 3.11+ virtual environment.
2. Install dependencies:

```bash
cd backend
python -m pip install -r requirements.txt  # or install from pyproject.toml
```

3. Run the server:

```bash
cd backend
uvicorn app.main:app --reload
```

4. Health check:

```bash
# in another terminal
curl http://127.0.0.1:8001/health
```

## Roadmap (selected items)

- Sprint 0: Project foundation, health endpoint, config, logging (this sprint).
- Sprint 1: Video ingestion pipeline, audio extraction, frame sampling.
- Sprint 2: Event detection and timestamping pipeline.
- Sprint 3: Embeddings generation and vector store integration.

## Contributing

Please follow the repository's Python style and testing conventions. Open issues for new features or bugs.
