# Phase 6: RAG Pipeline Step-by-Step

## Goal

Build the RAG pipeline slowly and deliberately so each step reinforces the concept behind it.

RAG means Retrieval-Augmented Generation:

1. Store useful knowledge outside the model.
2. Retrieve the most relevant pieces for a user question.
3. Give those pieces to the model as grounded context.
4. Ask the model to answer using that context.

This phase should be built one step at a time. Do not move to the next step until the current step is working and understood.

## Current Inputs

The project already has:

- Product catalog: `data/catalog/products.json`
- Category definitions: `data/catalog/categories.json`
- Customer review samples: `data/reviews/product_reviews.json`
- Product support docs: `data/knowledge_base/products/<product_id>/*.md`
- Store policy docs: `data/knowledge_base/store_policies/*.md`
- Synthetic support tickets: `data/support/tickets.json`

## Step 1: Document Inventory

### Concept

Before retrieval, we need to know what knowledge exists. RAG quality depends heavily on document quality and coverage.

### Build

Create a script that lists all available knowledge sources:

- Product docs
- Store policies
- Reviews
- Support tickets
- Catalog records

### Verify

Print counts by source type:

- Number of product docs
- Number of policy docs
- Number of products with reviews
- Number of support tickets

### Learn

Understand the difference between:

- Structured data, like JSON catalog records
- Unstructured text, like markdown support docs
- Semi-structured data, like support tickets

## Step 2: Load Documents

### Concept

Document loading turns files into a common in-memory format. Each loaded document should have:

- `page_content`: the searchable text
- `metadata`: information used for filtering, citations, and debugging

### Build

Create a loader that reads:

- Markdown files from `data/knowledge_base/`
- Review JSON from `data/reviews/product_reviews.json`
- Ticket JSON from `data/support/tickets.json`
- Optional catalog summaries from `data/catalog/products.json`

### Verify

Print a few loaded documents with metadata.

### Learn

Understand why metadata matters:

- `product_id`
- `doc_type`
- `category`
- `subcategory`
- `source_path`

Metadata helps retrieval and lets the chat agent cite sources later.

## Step 3: Normalize Text

### Concept

Different source files have different shapes. RAG works best when each document has clear, readable text.

### Build

Convert each source into natural-language text:

- Product docs can use markdown content directly.
- Reviews should become review snippets with rating and verified-purchase information.
- Tickets should become issue summaries.
- Catalog records should become short product profiles.

### Verify

Inspect examples from each source type.

### Learn

Understand that RAG does not retrieve JSON fields magically. It retrieves text representations plus metadata.

## Step 4: Chunk Documents

### Concept

Chunking splits long documents into smaller pieces. Retrieval usually works better with chunks than with entire large documents.

Chunks should be:

- Big enough to contain useful context
- Small enough to retrieve precisely

### Build

Use LangChain text splitters to chunk loaded documents.

Initial settings to try:

- Chunk size: 700-1000 characters
- Chunk overlap: 100-150 characters

### Verify

Print:

- Number of original documents
- Number of chunks
- Example chunks
- Metadata preserved on chunks

### Learn

Understand chunking tradeoffs:

- Chunks too small lose context.
- Chunks too large retrieve irrelevant text.
- Overlap helps preserve meaning across boundaries.

## Step 5: Preview Embeddings In Memory

### Concept

Embeddings convert text into vectors. Similar meanings should have similar vectors.

This step is for learning and inspection. It embeds a small sample of chunks in memory so you can inspect vector shape, provider metadata, and sample values. These preview vectors are not saved to Chroma and are lost when the Python process exits.

### Build

Use the embedding provider abstraction through LangChain/OpenAI-compatible clients.

Likely dependency areas:

- `langchain-openai`
- `truststore`

Environment variables, depending on provider:

```text
OPENAI_API_KEY=
NEBIUS_API_KEY=
NEBIUS_BASE_URL=
```

Current implementation:

- `rag_pipeline/embeddings.py`
- `rag_pipeline/preview_embeddings.py`
- Default provider: OpenAI through LangChain `OpenAIEmbeddings`
- Model: `text-embedding-3-small`
- Offline fallback provider: local hashing embeddings for pipeline-only tests
- Nebius provider: `Qwen/Qwen3-Embedding-8B` through an OpenAI-compatible API
- Current preview script default: `nebius`, matching the working project provider
- TLS support: `truststore.inject_into_ssl()`
- Tokenizer precheck disabled with `check_embedding_ctx_length=False` because chunks are already small

### Verify

Embed a few chunks and confirm vectors are returned.

```powershell
cd backend
uv run python ../rag_pipeline/preview_embeddings.py --provider nebius
```

Use `--limit 0` only when you intentionally want to embed all chunks in memory:

```powershell
uv run python ../rag_pipeline/preview_embeddings.py --provider nebius --limit 0
```

Current execution status:

- The OpenAI API call path is wired correctly.
- The request reached OpenAI after `truststore` was added.
- OpenAI embedding requests return `429 insufficient_quota`.
- Nebius embedding requests work and are the current working semantic provider.

### Learn

Understand that embeddings are not chat completions. They are numerical representations used for similarity search.

