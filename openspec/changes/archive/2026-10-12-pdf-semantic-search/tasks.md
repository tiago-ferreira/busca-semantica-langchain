# Tasks

## 1. Project and runtime configuration

- [x] 1.1 Add Python dependencies, shared environment loading/validation, `.env.example`, and ignore rules for local secrets; verify required-setting validation with `python -m pytest tests/test_config.py`.
- [x] 1.2 Add the persistent pgVector Docker Compose service and document virtualenv creation, current OpenAI model selection, environment setup, database startup, and shutdown in `README.md`; verify with `docker compose config`.

## 2. PDF ingestion

- [x] 2.1 Implement PDF loading and 1,000-character/150-overlap chunking in `src/ingest.py`; add tests for chunk sizes, overlap, and missing/unreadable input, and verify with `python -m pytest tests/test_ingest.py`.
- [x] 2.2 Persist chunks using the configured pgVector collection and replace its current vectors on reingestion without changing collection dimensions; add mocked-storage tests for replacement and dimension errors, document collection/volume reset steps in `README.md`, and verify with `python -m pytest tests/test_ingest.py`.

## 3. Contextual search and CLI

- [x] 3.1 Implement top-10 vector retrieval and the required context-only OpenAI prompt in `src/search.py`; add tests for retrieval limit, context construction, and the exact unsupported-answer fallback using mocked models, and verify with `python -m pytest tests/test_search.py`.
- [x] 3.2 Implement the Portuguese terminal question/answer flow in `src/chat.py`; add CLI tests for question/response display and configuration or database errors, document chat usage in `README.md`, and verify with `python -m pytest tests/test_chat.py`.

## 4. Local workflow integration

- [ ] 4.1 Add a generated-PDF integration test that exercises ingestion, persistence, and search against the Compose pgVector service with mocked OpenAI calls; verify with `docker compose up -d && python -m pytest tests/integration`.
- [ ] 4.2 Verify the documented start-database, ingest, and chat sequence against a user-supplied root `document.pdf`, and confirm `python -m pytest` passes.
