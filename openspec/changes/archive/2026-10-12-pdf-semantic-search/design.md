# Design

## Context

See `proposal.md` for motivation and `specs/pdf-semantic-search/spec.md` for the behavior contract. The repository currently has OpenSpec configuration but no application source, dependency manifest, PDF, or runtime documentation. The implementation is a single-document local workflow: the user supplies `document.pdf`, runs Python commands on the host, and runs PostgreSQL with pgVector in Docker Compose.

## Goals / Non-Goals

**Goals:**
- Keep ingestion, retrieval, and the terminal chat as separate entry points matching the required `src/ingest.py`, `src/search.py`, and `src/chat.py` structure.
- Share database, collection, and OpenAI model settings so ingestion and search always use compatible configuration.
- Make ingestion repeatable for the single current PDF without accumulating stale or duplicate chunks.

**Non-Goals:**
- Supporting multiple PDFs, multiple providers, a web interface, or hosted deployment.
- Automatically changing embedding models or migrating an existing collection to a different vector dimension.

## Decisions

### Use OpenAI models configured through environment variables

Use LangChain's OpenAI integrations for both embeddings and chat completion. Keep the API key and model identifiers out of source control, load local settings from `.env`, and provide placeholders in `.env.example`. Define shared settings such as `OPENAI_API_KEY`, `OPENAI_EMBEDDING_MODEL`, `OPENAI_CHAT_MODEL`, `DATABASE_URL`, and `PGVECTOR_COLLECTION` in a small `src/config.py` module. Verify currently available, low-cost model identifiers against OpenAI's official documentation during implementation instead of baking changeable model names into code.

Alternative considered: Gemini. It is not included because the user selected OpenAI for this version.

### Use one shared pgVector collection for the root PDF

Run PostgreSQL with a pgVector-enabled Docker image and persistent Docker volume. Use `langchain_postgres.PGVector` with the same collection name and embedding configuration in ingestion and search. Load the root PDF with `PyPDFLoader` and split its extracted documents with `RecursiveCharacterTextSplitter` configured to `chunk_size=1000` and `chunk_overlap=150`.

On ingestion, clear the existing vectors in the configured collection and write the chunks from the current PDF; do not append another copy. Preserve the collection's embedding dimension. If the embedding model changes dimension, fail with an actionable error and document manual collection or volume removal followed by a fresh ingestion.

Alternative considered: creating a new collection on every ingestion. That would leave obsolete collections and make model-dimension changes appear to succeed without the explicit reset required by the challenge.

### Keep retrieval and response construction in the search module

`src/search.py` owns vector retrieval and prompt-based answer generation so `src/chat.py` only handles terminal input/output. Retrieve at most 10 chunks, concatenate their text as `CONTEXTO`, and pass that plus the user's question to the configured OpenAI chat model. Use the prompt contract supplied for this challenge:

```text
CONTEXTO:
{resultados concatenados do banco de dados}

REGRAS:
- Responda somente com base no CONTEXTO.
- Se a informação não estiver explicitamente no CONTEXTO, responda:
  "Não tenho informações necessárias para responder sua pergunta."
- Nunca invente ou use conhecimento externo.
- Nunca produza opiniões ou interpretações além do que está escrito.

EXEMPLOS DE PERGUNTAS FORA DO CONTEXTO:
Pergunta: "Qual é a capital da França?"
Resposta: "Não tenho informações necessárias para responder sua pergunta."

Pergunta: "Quantos clientes temos em 2024?"
Resposta: "Não tenho informações necessárias para responder sua pergunta."

Pergunta: "Você acha isso bom ou ruim?"
Resposta: "Não tenho informações necessárias para responder sua pergunta."

PERGUNTA DO USUÁRIO:
{pergunta do usuário}

RESPONDA A "PERGUNTA DO USUÁRIO"
```

When retrieval produces no chunks, return the required fallback directly rather than asking the LLM to answer without evidence. The chat CLI displays the question and response in Portuguese, using the `PERGUNTA` and `RESPOSTA` labels from the example.

Alternative considered: a generic conversational chain with memory. It is excluded because it could introduce information beyond the indexed PDF.

### Run only the database in Docker Compose

Use Docker Compose for the pgVector database and run the Python scripts in the user's virtual environment, following the requested local workflow. Document dependency setup, environment configuration, database startup, ingestion, and chat launch in `README.md`.

## Risks / Trade-offs

- [An OpenAI model may still generate unsupported text despite prompt constraints] → Use only retrieved chunks as context, retain the explicit fallback and refusal examples, and test both supported and unsupported questions with a controllable/mock chat model.
- [Reingestion can leave the index empty or incomplete if storage fails after clearing old vectors] → Validate the PDF, required settings, and embedding results before replacing stored rows; report any failed write as an ingestion failure and document that ingestion can be rerun.
- [Changing the embedding model may change vector dimensions] → Keep collection dimensions stable, report dimension errors clearly, and document the required manual collection/volume reset before re-ingestion with the new model.
- [OpenAI credentials and API availability are external runtime dependencies] → Fail with explicit configuration/provider errors; never include credentials in `.env.example` or logs.

## Migration Plan

1. Create and activate a Python virtual environment, install `requirements.txt`, and copy `.env.example` to `.env` with the required OpenAI and database settings.
2. Start PostgreSQL with `docker compose up -d` and place the input document at the project root as `document.pdf`.
3. Run `python src/ingest.py`, then `python src/chat.py`.
4. To switch to an embedding model with a different dimension, stop using the existing collection, delete the collection or Docker volume as documented, and ingest the PDF again.

Rollback consists of stopping the Compose service and removing its volume if the local database state must be discarded; there is no existing application data to migrate.
