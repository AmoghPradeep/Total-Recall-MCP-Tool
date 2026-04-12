## ADDED Requirements

### Requirement: Watch audio and PDF drop folders
The system SHALL run a Windows-startup background process that watches configured audio and PDF folders for new supported files.

#### Scenario: Detect new audio file
- **WHEN** a new `.m4a` file is written to the configured audio folder
- **THEN** the system enqueues an audio ingestion job exactly once for that file version

#### Scenario: Detect new PDF file
- **WHEN** a new `.pdf` file is written to the configured PDF folder
- **THEN** the system enqueues a PDF ingestion job exactly once for that file version

### Requirement: Process audio files into normalized Obsidian markdown
The system SHALL transcribe each queued audio file using a transformer-based ASR model, normalize the transcript into Obsidian markdown via an Ollama-compatible LLM, and write the markdown document to the vault.

#### Scenario: Successful audio ingestion
- **WHEN** an audio job starts for a stable `.m4a` file
- **THEN** the system loads ASR model, transcribes audio, ejects ASR model, loads normalization LLM, generates normalized markdown, writes markdown to vault, and ejects normalization model

#### Scenario: Audio ingestion failure cleanup
- **WHEN** audio transcription or normalization fails
- **THEN** the system records an error status for the job and ejects any loaded model before retry or termination

### Requirement: Prefer localhost OpenAI-compatible LLM service before loading local model
The system SHALL check whether an OpenAI-compatible LLM API is available at `http://localhost:1234` before local generation, and only load the local model if the service is unavailable.

#### Scenario: Reuse active local API service
- **WHEN** an LLM-backed generation step starts and `http://localhost:1234` is healthy
- **THEN** the system sends generation requests to that API and does not perform local model load for the step

#### Scenario: Fallback to local model load
- **WHEN** an LLM-backed generation step starts and `http://localhost:1234` is unavailable
- **THEN** the system loads the configured local model, performs generation, and ejects the model after completion

### Requirement: Process PDFs into normalized markdown with summary
The system SHALL convert each queued PDF into normalized markdown that includes extracted content and a summary, and persist it to the vault.

#### Scenario: Successful PDF ingestion
- **WHEN** a PDF job starts for a stable `.pdf` file
- **THEN** the system converts PDF pages to JPG images, performs page-level multimodal extraction/normalization, reduces page summaries into a document summary, writes markdown to vault, and ejects the model when locally loaded

#### Scenario: Low-confidence handwritten extraction
- **WHEN** PDF handwritten content cannot be reliably parsed
- **THEN** the system still writes markdown with available extracted text and marks extraction confidence metadata

### Requirement: Generate and reuse domain tags during markdown creation
The system SHALL assign knowledge-domain tags during markdown generation, prefer existing tags from a persisted tag catalog, and allow creating a new tag only when no existing tag is suitable.

#### Scenario: Reuse existing tags
- **WHEN** markdown is generated and at least one catalog tag is relevant
- **THEN** the system outputs existing catalog tags in the markdown frontmatter and stores the tag associations in the database

#### Scenario: Create new tag only if necessary
- **WHEN** markdown is generated and no catalog tag is relevant above configured threshold
- **THEN** the system allows the LLM to propose a new domain tag and persists it to the tag catalog for reuse

### Requirement: Index generated markdown into vector store
The system SHALL chunk every generated markdown document, create embeddings, and upsert chunks with source metadata into a vector database.

#### Scenario: Index new generated markdown
- **WHEN** markdown generation succeeds for an audio or PDF source
- **THEN** the system chunks the markdown, computes embeddings, and stores chunk vectors linked to document metadata and source path

#### Scenario: Prevent duplicate indexing for same file version
- **WHEN** duplicate watcher events occur for an unchanged source file version
- **THEN** the system avoids creating duplicate chunk vectors for that source version
