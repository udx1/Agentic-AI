# Phase 6 RAG Pipeline Tasks

## Goal

Build the local retrieval-augmented generation pipeline: load documents, normalize text, chunk documents, create embeddings, persist vectors in Chroma, retrieve relevant context, generate cited answers, and expose the baseline `/chat` endpoint.

Status: complete.

## Task List

### 1. Knowledge Source Inventory

- [x] Add `rag_pipeline/inspect_knowledge_sources.py`.
- [x] Count catalog products.
- [x] Count categories.
- [x] Count review samples.
- [x] Count knowledge-base markdown documents.
- [x] Count support tickets.

### 2. Document Loading

- [x] Add `rag_pipeline/document_loader.py`.
- [x] Load markdown knowledge-base documents.
- [x] Load product catalog records.
- [x] Load category records.
- [x] Load customer review samples.
- [x] Load support tickets.
- [x] Preserve metadata for citations and filtering.

### 3. Text Normalization

- [x] Add `rag_pipeline/text_normalizer.py`.
- [x] Convert structured records into searchable natural-language text.
- [x] Compact whitespace.
- [x] Preserve metadata.
- [x] Mark normalized documents.

### 4. Chunking

- [x] Add `rag_pipeline/chunking.py`.
- [x] Use LangChain `RecursiveCharacterTextSplitter`.
- [x] Use chunk size 900.
- [x] Use chunk overlap 150.
- [x] Preserve metadata on chunks.
- [x] Generate globally unique chunk IDs.
- [x] Add `rag_pipeline/preview_chunks.py`.

### 5. Embedding Providers

- [x] Add `rag_pipeline/embeddings.py`.
- [x] Add OpenAI embedding provider through LangChain.
- [x] Add local deterministic hashing provider.
- [x] Add Nebius embedding provider through an OpenAI-compatible client.
- [x] Add `truststore` for Windows/system certificate support.
- [x] Disable tokenizer context precheck to avoid unnecessary tokenizer downloads.
- [x] Add `rag_pipeline/preview_embeddings.py`.
- [x] Add Nebius access and embedding check scripts.

### 6. Vector Store

- [x] Add `rag_pipeline/vector_store.py`.
- [x] Add Chroma local vector store support.
- [x] Persist Chroma under `data/vector_store/chroma`.
- [x] Add `rag_pipeline/build_vector_store.py`.
- [x] Build the full Chroma collection with Nebius embeddings.
- [x] Confirm 907 chunks are stored.

### 7. Retrieval

- [x] Add `rag_pipeline/retrieval.py`.
- [x] Load the provider-matched Chroma collection.
- [x] Retrieve vector candidates.
- [x] Add lexical overlap scoring.
- [x] Merge lexical matches for backup relevance.
- [x] Rerank retrieval results.
- [x] Add `rag_pipeline/preview_retrieval.py`.

### 8. Cited Answer Generation

- [x] Add `rag_pipeline/answer_generation.py`.
- [x] Select strongest retrieved contexts.
- [x] Generate deterministic extractive answer text.
- [x] Add numbered citations.
- [x] Include source label, source path, document type, product ID, and chunk ID.
- [x] Ask for clarification when retrieved context is weak.
- [x] Add `rag_pipeline/preview_answers.py`.

### 9. Backend Chat Baseline

- [x] Add `POST /chat` in `backend/app/main.py`.
- [x] Accept question and provider.
- [x] Return answer, citations, and retrieved context.
- [x] Keep the response usable by the future frontend chat UI.
- [x] Verify with FastAPI `TestClient`.

### 10. Notebook and Documentation

- [x] Add `rag_pipeline/rag_pipeline_walkthrough.ipynb`.
- [x] Explain each RAG concept step by step.
- [x] Add notebook examples for loading, chunking, embeddings, retrieval, answers, and backend chat.
- [x] Update `PROJECT_STATUS.md`.
- [x] Update `docs/learning-notes.md`.

### 11. Provider Status

- [x] Confirm OpenAI model listing works with the configured key.
- [x] Record OpenAI embedding quota blocker: `429 insufficient_quota`.
- [x] Confirm Nebius embeddings work.
- [x] Record Nebius model and embedding dimension.
- [x] Set Nebius as the current working retrieval provider.
- [x] Keep hashing as a local backup provider.

## Verification

- [x] Document inventory works.
- [x] 479 normalized documents load.
- [x] 907 unique chunks generate.
- [x] Nebius Chroma build completes.
- [x] Retrieval previews return relevant documents.
- [x] Answer previews return cited answers.
- [x] Backend `/chat` returns answer, citations, and retrieved context.

