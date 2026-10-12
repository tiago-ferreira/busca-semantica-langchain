# Spec Delta

## Purpose

Permite indexar o conteúdo de um PDF em um repositório vetorial local e consultar esse conteúdo por perguntas em uma CLI. As respostas devem estar fundamentadas somente em trechos recuperados do documento.

## ADDED Requirements

### Requirement: Ingest PDF content
The system SHALL read the PDF at the project root and prepare its text for semantic retrieval.

#### Scenario: Split a readable PDF
- **WHEN** the user runs ingestion with a readable `document.pdf`
- **THEN** the system divides the extracted text into chunks of 1,000 characters with 150 characters of overlap

#### Scenario: PDF is missing or unreadable
- **WHEN** ingestion cannot find or read `document.pdf`
- **THEN** the system reports the input error and does not report ingestion as successful

### Requirement: Persist document vectors
The system SHALL persist an embedding for each document chunk in PostgreSQL with pgVector so that a later search process can retrieve it.

#### Scenario: Store chunks for semantic search
- **WHEN** ingestion completes successfully
- **THEN** each chunk and its embedding are available in the configured vector collection

#### Scenario: Reingest the current PDF
- **WHEN** the user runs ingestion again
- **THEN** the collection contains chunks from the current `document.pdf` rather than appending duplicate or stale chunks

#### Scenario: Embedding dimensions do not match an existing collection
- **WHEN** ingestion uses an embedding model whose vector dimension is incompatible with the existing collection
- **THEN** the system reports the incompatibility and the project instructions explain that the collection or database volume must be cleared before re-ingestion

### Requirement: Retrieve relevant document context
The system SHALL accept a user's question and retrieve up to 10 semantically relevant document chunks from the configured vector collection.

#### Scenario: Search an indexed document
- **WHEN** the user submits a question after successful ingestion
- **THEN** the system embeds the question and supplies at most the 10 most relevant stored chunks as context for answer generation

#### Scenario: No indexed content is available
- **WHEN** the configured collection has no chunks available for retrieval
- **THEN** the CLI returns `Não tenho informações necessárias para responder sua pergunta.`

### Requirement: Answer only from retrieved context
The system SHALL answer questions using only information explicitly present in the retrieved context and SHALL use the exact fallback response `Não tenho informações necessárias para responder sua pergunta.` when the context does not explicitly contain the answer.

#### Scenario: Answer supported by the PDF
- **WHEN** retrieved context explicitly contains the information requested
- **THEN** the CLI returns an answer based only on that context

#### Scenario: Answer is not supported by the PDF
- **WHEN** retrieved context does not explicitly contain the requested information
- **THEN** the CLI returns `Não tenho informações necessárias para responder sua pergunta.`

### Requirement: Interact through the terminal
The system SHALL let the user submit questions in the terminal and display each resulting answer there.

#### Scenario: Submit a question in the CLI
- **WHEN** the user enters a question in the chat CLI
- **THEN** the CLI displays the question and its response in Portuguese

### Requirement: Configure OpenAI and database access
The system SHALL obtain OpenAI credentials, model settings, and PostgreSQL connection settings from environment configuration and SHALL provide a safe example configuration without real credentials.

#### Scenario: Run with documented configuration
- **WHEN** the user supplies the required environment values from the documented example
- **THEN** ingestion and question answering use the configured OpenAI models and PostgreSQL database

#### Scenario: Required configuration is missing
- **WHEN** a required credential or connection setting is absent
- **THEN** the relevant command reports which configuration is missing and does not claim success

### Requirement: Run the application locally
The project SHALL provide instructions to start the pgVector-enabled database with Docker Compose, ingest the root PDF, and launch the interactive CLI.

#### Scenario: Follow the documented local workflow
- **WHEN** the user follows the project instructions with Docker and the required environment configured
- **THEN** the user can start the database, run ingestion, and start the CLI in that order
