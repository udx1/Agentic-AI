# Project Status

## Current Goal

Build a local-first ecommerce site using a 50-product subset from the UCSD Amazon Electronics dataset, then extend it with a RAG-based customer support chat agent.

## Current Phase

Phase 6 RAG Pipeline is complete.

Phase 7 Support Chat Agent is complete:

- `POST /chat` exists in FastAPI.
- The endpoint is now backed by a LangGraph support-agent workflow.
- The workflow classifies intent, plans retrieval, retrieves context, assesses context sufficiency, answers with citations, asks for clarification, or prepares escalation.
- The endpoint keeps the existing public response shape: `question`, `answer`, `provider`, `citations`, and `retrievedContext`.
- The first LangGraph implementation remains deterministic and works without an LLM chat-completion call.

Phase 8 Chat UI / frontend support chat integration is complete:

```text
- The React frontend has a floating support chat panel available from the header.
- The panel calls the LangGraph-backed backend POST /chat endpoint with provider nebius.
- Assistant answers render with citations, retrieved source snippets, loading and error states.
- Product detail pages offer product-aware starter prompts.
- Developer trace mode is hidden by default and unlocked with ?eval=z.
- Citations, retrieved context, and debug traces are shown only in eval/developer mode, not normal support mode.
- Eval/developer evidence is enabled by default when the frontend URL includes `?eval=z`.
- Frontend evidence rendering now matches the backend API field names: label, docType, and snippet.
- Catalog availability questions such as `Is IBM Laptop available?` are answered from `data/catalog/products.json`, with related catalog matches when an exact brand/product is not present.
```

Current active phase:

```text
Phase 9: Ticket persistence and support workflow extensions
```

Current blocker for OpenAI embeddings:

```text
The current OPENAI_API_KEY can list available models, including text-embedding-3-small,
but actual embedding requests return 429 insufficient_quota. Add billing/credits or
switch to an OpenAI key/project with usable API quota before running the OpenAI
embedding pass.
```

Current working provider:

```text
Use Chroma as the local vector database. The current Chroma collection was built
with Nebius embeddings. The local deterministic hashing provider remains available,
but Chroma must be rebuilt with `--provider hashing` before retrieval or answer
previews can use hashing embeddings.
```

Chat-completion provider:

```text
Use Claude through Anthropic for natural final support answers. Keep Nebius as the
current embedding provider for retrieval. Claude is called after retrieval and
context sufficiency pass, preserving the existing /chat response shape and keeping
deterministic answer formatting as a fallback.
```

Nebius status:

```text
Nebius API access works through backend/.env. The available embedding model
Qwen/Qwen3-Embedding-8B returns 4096-dimensional embeddings. The full 907-chunk
Chroma build completed successfully in about 19 minutes.
```

## Key Decisions

- Use the Electronics category.
- Start with a clean subset of 50 products.
- Build locally first.
- Use the ecommerce site as the baseline UI.
- Add a support chat agent later using a RAG pipeline.
- Build the RAG pipeline with LangChain.
- Build the support agent workflow with LangGraph.
- Use Chroma first for local vector search.
- Keep Pinecone as a later cloud vector database option.
- Since the dataset does not include manuals, FAQs, or support tickets, create a synthetic support knowledge base tied to the selected products.
- Bring in 5-6 clean real customer reviews per selected product during Phase 5, stored separately from the product catalog.

## Planned Stack

- Frontend: React/Vite
- Backend: FastAPI managed with `uv`
- Data: local JSON and markdown files
- RAG framework: LangChain
- Agent workflow framework: LangGraph
- Local vector store: Chroma
- Cloud vector store option: Pinecone
- Models: Nebius embeddings currently; Claude chat-completion answer generation; OpenAI remains optional after quota is available

## Phase 0 Completed Setup

- Created the initial folder structure.
- Added build and learning docs.
- Initialized `backend/` as a `uv` project.
- Added FastAPI and Uvicorn backend dependencies.
- Added a starter FastAPI app with `GET /health`.
- Kept the frontend plan as React/Vite for Phase 2.

## Phase 1 Completed Data Layer

- Used the UCSD/McAuley Lab Amazon Reviews 2023 Electronics metadata.
- Added `backend/scripts/build_catalog.py`.
- Added `backend/scripts/validate_catalog.py`.
- Generated `data/catalog/products.json` with 50 normalized products.
- Saved selected source records to `data/raw/electronics_sample.jsonl`.
- Documented the source in `docs/data-source.md`.
- Documented the normalized schema in `docs/catalog-schema.md`.

## Phase 2 Completed UI Baseline