Understand the difference between preview embeddings and persisted vector-store embeddings:

- Step 5: embeds a small sample in memory for inspection.
- Step 6: runs full embedding, indexing, and Chroma storage.

## Step 6: Full Embedding / Indexing / Chroma Store

### Concept

A vector store saves embedded chunks and lets us search them by semantic similarity.

We are using Chroma first because it is local and easy to inspect. The full Chroma build embeds every chunk, indexes the vectors, stores vectors and metadata, and persists the collection under `data/vector_store/chroma/`.

### Build

Create a Chroma database from the chunks.

Suggested path:

```powershell
data/vector_store/chroma/
```

Command:

```powershell
cd backend
uv run python ../rag_pipeline/build_vector_store.py --provider nebius
```

### Verify

Print:

- Number of chunks stored
- Collection name
- Persisted database path

### Learn

Understand the difference between:

- The source documents
- The chunks
- Preview embeddings in memory
- Persisted Chroma vectors
- The vector database index

## Step 7: Basic Retrieval

### Concept

Retrieval finds the most relevant chunks for a question.

At this step, we are not generating answers yet. We are only checking whether the right context comes back.

The provider used for retrieval must match the provider used to build the persisted Chroma collection. The current persisted store uses `nebius`.

### Build

Create a retrieval script that accepts test questions.

Example questions:

- "What is the return policy?"
- "How long does shipping take?"
- "How do I troubleshoot a Bluetooth speaker?"
- "Is this MacBook case compatible with my model?"
- "What do customers say about the Garmin Vivofit band?"

### Verify

Print:

- Score if available
- Source path
- Document type
- Product id if available
- Text snippet

### Learn

Understand retrieval quality before adding generation. If retrieval is bad, the final answer will be bad.

## Step 8: Grounded Answer Prototype

### Concept

Only after retrieval works should we generate answers.

The answer should use retrieved context and avoid making unsupported claims.

### Build

Create a grounded answer prototype:

- User question
- Retrieved context
- Extracted context snippets
- Numbered citations back to source metadata

### Verify

Ask a few questions and inspect:

- Does the answer use retrieved context?
- Does it cite sources?
- Does it refuse or ask for clarification when context is insufficient?

### Learn

Understand that generation is the final layer. RAG is mostly about good documents, metadata, chunking, embeddings, and retrieval.

Current implementation:

- `rag_pipeline/answer_generation.py`
- `rag_pipeline/preview_answers.py`
- Deterministic extractive answers for now, so answer previews work without chat-completion quota.
- Citations include labels, source paths, document types, product IDs when available, and chunk IDs.

Verify with:

```powershell
cd backend
uv run python ../rag_pipeline/preview_answers.py --provider nebius
```

## Later Retrieval Improvements: Metadata Filtering

### Concept

Metadata filters let us narrow retrieval to relevant subsets.

For example:

- Product-specific questions should prefer that product's docs.
- Policy questions should include store policy docs.
- Ticket questions should include support tickets.

### Build

Add optional filters:

- `product_id`
- `doc_type`
- `category`

### Verify

Compare retrieval with and without filters.

### Learn

Understand when semantic search alone is enough and when metadata constraints improve precision.

## Later Retrieval Improvements: Retrieval Evaluation

### Concept

Before connecting to chat, create a small evaluation set. This helps detect when changes improve or hurt retrieval.

### Build

Create 10-15 test questions with expected source types.

Example expected source types:

- `store_policy`
- `product_faq`
- `setup`
- `troubleshooting`
- `compatibility`
- `review_summary`
- `support_ticket`

### Verify

For each question, record whether the top results include the expected source type.

### Learn

Understand that RAG systems need evaluation, even simple evaluation, because retrieval quality is not obvious from code alone.

## Suggested Implementation Order

1. `rag_pipeline/inspect_knowledge_sources.py`
2. `rag_pipeline/document_loader.py`
3. `rag_pipeline/text_normalizer.py`
4. `rag_pipeline/chunking.py`
5. `rag_pipeline/embeddings.py`
6. `rag_pipeline/build_vector_store.py`
7. `rag_pipeline/preview_retrieval.py`
8. `rag_pipeline/answer_generation.py`
9. `rag_pipeline/preview_answers.py`

## Stop Points

Pause after each step and answer:

- What concept did this step demonstrate?
- What code did we add?
- What output proves it works?
- What could go wrong in a real support app?

## Current Resume Point

Phase 6 is complete. It has working document loading, chunking, embedding preview, full embedding/indexing/Chroma storage, hybrid retrieval, deterministic cited answer previews, and a backend `/chat` endpoint.

Current state:

```text
Loaded/normalized documents: 479
Chunks: 907
Vector store: Chroma
Embedding provider used for current Chroma index: nebius
Nebius embedding model: Qwen/Qwen3-Embedding-8B
Current answer layer: deterministic extractive answers with citations
OpenAI blocker: embedding requests return 429 insufficient_quota
```

Verification command:

```powershell
cd backend
uv run python ../rag_pipeline/preview_answers.py --provider nebius
```

The FastAPI endpoint now exists:

```text
POST /chat
```

Next action: connect the frontend support chat UI to this endpoint.