- Created the React/Vite frontend project in `frontend/`.
- Initially used local frontend catalog data for the UI baseline.
- Built a product listing page.
- Built reusable product cards.
- Built a product detail view using hash-based navigation.
- Added responsive CSS for desktop and mobile layouts.
- Verified `npm run build` succeeds.
- Started the local dev server at `http://127.0.0.1:5173/`.

## Phase 3 Completed Frontend Logic

- Added search across title, brand, category, subcategory, and description.
- Kept department navigation as category filtering.
- Added sorting by featured order, price, rating, and review count.
- Added a local cart panel.
- Added product card and product detail add-to-cart actions.
- Added cart quantity increase, decrease, direct edit, and remove behavior.
- Verified `npm run build` succeeds.

## Phase 4 Completed Backend API

- Added FastAPI product and category response models.
- Added `GET /products`.
- Added `GET /products/{id}`.
- Added `GET /categories`.
- Added CORS for the local Vite frontend.
- Served catalog data from `data/catalog/products.json` and `data/catalog/categories.json`.
- Updated the frontend to fetch products and categories from FastAPI.
- Removed duplicate frontend catalog JSON files.
- Started the backend API at `http://127.0.0.1:8000/`.

## Phase 5 Completed Local Support Knowledge Base

- Added `backend/scripts/build_reviews.py`.
- Added `backend/scripts/build_support_kb.py`.
- Added `backend/scripts/validate_support_kb.py`.
- Extracted real customer review samples to `data/reviews/product_reviews.json`.
- Saved raw review sample records to `data/raw/electronics_review_sample.jsonl`.
- Generated 250 product KB markdown documents under `data/knowledge_base/products/`.
- Generated 4 store policy markdown documents under `data/knowledge_base/store_policies/`.
- Generated 20 synthetic support tickets in `data/support/tickets.json`.
- Documented the KB in `docs/knowledge-base.md`.
- Validated the KB successfully.

Review extraction coverage:

- Products with at least one clean review sample: 39 of 50
- Products with 6 or more clean review samples: 17 of 50

## Phase 6 RAG Pipeline Completed

Completed:

- Created root-level `rag_pipeline/` folder for RAG-specific code.
- Added `rag_pipeline/rag_pipeline_walkthrough.ipynb` as the step-by-step learning notebook.
- Added source inventory script: `rag_pipeline/inspect_knowledge_sources.py`.
- Added document loader: `rag_pipeline/document_loader.py`.
- Added normalization layer: `rag_pipeline/text_normalizer.py`.
- Added LangChain chunking with `RecursiveCharacterTextSplitter`: `rag_pipeline/chunking.py`.
- Added chunk preview script: `rag_pipeline/preview_chunks.py`.
- Added OpenAI embedding layer with LangChain `OpenAIEmbeddings`: `rag_pipeline/embeddings.py`.
- Added embedding preview script: `rag_pipeline/preview_embeddings.py`; it now defaults to a small in-memory preview sample.
- Added local deterministic hashing embeddings as a backup provider.
- Added Nebius embedding provider support using the OpenAI-compatible API.
- Added Nebius access and embedding check scripts.
- Added Chroma vector store utilities: `rag_pipeline/vector_store.py`.
- Added Chroma build script: `rag_pipeline/build_vector_store.py`.
- Added hybrid retrieval layer: `rag_pipeline/retrieval.py`.
- Added retrieval preview script: `rag_pipeline/preview_retrieval.py`.
- Added deterministic grounded answer formatting: `rag_pipeline/answer_generation.py`.
- Added answer/citation preview script: `rag_pipeline/preview_answers.py`.
- Added backend chat endpoint: `POST /chat`.
- Added `--provider` flags for embedding, vector-store, retrieval preview, and answer preview scripts.
- Split the learning flow into embedding preview, full embedding/indexing/Chroma store, retrieval, and answer preview.
- Set the retrieval default embedding provider to `nebius` to match the current Chroma collection.
- Fixed chunk ID generation so customer reviews and support tickets produce unique Chroma IDs.
- Added `langchain-text-splitters`, `langchain-openai`, `langchain-chroma`, and `truststore` dependencies to the backend uv project.

Verified outputs:

```text
Document inventory:
- Products: 50
- Categories: 5
- Review samples: 145
- KB markdown docs: 254
- Support tickets: 25

Chunking:
- Normalized documents: 479
- Chunks: 907
- Unique chunk IDs: 907
- Chunk size: 900
- Chunk overlap: 150

Local backup embeddings:
- Provider: local-hashing
- Dimension: 384
- Embedded chunks: 907

Nebius embeddings:
- Provider: nebius
- Model: Qwen/Qwen3-Embedding-8B
- Dimension: 4096
- Preview embedding default: first 5 chunks
- Full Chroma build: 907 embedded chunks
- Full Chroma build time: about 19 minutes

Chroma:
- Collection: csagent_support_knowledge
- Persist directory: data/vector_store/chroma
- Stored chunks: 907
- Vector database: Chroma
- Embedding provider used to build current collection: nebius

Retrieval:
- `preview_retrieval.py --provider nebius` returns `returns.md` for a return-policy question.
- It returns troubleshooting documents for a power/troubleshooting question.
- It returns Bluetooth-related product documents for a Bluetooth compatibility question.

Answer generation:
- `preview_answers.py --provider nebius` produces grounded answers with numbered citations.
- Citations include a readable source label, source path, document type, product id when available, and chunk id.
- The current answer layer is deterministic and extractive, so it works without an LLM chat-completion call.

Backend chat:
- `POST /chat` now calls `run_support_agent(...)`.
- Request body: `{ "question": "...", "provider": "nebius" }`.
- Response includes `answer`, `citations`, and `retrievedContext`.
- Verified with FastAPI `TestClient` using a return-policy question.
- Verified from the Python walkthrough notebook using a FastAPI `TestClient`.
```

## Phase 7 Support Chat Agent Completed

Completed:

- Added `langgraph` to the backend dependencies.
- Added `rag_pipeline/support_agent.py`.
- Defined typed agent state, intent labels, escalation metadata, and support-agent result objects.
- Added deterministic intent classification for store policy, product questions, troubleshooting, compatibility, comparison, review summaries, clarification, escalation, and unsupported categories.
- Added product hints from product IDs, titles, brands, categories, and subcategories.
- Added retrieval planning by intent while reusing `retrieve_relevant_chunks(...)`.
- Added context sufficiency checks based on lexical score and expected document-type coverage.
- Refactored answer formatting with `build_cited_answer_from_results(...)` so the graph can reuse retrieved chunks without duplicate retrieval.
- Added clarification behavior for vague or underspecified questions.
- Added escalation preparation for account/order-specific questions, urgent safety-related language, and weak-context handoff.
- Added unsupported-category handling so apparel/clothing questions do not cite electronics policy documents.
- Assembled and compiled a LangGraph workflow with classify, retrieve, assess, answer, clarify, and escalate nodes.
- Added `run_support_agent(question, provider)`.
- Updated `POST /chat` to call `run_support_agent(...)` while preserving the existing API response shape.
- Added repeatable validation script: `rag_pipeline/validate_support_agent.py`.
- Updated `rag_pipeline/rag_pipeline_walkthrough.ipynb` through the LangGraph design, node, API, and validation steps.

Current validation command:

```powershell
cd backend
uv run python ../rag_pipeline/validate_support_agent.py
```

Current validation coverage:

- Return-policy question
- Product setup question
- Troubleshooting question
- Comparison question
- Catalog availability question
- Underspecified clarification question
- Order-specific escalation question
- Unsupported category question

Validation result:

```text
Validated 8 support-agent cases.
```

Deferred or dependent:

- OpenAI remains blocked by quota for embeddings; Nebius is currently available for embeddings.
- Ticket persistence and full ticket-management endpoints remain Phase 9.

Embedding execution status:

- The first embedding run hit a Windows TLS/certificate issue.
- Added `truststore` and configured the embedding code to use system certificates.
- Added `check_embedding_ctx_length=False` to avoid `tiktoken` downloading tokenizer data before the API call.
- After those fixes, the request reached OpenAI successfully.
- Verified the current key can list models when `truststore` is injected.
- The current key can see `text-embedding-3-small`, `text-embedding-3-large`, and chat models.
- Actual OpenAI embedding requests still return `429 insufficient_quota`, so the account/project does not currently have usable embedding quota.

Resume command after adding billing/credits or switching to a key with quota:

```powershell
cd backend
uv run python ../rag_pipeline/preview_embeddings.py
```

If the new key is loaded correctly and has quota, this should generate embeddings for 907 chunks using `text-embedding-3-small`.

Current local backup commands:

```powershell
cd backend
uv run python ../rag_pipeline/preview_embeddings.py --provider hashing
uv run python ../rag_pipeline/build_vector_store.py --provider hashing
uv run python ../rag_pipeline/preview_retrieval.py --provider hashing
uv run python ../rag_pipeline/preview_answers.py --provider hashing
```

Nebius test commands:

```powershell
cd backend
uv run python ../rag_pipeline/check_nebius_access.py
uv run python ../rag_pipeline/check_nebius_embeddings.py
uv run python ../rag_pipeline/preview_embeddings.py --provider nebius --limit 50
```

Full Nebius Chroma build command, when ready to wait for the slower run:
Completed successfully:

```powershell
cd backend
uv run python ../rag_pipeline/build_vector_store.py --provider nebius
uv run python ../rag_pipeline/preview_retrieval.py --provider nebius
uv run python ../rag_pipeline/preview_answers.py --provider nebius
```

## Planned Structure

```text
data/
  raw/
  catalog/
  reviews/
  knowledge_base/
  support/
docs/
frontend/
backend/
```

## Existing Planning Documents

- `rag-ecommerce-plan.md`
- `docs/build-plan.md`
- `docs/learning-notes.md`
- `docs/phase-0-setup-tasks.md`
- `docs/phase-1-data-layer-tasks.md`
- `docs/phase-2-ui-baseline-tasks.md`
- `docs/phase-3-frontend-logic-tasks.md`
- `docs/phase-4-backend-api-tasks.md`
- `docs/phase-5-support-kb-tasks.md`
- `docs/phase-6-rag-pipeline-tasks.md`
- `docs/phase-7-langgraph-tasks.md`
- `docs/phase-8-chat-ui-tasks.md`

## Next Steps

1. Start Phase 9 ticket persistence and support workflow extensions.
2. Add ticket storage for escalation cases.
3. Consider ticket-management endpoints for listing and reviewing support handoffs.
4. Add the catalog-ranking intent for questions such as `List top 5 products with highest reviews`.
5. Keep developer/debug trace mode available for observability and eval.
6. Rebuild Chroma with OpenAI embeddings later only if switching away from Nebius.
7. Keep Pinecone as a later cloud vector database option.

## Notes For Next Session

Before starting Phase 9 support workflow extensions, review:

- `rag-ecommerce-plan.md`
- `PROJECT_STATUS.md`
- `docs/build-plan.md`
- `docs/learning-notes.md`
- `docs/phase-7-langgraph-tasks.md`
- `docs/phase-8-chat-ui-tasks.md`
- `docs/catalog-schema.md`
- `data/catalog/products.json`
- `frontend/src/main.jsx`
- `frontend/src/styles.css`
- `backend/app/main.py`
- `data/catalog/categories.json`
- `docs/knowledge-base.md`
- `data/knowledge_base/`
- `data/reviews/product_reviews.json`
- `data/support/tickets.json`
- `rag_pipeline/support_agent.py`
- `rag_pipeline/validate_support_agent.py`

Then continue with ticket persistence and support workflow extensions.

RAG and LangGraph agent behavior are now available through `POST /chat`, and the React frontend exposes that behavior through the support chat panel. Ticket fallback and ticket persistence are the next backend/product workflow steps.

Developer/debug trace mode:

- Added an explicitly enabled frontend developer-mode toggle in the support chat composer, unlocked only when the frontend URL includes `?eval=z`.
- When the URL includes `?eval=z`, developer mode is enabled by default and the frontend sends an optional `debug: true` flag with chat requests.
- Extended `POST /chat` to optionally return intent classification, product hints, retrieval plan, context sufficiency decision, retrieval scores, selected chunks, and graph path metadata.
- Rendered citations, retrieved context, and debug metadata in compact expandable eval/developer panels.
- Developer mode remains hidden and disabled in normal support mode, and the frontend tolerates missing debug metadata.

Catalog availability:

- Added deterministic catalog availability handling for questions such as `Is IBM Laptop available?`.
- Availability answers use `data/catalog/products.json` rather than RAG retrieval.
- If an exact brand/product is absent, the answer says so and lists related catalog matches.

Planned catalog-ranking enhancement:

- Add a catalog-ranking intent for questions such as `List top 5 products with highest reviews`.
- Answer ranking questions from `data/catalog/products.json` using deterministic sorting by `reviewCount`, `rating`, or `price`.
- Keep ranking separate from RAG review-summary questions, which should remain product-specific.

Most recent RAG/backend files to review after restart:

- `rag_pipeline/rag_pipeline_walkthrough.ipynb`
- `rag_pipeline/support_agent.py`
- `rag_pipeline/validate_support_agent.py`
- `rag_pipeline/embeddings.py`
- `rag_pipeline/check_nebius_access.py`
- `rag_pipeline/check_nebius_embeddings.py`
- `rag_pipeline/preview_embeddings.py`
- `rag_pipeline/vector_store.py`
- `rag_pipeline/build_vector_store.py`
- `rag_pipeline/retrieval.py`
- `rag_pipeline/preview_retrieval.py`
- `rag_pipeline/answer_generation.py`
- `rag_pipeline/preview_answers.py`
- `rag_pipeline/chunking.py`
- `backend/app/main.py`
- `backend/pyproject.toml`
